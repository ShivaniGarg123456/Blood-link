from datetime import datetime, timedelta

from database import SessionLocal
import models  # noqa: F401
from models import BloodRequest, Alert
from matching import find_donors_for_wave

db = SessionLocal()

req = BloodRequest(
    receiver_phone="9111111111",
    receiver_name="Test Receiver",
    blood_group="B-",
    units_needed=1,
    hospital="AIIMS Delhi",
    latitude=28.5672,
    longitude=77.2100,
)
db.add(req)
db.commit()
db.refresh(req)

try:
    print("Receiver needs B- blood at AIIMS Delhi")
    print("Compatible donor groups: B- and O-\n")

    for radius in (15, 30, 45, 60):
        wave = find_donors_for_wave(db, req, radius)
        print(f"Wave: up to {radius} km")
        if not wave:
            print("   nobody new to alert")
        for donor, dist in wave:
            print(f"   alert {donor.name:16} {donor.city:16} {donor.blood_group:3} {dist:5.1f} km")
            db.add(Alert(
                request_id=req.id,
                donor_id=donor.id,
                wave_radius_km=radius,
                expires_at=datetime.utcnow() + timedelta(minutes=5),
            ))
        db.commit()  # saved, so the next wave skips these donors
        print()
finally:
    # Clean up so the test leaves no trace
    db.query(Alert).filter(Alert.request_id == req.id).delete()
    db.delete(req)
    db.commit()
    db.close()