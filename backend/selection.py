from datetime import datetime
from typing import Optional

from sqlalchemy import update
from sqlalchemy.orm import Session

from config import CONFIRM_WINDOW_SECONDS
from models import Alert, BloodRequest


def _dist(alert: Alert) -> float:
    return alert.distance_km if alert.distance_km is not None else 0.0


def _try_confirm(db: Session, request: BloodRequest, alert: Alert) -> bool:
    """Take one unit with a single atomic update.

    The WHERE clause means units_accepted can never go above units_needed,
    even if two confirmations happen at the same moment.
    """
    result = db.execute(
        update(BloodRequest)
        .where(
            BloodRequest.id == request.id,
            BloodRequest.units_accepted < BloodRequest.units_needed,
        )
        .values(units_accepted=BloodRequest.units_accepted + 1)
    )
    if result.rowcount == 0:
        return False
    alert.response = "confirmed"
    db.refresh(request)
    return True


def resolve_request(db: Session, request: BloodRequest, now: Optional[datetime] = None) -> dict:
    """Decide who is confirmed, who is standby, and whether the request is fulfilled.

    Call this every time a donor responds, and also on every scheduler tick.
    Returns which alerts changed, so the Automation teammate knows whom to message.
    """
    now = now or datetime.utcnow()
    outcome = {"confirmed": [], "standby": [], "cancelled": [], "fulfilled": False}

    if request.status == "closed":
        return outcome

    db.refresh(request)
    alerts = db.query(Alert).filter(Alert.request_id == request.id).all()

    def nearer_donor_still_deciding(distance: float) -> bool:
        return any(
            a.response == "pending" and a.expires_at > now and _dist(a) < distance
            for a in alerts
        )

    # 1. Donors who accepted, nearest first
    accepted = sorted((a for a in alerts if a.response == "accepted"), key=_dist)
    for a in accepted:
        if request.units_accepted >= request.units_needed:
            break
        if nearer_donor_still_deciding(_dist(a)):
            waited = (now - (a.responded_at or now)).total_seconds()
            if waited < CONFIRM_WINDOW_SECONDS:
                break  # the nearest accepted donor must wait, so everyone farther waits too
        if _try_confirm(db, request, a):
            outcome["confirmed"].append(a.id)
        else:
            break

    # 2. Still short of units: promote the nearest standby donors
    if request.units_accepted < request.units_needed:
        standby = sorted((a for a in alerts if a.response == "standby"), key=_dist)
        for a in standby:
            if request.units_accepted >= request.units_needed:
                break
            if _try_confirm(db, request, a):
                outcome["confirmed"].append(a.id)

    # 3. All units found: stop the search
    if request.units_accepted >= request.units_needed:
        for a in alerts:
            if a.response == "accepted":
                a.response = "standby"      # "need fulfilled, thank you, we will contact you if needed"
                outcome["standby"].append(a.id)
            elif a.response == "pending":
                a.response = "cancelled"
                outcome["cancelled"].append(a.id)
        request.status = "fulfilled"
        outcome["fulfilled"] = True
    elif request.status == "fulfilled":
        request.status = "open"

    db.commit()
    return outcome


def mark_arrived(db: Session, alert: Alert) -> None:
    """Hospital says the confirmed donor came. The unit stays counted."""
    if alert.response == "confirmed":
        alert.response = "arrived"
        db.commit()


def mark_no_show(
    db: Session, request: BloodRequest, alert: Alert, now: Optional[datetime] = None
) -> dict:
    """A confirmed donor did not show up. Give the unit back and look again."""
    if alert.response in ("confirmed", "arrived"):
        alert.response = "no_show"
        request.units_accepted = max(0, request.units_accepted - 1)
        request.status = "open"
        db.commit()
    return resolve_request(db, request, now)