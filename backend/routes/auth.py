import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import Donor
from security import create_token

router = APIRouter(prefix="/auth", tags=["Auth"])

DEMO_OTP = "1234"  # fixed OTP for the prototype


class SendOtpRequest(BaseModel):
    phone: str


class VerifyOtpRequest(BaseModel):
    phone: str
    otp: str


def clean_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", phone)
    if len(digits) < 10:
        raise HTTPException(status_code=400, detail="Enter a valid 10-digit mobile number")
    return digits[-10:]


@router.post("/otp/send")
def send_otp(body: SendOtpRequest):
    phone = clean_phone(body.phone)
    # In production: send a real SMS here.
    return {"message": f"OTP sent to {phone}", "demo_hint": "Use 1234 in demo mode"}


@router.post("/otp/verify")
def verify_otp(body: VerifyOtpRequest, db: Session = Depends(get_db)):
    phone = clean_phone(body.phone)
    if body.otp != DEMO_OTP:
        raise HTTPException(status_code=400, detail="Wrong OTP")

    donor = db.query(Donor).filter(Donor.phone == phone).first()
    return {
        "token": create_token(phone),
        "phone": phone,
        "is_registered_donor": donor is not None,
    }