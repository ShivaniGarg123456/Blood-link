from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from config import WAVE_RADII_KM
from database import get_db
from models import Alert, BloodRequest
from rules.compatibility import COMPATIBLE_DONORS
from security import get_current_phone
from waves import send_wave

router = APIRouter(prefix="/requests", tags=["Requests"])


class RequestForm(BaseModel):
    receiver_name: str = Field(min_length=2)
    blood_group: str                      # e.g. B-
    units_needed: int = Field(ge=1, le=10)
    hospital: str = Field(min_length=2)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    urgency: str = "high"                 # critical / high / normal


@router.post("")
def create_request(
    form: RequestForm,
    phone: str = Depends(get_current_phone),
    db: Session = Depends(get_db),
):
    """A receiver asks for blood. Wave 1 (15 km) is alerted straight away."""
    group = form.blood_group.strip().upper()
    urgency = form.urgency.strip().lower()

    if group not in COMPATIBLE_DONORS:
        raise HTTPException(status_code=400, detail="Unknown blood group")
    if urgency not in ("critical", "high", "normal"):
        raise HTTPException(status_code=400, detail="urgency must be critical, high or normal")

    req = BloodRequest(
        receiver_phone=phone,
        receiver_name=form.receiver_name.strip(),
        blood_group=group,
        component="whole_blood",
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
        "alerted_count": len(wave),
        "alerted_distances_km": [round(d, 1) for _donor, d in wave],
    }


@router.get("/{request_id}/status")
def request_status(
    request_id: int,
    phone: str = Depends(get_current_phone),
    db: Session = Depends(get_db),
):
    """Live status for the receiver's screen."""
    req = db.query(BloodRequest).filter(BloodRequest.id == request_id).first()
    if req is None or req.receiver_phone != phone:
        raise HTTPException(status_code=404, detail="Request not found")

    alerts = db.query(Alert).filter(Alert.request_id == req.id).all()
    counts = {}
    for a in alerts:
        counts[a.response] = counts.get(a.response, 0) + 1

    return {
        "request_id": req.id,
        "status": req.status,
        "blood_group": req.blood_group,
        "hospital": req.hospital,
        "units_needed": req.units_needed,
        "units_accepted": req.units_accepted,
        "radius_km": req.current_radius_km,
        "total_alerted": len(alerts),
        "alerts_by_response": counts,
    }