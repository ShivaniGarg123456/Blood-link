from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from config import WAVE_RADII_KM
from database import get_db
from models import Alert, BloodRequest, Donor
from rules.compatibility import COMPATIBLE_DONORS, COMPONENTS
from security import get_current_phone
from selection import mark_checkup_failed, mark_donated, mark_no_show, resolve_request
from waves import send_wave
from AI.services.llm_parser import parse_blood_request_llm

router = APIRouter(prefix="/requests", tags=["Requests"])


# Donors the receiver is allowed to see (confirmed, or already helped)
HELPER_STATES = ("confirmed", "arrived", "donated")


class ParseRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


@router.post("/parse")
def parse_request_text(form: ParseRequest):
    """
    Converts natural-language blood requests into structured data.
    """
    result = parse_blood_request_llm(form.text)

    return {
        **result.model_dump(),
        "is_complete": len(result.missing_fields) == 0
    }


class RequestForm(BaseModel):
    receiver_name: str = Field(min_length=2)
    blood_group: str                      # e.g. B-
    units_needed: int = Field(ge=1, le=10)
    hospital: str = Field(min_length=2)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    urgency: str = "high"                 # critical / high / normal
    component: str = "whole_blood"        # whole_blood / rbc


def _get_my_request(db: Session, request_id: int, phone: str) -> BloodRequest:
    req = db.query(BloodRequest).filter(BloodRequest.id == request_id).first()
    if req is None or req.receiver_phone != phone:
        raise HTTPException(status_code=404, detail="Request not found")
    return req


def _get_request_alert(db: Session, req: BloodRequest, alert_id: int) -> Alert:
    alert = (
        db.query(Alert)
        .filter(Alert.id == alert_id, Alert.request_id == req.id)
        .first()
    )
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found for this request")
    return alert


@router.post("")
def create_request(
    form: RequestForm,
    phone: str = Depends(get_current_phone),
    db: Session = Depends(get_db),
):
    """A receiver asks for blood. Wave 1 (15 km) is alerted straight away."""
    group = form.blood_group.strip().upper()
    urgency = form.urgency.strip().lower()
    component = form.component.strip().lower()

    if group not in COMPATIBLE_DONORS:
        raise HTTPException(status_code=400, detail="Unknown blood group")
    if urgency not in ("critical", "high", "normal"):
        raise HTTPException(status_code=400, detail="urgency must be critical, high or normal")
    if component not in COMPONENTS:
        raise HTTPException(status_code=400, detail="component must be whole_blood or rbc")

    req = BloodRequest(
        receiver_phone=phone,
        receiver_name=form.receiver_name.strip(),
        blood_group=group,
        component=component,
        units_needed=form.units_needed,
        hospital=form.hospital.strip(),
        latitude=form.latitude,
        longitude=form.longitude,
        urgency=urgency,
        status="open",
        current_radius_km=WAVE_RADII_KM[0],
    )
    db.add(req)
    db.commit()
    db.refresh(req)

    wave = send_wave(db, req, WAVE_RADII_KM[0])

    # Privacy: the receiver sees counts and distances only, never donor details
    return {
        "request_id": req.id,
        "status": req.status,
        "radius_km": req.current_radius_km,
        "component": req.component,
        "alerted_count": len(wave),
        "alerted_distances_km": [round(d, 1) for _donor, d in wave],
    }


@router.get("/mine")
def my_requests(
    phone: str = Depends(get_current_phone),
    db: Session = Depends(get_db),
):
    """All requests made by this receiver, newest first (history screen).

    Each request lists the donors who helped (confirmed, arrived or donated),
    so the receiver can contact them in future. Other donors are never shown.
    """
    requests = (
        db.query(BloodRequest)
        .filter(BloodRequest.receiver_phone == phone)
        .order_by(BloodRequest.created_at.desc())
        .all()
    )
    request_ids = [r.id for r in requests]

    helped = {}  # request_id -> list of donors who helped
    if request_ids:
        alerts = (
            db.query(Alert)
            .filter(
                Alert.request_id.in_(request_ids),
                Alert.response.in_(HELPER_STATES),
            )
            .all()
        )
        for a in alerts:
            donor = db.query(Donor).filter(Donor.id == a.donor_id).first()
            if donor is None:   # the donor deleted their account
                continue
            helped.setdefault(a.request_id, []).append({
                "name": donor.name,
                "phone": donor.phone,
                "blood_group": donor.blood_group,
                "city": donor.city,
                "donated": a.response == "donated",
            })

    return [
        {
            "request_id": r.id,
            "receiver_name": r.receiver_name,
            "blood_group": r.blood_group,
            "component": r.component,
            "units_needed": r.units_needed,
            "units_found": r.units_accepted,
            "hospital": r.hospital,
            "urgency": r.urgency,
            "status": r.status,
            "radius_km": r.current_radius_km,
            "created_at": r.created_at.isoformat(),
            "donors_who_helped": helped.get(r.id, []),
        }
        for r in requests
    ]


