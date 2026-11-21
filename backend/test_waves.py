from datetime import datetime, timedelta

from database import SessionLocal
import models  # noqa: F401
from models import BloodRequest, Alert
from matching import find_donors_for_wave, wave_is_finished
from config import WAVE_SECONDS, next_radius

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


def send_wave(radius):
    """Create alerts for every new donor in this wave."""
    created = []
    for donor, dist in find_donors_for_wave(db, req, radius):
        alert = Alert(
            request_id=req.id,
            donor_id=donor.id,
            wave_radius_km=radius,
            expires_at=datetime.utcnow() + timedelta(seconds=WAVE_SECONDS),
        )
        db.add(alert)
        created.append((donor, alert))
    db.commit()
    return created


try:
    print(f"Wave length: {WAVE_SECONDS} seconds\n")

    # ---- Wave 1: 15 km ----
    radius = 15
    wave1 = send_wave(radius)
    print(f"Wave 1 ({radius} km): alerted {[d.name for d, _ in wave1]}")
    print("Just after sending, wave finished?        ",
          wave_is_finished(db, req, radius), "(expect False)")

    wave1[0][1].response = "declined"
    db.commit()
    print("One donor declined, wave finished?         ",
          wave_is_finished(db, req, radius), "(expect False, one is still pending)")

    wave1[1][1].response = "declined"
    db.commit()
    print("Everyone declined (about 2 min), finished? ",
          wave_is_finished(db, req, radius), "(expect True, do not wait for 3 min)")

    # ---- Wave 2: starts immediately ----
    radius = next_radius(radius)
    wave2 = send_wave(radius)
    print(f"\nWave 2 ({radius} km) started right away: alerted {[d.name for d, _ in wave2]}")
    print("Wave 1 donors alerted again?               ",
          any(d.name in [x.name for x, _ in wave1] for d, _ in wave2), "(expect False)")

    # ---- Timer test: nobody answers, so the 3 minutes run out ----
    print("\nNobody answers wave 2.")
    print("Wave finished before the timer ends?       ",
          wave_is_finished(db, req, radius), "(expect False)")
    later = datetime.utcnow() + timedelta(seconds=WAVE_SECONDS + 1)
    print("Wave finished after the timer ends?        ",
          wave_is_finished(db, req, radius, now=later), "(expect True)")
finally:
    # Clean up so the test leaves no trace
    db.query(Alert).filter(Alert.request_id == req.id).delete()
    db.delete(req)
    db.commit()
    db.close()