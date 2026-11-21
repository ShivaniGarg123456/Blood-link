from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey
from database import Base


class Donor(Base):
    __tablename__ = "donors"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    state = Column(String, nullable=False)
    city = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    age = Column(Integer, nullable=False)
    sex = Column(String, nullable=False)              # male / female
    weight_kg = Column(Float, nullable=False)
    blood_group = Column(String, nullable=False)      # e.g. B-
    component = Column(String, default="whole_blood") # prototype: whole blood only
    last_donation_date = Column(Date, nullable=True)

    # Only the RESULT of the eligibility rules is stored, not disease details
    status = Column(String, default="not_active")     # active / not_active / paused
    reason = Column(String, default="")
    eligible_after = Column(Date, nullable=True)

    consent_given_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class BloodRequest(Base):
    __tablename__ = "requests"

    id = Column(Integer, primary_key=True, index=True)
    receiver_phone = Column(String, nullable=False)
    receiver_name = Column(String, nullable=False)
    blood_group = Column(String, nullable=False)
    component = Column(String, default="whole_blood")
    units_needed = Column(Integer, default=1)
    units_accepted = Column(Integer, default=0)
    hospital = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    urgency = Column(String, default="high")          # critical / high / normal
    status = Column(String, default="open")           # open / fulfilled / closed
    current_radius_km = Column(Integer, default=15)
    created_at = Column(DateTime, default=datetime.utcnow)


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("requests.id"), nullable=False)
    donor_id = Column(Integer, ForeignKey("donors.id"), nullable=False)
    wave_radius_km = Column(Integer, default=15)
    distance_km = Column(Float, nullable=True)       # donor's distance from the hospital
    responded_at = Column(DateTime, nullable=True)   # when the donor accepted or declined
    sent_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    # pending / accepted / arrived / no_show / declined / expired
    response = Column(String, default="pending")