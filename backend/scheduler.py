import asyncio
import os
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from config import REQUEST_MAX_HOURS, next_radius
from database import SessionLocal
from matching import wave_is_finished
from models import Alert, BloodRequest
from selection import resolve_request
from waves import send_wave

# How often the scheduler checks all open requests
TICK_SECONDS = int(os.getenv("SCHEDULER_TICK_SECONDS", "5"))


def tick(db: Session, now: Optional[datetime] = None) -> dict:
    """One check of every open request. Safe to call as often as you like."""
    now = now or datetime.utcnow()
    report = {"expired": 0, "waves": [], "auto_closed": []}

    # 1. Alerts whose timer ran out are marked expired
    expired = (
        db.query(Alert)
        .filter(Alert.response == "pending", Alert.expires_at <= now)
        .all()
    )
    for a in expired:
        a.response = "expired"
    db.commit()
    report["expired"] = len(expired)

    # 2. Look at every open request
    open_requests = db.query(BloodRequest).filter(BloodRequest.status == "open").all()
    for req in open_requests:
        # Too old: close it, so donors who register later are not alerted
        # for a stale request
        if now - req.created_at > timedelta(hours=REQUEST_MAX_HOURS):
            for a in db.query(Alert).filter(
                Alert.request_id == req.id,
                Alert.response.in_(("pending", "accepted")),
            ).all():
                a.response = "cancelled" if a.response == "pending" else "standby"
            req.status = "closed"
            db.commit()
            report["auto_closed"].append(req.id)
            continue

        # Nearest donor wins, 15 second wait, standby
        resolve_request(db, req, now)
        db.refresh(req)
        if req.status != "open":
            continue

        # Is the current wave over? (3 minutes passed, or everyone declined)
        radius = req.current_radius_km
        if not wave_is_finished(db, req, radius, now):
            continue

        # Grow the circle. After the last radius, keep checking at the same size,
        # so donors who register or become active later still get alerted
        # (until the request is closed or too old).
        new_radius = next_radius(radius) or radius
        wave = send_wave(db, req, new_radius)
        report["waves"].append({
            "request_id": req.id,
            "radius_km": new_radius,
            "alerted_donor_ids": [donor.id for donor, _dist in wave],
        })

    return report


async def run_forever() -> None:
    """Runs in the background while the server is on."""
    print(f"Scheduler started, checking every {TICK_SECONDS} seconds")
    while True:
        try:
            db = SessionLocal()
            try:
                tick(db)
            finally:
                db.close()
        except Exception as error:  # never let the loop die
            print("Scheduler error:", error)
        await asyncio.sleep(TICK_SECONDS)