from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Alert, BloodRequest, Donor
from security import get_current_phone
from selection import release_confirmed, resolve_request

router = APIRouter(tags=["Donor alerts"])

CONTACT_STATES = ("confirmed", "arrived")

MESSAGES = {
    "pending": "Blood is needed near you. Please accept or decline.",
    "accepted": "Thank you. We are confirming the nearest donors.",
    "confirmed": "You are confirmed. Please go to the hospital and contact the receiver.",
    "arrived": "You are at the hospital. Thank you for coming!",
    "donated": "Thank you for donating! You saved a life.",
    "standby": "The need is fulfilled for now. Thank you! We will contact you if needed.",
    "standby_waiting": (
        "You are a backup donor. If the first donor cannot come, we will tell you "
        "right away. Please stay ready."
    ),
    "cancelled": "This request is already fulfilled or closed. Thank you!",
    "declined": "You declined this request.",
    "expired": "This alert expired.",
    "no_show": "This donation was marked as not completed.",
    "cant_come": "You told us you can't come. Thank you for letting us know.",
    "checkup_failed": (
        "You did not pass the checkup this time. Please rest, and press "
        "'I am well now' when you feel better."
    ),
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

    message = MESSAGES.get(alert.response, "")
    # A standby donor hears something different while the search is still on
    if alert.response == "standby" and req.status != "closed":
        message = MESSAGES["standby_waiting"]

    view = {
        "alert_id": alert.id,
        "response": alert.response,
        "progress": alert.progress,
        "message": message,
        "blood_group": req.blood_group,
        "component": req.component,
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


def _require_confirmed(alert: Alert, db: Session) -> BloodRequest:
    """On the way, arrived and can't come are only for a confirmed donor."""
    req = db.query(BloodRequest).filter(BloodRequest.id == alert.request_id).first()
    if alert.response != "confirmed":
        raise HTTPException(
            status_code=409,
            detail="Only a confirmed donor can do this",
        )
    if req.status == "closed":
        raise HTTPException(status_code=409, detail="This request is closed")
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


@router.get("/donors/me/active-alerts")
def my_active_alerts(
    phone: str = Depends(get_current_phone),
    db: Session = Depends(get_db),
):
    """Alerts the donor has already answered: confirmed or backup (standby).

    The app uses this to show the On the way, Arrived and Can't come buttons.
    Only requests that are still open or fulfilled are listed.
    """
    donor = _get_donor(db, phone)
    alerts = (
        db.query(Alert)
        .filter(Alert.donor_id == donor.id, Alert.response.in_(("confirmed", "standby")))
        .order_by(Alert.sent_at.desc())
        .all()
    )
    result = []
    for a in alerts:
        req = db.query(BloodRequest).filter(BloodRequest.id == a.request_id).first()
        if req is not None and req.status != "closed":
            result.append(_view(db, a))
    return result


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


@router.post("/alerts/{alert_id}/on-the-way")
def on_the_way(
    alert_id: int,
    phone: str = Depends(get_current_phone),
    db: Session = Depends(get_db),
):
    """The confirmed donor has left for the hospital. The receiver sees this."""
    donor = _get_donor(db, phone)
    alert = _get_my_alert(db, alert_id, donor)
    _require_confirmed(alert, db)

    alert.progress = "on_the_way"
    alert.progress_at = datetime.utcnow()
    db.commit()
    return _view(db, alert)


@router.post("/alerts/{alert_id}/arrived")
def donor_says_arrived(
    alert_id: int,
    phone: str = Depends(get_current_phone),
    db: Session = Depends(get_db),
):
    """The confirmed donor reached the hospital.

    This is only information for the receiver. It does not mean the donation
    is done. The hospital checkup comes next.
    """
    donor = _get_donor(db, phone)
    alert = _get_my_alert(db, alert_id, donor)
    _require_confirmed(alert, db)

    alert.progress = "arrived"
    alert.progress_at = datetime.utcnow()
    db.commit()
    return _view(db, alert)


@router.post("/alerts/{alert_id}/cant-come")
def cant_come(
    alert_id: int,
    phone: str = Depends(get_current_phone),
    db: Session = Depends(get_db),
):
    """The confirmed donor can no longer come.

    The unit is given back, and the nearest backup (standby) donor is
    confirmed. If there is no backup donor, the search simply continues.
    """
    donor = _get_donor(db, phone)
    alert = _get_my_alert(db, alert_id, donor)
    req = _require_confirmed(alert, db)

    release_confirmed(db, req, alert, "cant_come")
    db.refresh(alert)
    return _view(db, alert)