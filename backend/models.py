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
    sex = Column(String, nullable=False)             # male / female
    weight_kg = Column(Float, nullable=False)
    blood_group = Column(String, nullable=False)     # e.g. B-
    conditions = Column(String, default="")          # comma-separated categories
    last_donation_date = Column(Date, nullable=True)

    # Result of the eligibility rules
    status = Column(String, default="not_active")    # active / not_active / paused
    reason = Column(String, default="")
    eligible_after = Column(Date, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)


class BloodRequest(Base):
    __tablename__ = "requests"

    id = Column(Integer, primary_key=True, index=True)
    receiver_phone = Column(String, nullable=False)
    receiver_name = Column(String, nullable=False)
    blood_group = Column(String, nullable=False)
    units_needed = Column(Integer, default=1)
    units_accepted = Column(Integer, default=0)
    hospital = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    urgency = Column(String, default="high")
    status = Column(String, default="open")          # open / fulfilled / closed
    current_radius_km = Column(Integer, default=15)
    created_at = Column(DateTime, default=datetime.utcnow)


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("requests.id"), nullable=False)
    donor_id = Column(Integer, ForeignKey("donors.id"), nullable=False)
    wave_radius_km = Column(Integer, default=15)
    sent_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    response = Column(String, default="pending")     # pending / accepted / declined / expired