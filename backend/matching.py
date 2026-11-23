from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from models import Donor, Alert, BloodRequest
from rules.compatibility import compatible_donors
from rules.distance import distance_km


def find_donors_for_wave(db: Session, request: BloodRequest, radius_km: int):
    """Return (donor, distance_km) pairs to alert in this wave, nearest first.

    Rules:
    - donor must be active, and must have the "available" switch ON
    - donor's blood group must be compatible with the receiver's group
      for the requested component (whole blood or RBC)
    - donor must be within radius_km of the hospital
    - donor must NOT have been alerted already for this request,
      so growing the radius never alerts the same person twice
    - the receiver is never alerted about their own request
    """
    groups = compatible_donors(request.blood_group, request.component)

    # Donors whose alert was only cancelled (the need was fulfilled before they
    # could answer) are allowed to be alerted again. Everyone else is skipped,
    # so nobody is spammed twice.
    already_alerted = {
        row[0]
        for row in db.query(Alert.donor_id)
        .filter(Alert.request_id == request.id, Alert.response != "cancelled")
        .all()
    }

    candidates = (
        db.query(Donor)
        .filter(Donor.status == "active")
        .filter(Donor.available.is_(True))
        .filter(Donor.blood_group.in_(groups))
        .filter(Donor.phone != request.receiver_phone)
        .all()
    )

    wave = []
    for donor in candidates:
        if donor.id in already_alerted:
            continue
        d = distance_km(request.latitude, request.longitude, donor.latitude, donor.longitude)
        if d <= radius_km:
            wave.append((donor, d))

    wave.sort(key=lambda pair: pair[1])
    return wave


def wave_is_finished(
    db: Session,
    request: BloodRequest,
    radius_km: int,
    now: Optional[datetime] = None,
) -> bool:
    """True when this wave is over and the next radius should start now.

    A wave is over when nobody in it can still accept:
    - everyone declined or let their alert expire (do not wait for the clock), or
    - the timer ran out (pending alerts past expires_at count as expired).
    A wave with nobody in it is over straight away.
    """
    now = now or datetime.utcnow()

    alerts = (
        db.query(Alert)
        .filter(Alert.request_id == request.id, Alert.wave_radius_km == radius_km)
        .all()
    )
    if not alerts:
        return True

    still_waiting = [a for a in alerts if a.response == "pending" and a.expires_at > now]
    return len(still_waiting) == 0