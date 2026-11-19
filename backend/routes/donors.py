from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_db
from models import Donor
from rules.compatibility import COMPATIBLE_DONORS
from rules.eligibility import check_eligibility
from security import get_current_phone

router = APIRouter(prefix="/donors", tags=["Donors"])

# Eligibility result -> donor status
STATUS_MAP = {
    "eligible": "active",
    "not_eligible": "not_active",
    "eligible_after": "paused",
}


class DonorForm(BaseModel):
    name: str = Field(min_length=2)
    state: str
    city: str
    latitude: float
    longitude: float
    age: int = Field(ge=1, le=120)
    sex: str                      # male / female
    weight_kg: float = Field(gt=0)
    blood_group: str              # e.g. B-
    conditions: List[str] = []    # category names, e.g. ["fever"]
    last_donation_date: Optional[date] = None


def donor_to_dict(d: Donor) -> dict:
    return {
        "phone": d.phone,
        "name": d.name,
        "state": d.state,
        "city": d.city,
        "latitude": d.latitude,
        "longitude": d.longitude,
        "age": d.age,
        "sex": d.sex,
        "weight_kg": d.weight_kg,
        "blood_group": d.blood_group,
        "conditions": [c for c in d.conditions.split(",") if c],
        "last_donation_date": d.last_donation_date.isoformat() if d.last_donation_date else None,
        "status": d.status,
        "reason": d.reason,
        "eligible_after": d.eligible_after.isoformat() if d.eligible_after else None,
    }


@router.post("/register")
def register_donor(
    form: DonorForm,
    phone: str = Depends(get_current_phone),
    db: Session = Depends(get_db),
):
    """Create a donor profile, or update it if this phone already registered."""
    sex = form.sex.strip().lower()
    group = form.blood_group.strip().upper()

    if sex not in ("male", "female"):
        raise HTTPException(status_code=400, detail="sex must be male or female")
    if group not in COMPATIBLE_DONORS:
        raise HTTPException(status_code=400, detail="Unknown blood group")

    conditions = [c.strip().lower() for c in form.conditions if c.strip()]

    donor = db.query(Donor).filter(Donor.phone == phone).first()
    if donor is None:
        donor = Donor(phone=phone)
        db.add(donor)

    donor.name = form.name.strip()
    donor.state = form.state.strip()
    donor.city = form.city.strip()
    donor.latitude = form.latitude
    donor.longitude = form.longitude
    donor.age = form.age
    donor.sex = sex
    donor.weight_kg = form.weight_kg
    donor.blood_group = group
    donor.conditions = ",".join(conditions)
    donor.last_donation_date = form.last_donation_date

    # Run the fixed eligibility rules
    result = check_eligibility(
        form.age, form.weight_kg, sex, form.last_donation_date, conditions
    )
    donor.status = STATUS_MAP[result["status"]]
    donor.reason = result["reason"]
    donor.eligible_after = (
        date.fromisoformat(result["eligible_after"]) if result["eligible_after"] else None
    )

    db.commit()
    db.refresh(donor)
    return donor_to_dict(donor)


@router.get("/me")
def my_profile(
    phone: str = Depends(get_current_phone),
    db: Session = Depends(get_db),
):
    """Returning donor: load the saved profile, no form needed."""
    donor = db.query(Donor).filter(Donor.phone == phone).first()
    if donor is None:
        raise HTTPException(status_code=404, detail="Not registered yet")

    # If the waiting period is over, the donor becomes active again
    if donor.status == "paused" and donor.eligible_after and donor.eligible_after <= date.today():
        donor.status = "active"
        donor.reason = "You can donate. The hospital will do the final check."
        donor.eligible_after = None
        db.commit()
        db.refresh(donor)

    return donor_to_dict(donor)