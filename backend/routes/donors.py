from datetime import date, datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_db
from models import Alert, BloodRequest, Donor
from rules.compatibility import COMPATIBLE_DONORS
from rules.eligibility import age_from_dob, check_eligibility, refresh_donor_status
from security import get_current_phone
from selection import release_confirmed

router = APIRouter(prefix="/donors", tags=["Donors"])

# Eligibility result -> donor status
STATUS_MAP = {
    "eligible": "active",
    "not_eligible": "not_active",
    "eligible_after": "paused",
}


# ---------- request bodies ----------

class DonorForm(BaseModel):
    name: str = Field(min_length=2)
    state: str
    city: str
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    date_of_birth: date
    sex: str                      # male / female
    weight_kg: float = Field(gt=0)
    blood_group: str              # e.g. B-
    # Used only to run the rules. NOT saved.
    conditions: List[str] = []
    last_donation_date: Optional[date] = None
    consent: bool                 # must be true


class DonorEdit(BaseModel):
    """Everything is optional. Phone, blood group, date of birth and sex are locked."""
    name: Optional[str] = Field(default=None, min_length=2)
    state: Optional[str] = None
    city: Optional[str] = None
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)
    weight_kg: Optional[float] = Field(default=None, gt=0)
    last_donation_date: Optional[date] = None
    # The current health answer ("any fever or illness now?"). Used only to run the rules.
    conditions: List[str] = []