@router.get("/{request_id}/status")
def request_status(
    request_id: int,
    phone: str = Depends(get_current_phone),
    db: Session = Depends(get_db),
):
    """Live dashboard for the receiver."""
    req = _get_my_request(db, request_id, phone)

    # Checking the status also moves things forward (the 15 second wait)
    resolve_request(db, req)
    db.refresh(req)

    alerts = db.query(Alert).filter(Alert.request_id == req.id).all()
    counts = {}
    for a in alerts:
        counts[a.response] = counts.get(a.response, 0) + 1

    # Privacy: donor name and phone only for confirmed donors
    confirmed = []
    for a in alerts:
        if a.response in HELPER_STATES:
            donor = db.query(Donor).filter(Donor.id == a.donor_id).first()
            if donor is None:
                continue
            confirmed.append({
                "alert_id": a.id,
                "name": donor.name,
                "phone": donor.phone,
                "blood_group": donor.blood_group,
                "distance_km": round(a.distance_km, 1) if a.distance_km is not None else None,
                "response": a.response,
                "progress": a.progress,
            })
    confirmed.sort(key=lambda c: c["distance_km"] if c["distance_km"] is not None else 0)

    return {
        "request_id": req.id,
        "status": req.status,
        "still_searching": req.status == "open",
        "blood_group": req.blood_group,
        "component": req.component,
        "hospital": req.hospital,
        "units_needed": req.units_needed,
        "units_found": req.units_accepted,
        "radius_km": req.current_radius_km,
        "total_alerted": len(alerts),
        "alerts_by_response": counts,
        "confirmed_donors": confirmed,
    }


@router.post("/{request_id}/close")
def close_request(
    request_id: int,
    phone: str = Depends(get_current_phone),
    db: Session = Depends(get_db),
):
    """The receiver found blood elsewhere, or no longer needs it. The search stops."""
    req = _get_my_request(db, request_id, phone)
    if req.status == "closed":
        return {"message": "Request already closed", "status": "closed"}

    alerts = db.query(Alert).filter(Alert.request_id == req.id).all()
    for a in alerts:
        if a.response == "pending":
            a.response = "cancelled"
        elif a.response == "accepted":
            a.response = "standby"   # "need fulfilled, thank you"

    req.status = "closed"
    db.commit()
    return {"message": "Request closed. Thank you!", "status": "closed"}


@router.post("/{request_id}/alerts/{alert_id}/donated")
def donor_donated(
    request_id: int,
    alert_id: int,
    phone: str = Depends(get_current_phone),
    db: Session = Depends(get_db),
):
    """The receiver pressed "I got blood". The donation is complete.

    The donor's last donation date is saved and the donor is paused for the
    waiting period. When every unit is donated, the request closes.
    """
    req = _get_my_request(db, request_id, phone)
    alert = _get_request_alert(db, req, alert_id)
    if alert.response not in ("confirmed", "arrived"):
        raise HTTPException(
            status_code=409,
            detail="Only a confirmed donor can be marked as donated",
        )

    result = mark_donated(db, req, alert)
    db.refresh(req)
    return {
        "message": "Thank you! The donation is recorded.",
        "request_status": req.status,
        "units_donated": result["donated"],
        "units_needed": req.units_needed,
        "request_closed": result["closed"],
    }

@router.post("/{request_id}/alerts/{alert_id}/checkup-failed")
def donor_checkup_failed(
    request_id: int,
    alert_id: int,
    phone: str = Depends(get_current_phone),
    db: Session = Depends(get_db),
):
    """The donor reached the hospital but failed the medical checkup.

    No donation happened, so the donor's last donation date is not changed.
    The donor is paused for a few days, the unit is given back, and the
    nearest backup donor is confirmed. If there is none, the search continues.
    """
    req = _get_my_request(db, request_id, phone)
    alert = _get_request_alert(db, req, alert_id)
    if alert.response not in ("confirmed", "arrived"):
        raise HTTPException(
            status_code=409,
            detail="Only a confirmed donor can be marked as checkup failed",
        )
    if req.status == "closed":
        raise HTTPException(status_code=409, detail="This request is closed")

    mark_checkup_failed(db, req, alert)
    db.refresh(req)
    return {
        "message": "Marked as checkup failed. We are looking for another donor.",
        "request_status": req.status,
        "units_found": req.units_accepted,
        "units_needed": req.units_needed,
    }


@router.post("/{request_id}/alerts/{alert_id}/no-show")
def donor_no_show(
    request_id: int,
    alert_id: int,
    phone: str = Depends(get_current_phone),
    db: Session = Depends(get_db),
):
    """The confirmed donor did not come. Give the unit back and look again."""
    req = _get_my_request(db, request_id, phone)
    alert = _get_request_alert(db, req, alert_id)
    if alert.response not in ("confirmed", "arrived"):
        raise HTTPException(status_code=409, detail="Only a confirmed donor can be marked as no-show")
    if req.status == "closed":
        raise HTTPException(status_code=409, detail="This request is closed")

    mark_no_show(db, req, alert)
    db.refresh(req)
    return {
        "message": "Donor marked as no-show. We are looking for another donor.",
        "status": req.status,
        "units_found": req.units_accepted,
        "units_needed": req.units_needed,
    }