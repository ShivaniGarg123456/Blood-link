from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Alert, BloodRequest, Donor
from security import get_current_phone
from selection import resolve_request

router = APIRouter(tags=["Donor alerts"])

CONTACT_STATES = ("confirmed", "arrived")

MESSAGES = {
    "pending": "Blood is needed near you. Please accept or decline.",
    "accepted": "Thank you. We are confirming the nearest donors.",
    "confirmed": "You are confirmed. Please go to the hospital and contact the receiver.",
    "arrived": "Thank you for donating!",
    "standby": "The need is fulfilled for now. Thank you! We will contact you if needed.",
    "cancelled": "This request is already fulfilled or closed. Thank you!",
    "declined": "You declined this request.",
    "expired": "This alert expired.",
    "no_show": "This donation was marked as not completed.",
}


def _get_donor(db: Session, phone: str) -> Donor:
    donor = db.query(Donor).filter(Donor.phone == phone).first()
    if donor is None:
        raise HTTPException(status_code=404, detail="Not registered yet")
    return donor


def _get_my_alert(db: Session, alert_id: int, donor: Donor) -> Alert:
    alert = (
        db.query(Alert)
        .filter(Alert.id == alert_id, Alert.donor_id == donor.id)
        .first()
    )
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


def _view(db: Session, alert: Alert) -> dict:
    now = datetime.utcnow()
    req = db.query(BloodRequest).filter(BloodRequest.id == alert.request_id).first()
    seconds_left = int((alert.expires_at - now).total_seconds())

    view = {
        "alert_id": alert.id,
        "response": alert.response,
        "message": MESSAGES.get(alert.response, ""),
        "blood_group": req.blood_group,
        "units_needed": req.units_needed,
        "hospital": req.hospital,
        "urgency": req.urgency,
        "distance_km": round(alert.distance_km, 1) if alert.distance_km is not None else None,
        "seconds_left": max(0, seconds_left) if alert.response == "pending" else 0,
    }
    # Privacy: contact details only after the donor is confirmed
    if alert.response in CONTACT_STATES:
        view["receiver_name"] = req.receiver_name
        view["receiver_phone"] = req.receiver_phone
    return view


def _require_open_alert(alert: Alert, db: Session) -> BloodRequest:
    """The donor can only respond to a pending alert that has not expired."""
    req = db.query(BloodRequest).filter(BloodRequest.id == alert.request_id).first()
    if alert.response != "pending":
        raise HTTPException(
            status_code=409,
            detail=MESSAGES.get(alert.response, "This alert is no longer open."),
        )
    if alert.expires_at <= datetime.utcnow():
        alert.response = "expired"
        db.commit()
        raise HTTPException(status_code=409, detail=MESSAGES["expired"])
    if req.status != "open":
        alert.response = "cancelled"
        db.commit()
        raise HTTPException(status_code=409, detail=MESSAGES["cancelled"])
    return req


@router.get("/donors/me/alerts")
def my_alerts(
    phone: str = Depends(get_current_phone),
    db: Session = Depends(get_db),
):
    """Alerts waiting for this donor to accept or decline."""
    donor = _get_donor(db, phone)
    now = datetime.utcnow()
    alerts = (
        db.query(Alert)
        .filter(Alert.donor_id == donor.id, Alert.response == "pending", Alert.expires_at > now)
        .order_by(Alert.sent_at.desc())
        .all()
    )
    return [_view(db, a) for a in alerts]


@router.get("/alerts/{alert_id}")
def alert_status(
    alert_id: int,
    phone: str = Depends(get_current_phone),
    db: Session = Depends(get_db),
):
    """The donor's app checks this after tapping Accept to see the result."""
    donor = _get_donor(db, phone)
    alert = _get_my_alert(db, alert_id, donor)
    req = db.query(BloodRequest).filter(BloodRequest.id == alert.request_id).first()

    # Checking the status also moves things forward (the 15 second wait)
    resolve_request(db, req)
    db.refresh(alert)
    return _view(db, alert)


@router.post("/alerts/{alert_id}/accept")
def accept_alert(
    alert_id: int,
    phone: str = Depends(get_current_phone),
    db: Session = Depends(get_db),
):
    donor = _get_donor(db, phone)
    alert = _get_my_alert(db, alert_id, donor)
    req = _require_open_alert(alert, db)

    alert.response = "accepted"
    alert.responded_at = datetime.utcnow()
    db.commit()

    # Nearest donor wins, with the 15 second wait if a nearer donor is deciding
    resolve_request(db, req)
    db.refresh(alert)
    return _view(db, alert)


@router.post("/alerts/{alert_id}/decline")
def decline_alert(
    alert_id: int,
    phone: str = Depends(get_current_phone),
    db: Session = Depends(get_db),
):
    donor = _get_donor(db, phone)
    alert = _get_my_alert(db, alert_id, donor)
    req = _require_open_alert(alert, db)

    alert.response = "declined"
    alert.responded_at = datetime.utcnow()
    db.commit()

    # If everyone nearer has now declined, a waiting donor is confirmed straight away
    resolve_request(db, req)
    db.refresh(alert)
    return _view(db, alert)