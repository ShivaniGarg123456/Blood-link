from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from config import WAVE_SECONDS
from matching import find_donors_for_wave
from models import Alert, BloodRequest


def send_wave(db: Session, request: BloodRequest, radius_km: int):
    """Create an alert for every new donor inside radius_km.

    Returns a list of (donor, distance_km). Actually delivering the message
    (Telegram, voice, SMS) is the Automation teammate's job. This only
    records who must be alerted, how far they are, and until when.
    """
    wave = find_donors_for_wave(db, request, radius_km)
    expires = datetime.utcnow() + timedelta(seconds=WAVE_SECONDS)

    for donor, dist in wave:
        db.add(Alert(
            request_id=request.id,
            donor_id=donor.id,
            wave_radius_km=radius_km,
            distance_km=dist,
            expires_at=expires,
        ))

    request.current_radius_km = radius_km
    db.commit()
    return wave