class LocationUpdate(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class Availability(BaseModel):
    available: bool


class Recheck(BaseModel):
    conditions: List[str] = []


# ---------- helpers ----------

def _get_donor(db: Session, phone: str) -> Donor:
    donor = db.query(Donor).filter(Donor.phone == phone).first()
    if donor is None:
        raise HTTPException(status_code=404, detail="Not registered yet")
    return donor


def _check_dob(dob: date) -> None:
    today = date.today()
    if dob > today:
        raise HTTPException(status_code=400, detail="Date of birth cannot be in the future")
    if age_from_dob(dob, today) > 120:
        raise HTTPException(status_code=400, detail="Please check the date of birth")


def _apply_rules(donor: Donor, conditions: List[str]) -> None:
    """Run the fixed eligibility rules and save only the result."""
    cleaned = [c.strip().lower() for c in conditions if c.strip()]
    result = check_eligibility(
        age_from_dob(donor.date_of_birth),
        donor.weight_kg,
        donor.sex,
        donor.last_donation_date,
        cleaned,
    )
    donor.status = STATUS_MAP[result["status"]]
    donor.reason = result["reason"]
    donor.eligible_after = (
        date.fromisoformat(result["eligible_after"]) if result["eligible_after"] else None
    )


def _release_open_alerts(db: Session, donor: Donor) -> None:
    """The donor is pausing or leaving. Free up every open alert of this donor.

    Alerts that were only waiting are cancelled. If the donor was confirmed for a
    request, the unit is given back and the nearest backup donor is confirmed.
    """
    alerts = db.query(Alert).filter(Alert.donor_id == donor.id).all()
    for a in alerts:
        if a.response in ("pending", "accepted", "standby"):
            a.response = "cancelled"
    db.commit()

    for a in alerts:
        if a.response in ("confirmed", "arrived"):
            req = db.get(BloodRequest, a.request_id)
            if req is not None and req.status != "closed":
                release_confirmed(db, req, a, "cant_come")


def donor_to_dict(d: Donor) -> dict:
    return {
        "phone": d.phone,
        "name": d.name,
        "state": d.state,
        "city": d.city,
        "latitude": d.latitude,
        "longitude": d.longitude,
        "date_of_birth": d.date_of_birth.isoformat(),
        "age": age_from_dob(d.date_of_birth),
        "sex": d.sex,
        "weight_kg": d.weight_kg,
        "blood_group": d.blood_group,
        "component": d.component,
        "last_donation_date": d.last_donation_date.isoformat() if d.last_donation_date else None,
        "available": d.available,
        "status": d.status,
        "reason": d.reason,
        "eligible_after": d.eligible_after.isoformat() if d.eligible_after else None,
    }


# ---------- endpoints ----------

@router.post("/register")
def register_donor(
    form: DonorForm,
    phone: str = Depends(get_current_phone),
    db: Session = Depends(get_db),
):
    """Create the donor profile (only once per phone number)."""
    if not form.consent:
        raise HTTPException(status_code=400, detail="Consent is required to register as a donor")

    sex = form.sex.strip().lower()
    group = form.blood_group.strip().upper()
    if sex not in ("male", "female"):
        raise HTTPException(status_code=400, detail="sex must be male or female")
    if group not in COMPATIBLE_DONORS:
        raise HTTPException(status_code=400, detail="Unknown blood group")
    _check_dob(form.date_of_birth)
    if form.last_donation_date and form.last_donation_date > date.today():
        raise HTTPException(status_code=400, detail="Last donation date cannot be in the future")

    if db.query(Donor).filter(Donor.phone == phone).first() is not None:
        raise HTTPException(
            status_code=409,
            detail="Already registered. Use PUT /donors/me to edit your profile.",
        )

    donor = Donor(
        phone=phone,
        name=form.name.strip(),
        state=form.state.strip(),
        city=form.city.strip(),
        latitude=form.latitude,
        longitude=form.longitude,
        date_of_birth=form.date_of_birth,
        sex=sex,
        weight_kg=form.weight_kg,
        blood_group=group,
        component="whole_blood",
        last_donation_date=form.last_donation_date,
        available=True,
        consent_given_at=datetime.utcnow(),
    )
    _apply_rules(donor, form.conditions)

    db.add(donor)
    db.commit()
    db.refresh(donor)
    return donor_to_dict(donor)


@router.get("/me")
def my_profile(
    phone: str = Depends(get_current_phone),
    db: Session = Depends(get_db),
):
    """Returning donor: load the saved profile, no form needed."""
    donor = _get_donor(db, phone)
    if refresh_donor_status(donor):
        db.commit()
        db.refresh(donor)
    return donor_to_dict(donor)


@router.put("/me")
def edit_profile(
    body: DonorEdit,
    phone: str = Depends(get_current_phone),
    db: Session = Depends(get_db),
):
    """Edit the profile. The eligibility rules run again with the new answers."""
    donor = _get_donor(db, phone)
    sent = body.model_fields_set

    if body.name is not None:
        donor.name = body.name.strip()
    if body.state is not None:
        donor.state = body.state.strip()
    if body.city is not None:
        donor.city = body.city.strip()
    if body.latitude is not None:
        donor.latitude = body.latitude
    if body.longitude is not None:
        donor.longitude = body.longitude
    if body.weight_kg is not None:
        donor.weight_kg = body.weight_kg
    if "last_donation_date" in sent:
        if body.last_donation_date and body.last_donation_date > date.today():
            raise HTTPException(status_code=400, detail="Last donation date cannot be in the future")
        donor.last_donation_date = body.last_donation_date

    _apply_rules(donor, body.conditions)
    db.commit()
    db.refresh(donor)
    return donor_to_dict(donor)


@router.put("/me/location")
def update_location(
    body: LocationUpdate,
    phone: str = Depends(get_current_phone),
    db: Session = Depends(get_db),
):
    """Donors move. The app calls this to refresh the saved location."""
    donor = _get_donor(db, phone)
    donor.latitude = body.latitude
    donor.longitude = body.longitude
    db.commit()
    return {"message": "Location updated"}


@router.put("/me/availability")
def set_availability(
    body: Availability,
    phone: str = Depends(get_current_phone),
    db: Session = Depends(get_db),
):
    """The donor's own pause switch. OFF means no new alerts.

    Switching OFF also frees every open alert of this donor. If the donor was
    confirmed, the unit is given back and the nearest backup donor is confirmed.
    """
    donor = _get_donor(db, phone)
    if not body.available and donor.available:
        _release_open_alerts(db, donor)
    donor.available = body.available
    db.commit()
    db.refresh(donor)
    return donor_to_dict(donor)


@router.post("/me/recheck")
def i_am_well_now(
    body: Recheck,
    phone: str = Depends(get_current_phone),
    db: Session = Depends(get_db),
):
    """The "I am well now" button (for example after a failed checkup).

    The app asks "any fever or illness now?" again, and the rules run again.
    """
    donor = _get_donor(db, phone)
    _apply_rules(donor, body.conditions)
    db.commit()
    db.refresh(donor)
    return donor_to_dict(donor)


@router.delete("/me")
def delete_account(
    phone: str = Depends(get_current_phone),
    db: Session = Depends(get_db),
):
    """Delete the account and all saved data of this donor."""
    donor = _get_donor(db, phone)
    _release_open_alerts(db, donor)
    db.query(Alert).filter(Alert.donor_id == donor.id).delete()
    db.delete(donor)
    db.commit()
    return {"message": "Your account and data have been deleted."}