from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy import update
from sqlalchemy.orm import Session

from config import CHECKUP_FAIL_PAUSE_DAYS, CONFIRM_WINDOW_SECONDS
from models import Alert, BloodRequest, Donor
from rules.eligibility import DONATION_GAP_DAYS


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
        alert.progress = None
        request.units_accepted = max(0, request.units_accepted - 1)
        request.status = "open"
        db.commit()
    return resolve_request(db, request, now)


def release_confirmed(
    db: Session,
    request: BloodRequest,
    alert: Alert,
    new_state: str,
    now: Optional[datetime] = None,
) -> dict:
    """A confirmed donor can no longer give blood. Give the unit back.

    new_state says why: "cant_come" (the donor withdrew) or "no_show".
    The nearest standby donor is then confirmed automatically, and if there
    is no standby donor the search simply continues.
    """
    if alert.response in ("confirmed", "arrived"):
        alert.response = new_state
        alert.progress = None
        request.units_accepted = max(0, request.units_accepted - 1)
        request.status = "open"
        db.commit()
    return resolve_request(db, request, now)


def mark_donated(
    db: Session,
    request: BloodRequest,
    alert: Alert,
    today: Optional[date] = None,
) -> dict:
    """The receiver says "I got blood". The donation is now complete.

    - the donor's last donation date becomes today, and the donor is paused
      for the waiting period (then becomes active again by themselves)
    - when every unit is donated, the request closes and the search stops
    """
    today = today or date.today()

    donor = db.query(Donor).filter(Donor.id == alert.donor_id).first()
    alert.response = "donated"
    if donor is not None:
        gap_days = DONATION_GAP_DAYS.get(donor.sex, 120)
        donor.last_donation_date = today
        donor.status = "paused"
        donor.eligible_after = today + timedelta(days=gap_days)
        donor.reason = "You donated recently. Thank you! You can donate again after the waiting period."

    db.flush()  # make the new "donated" state visible to the count below
    donated = (
        db.query(Alert)
        .filter(Alert.request_id == request.id, Alert.response == "donated")
        .count()
    )

    if donated >= request.units_needed:
        for a in db.query(Alert).filter(
            Alert.request_id == request.id,
            Alert.response.in_(("pending", "accepted")),
        ).all():
            a.response = "cancelled" if a.response == "pending" else "standby"
        request.status = "closed"

    db.commit()
    return {"donated": donated, "closed": request.status == "closed"}



def mark_checkup_failed(
    db: Session,
    request: BloodRequest,
    alert: Alert,
    today: Optional[date] = None,
    now: Optional[datetime] = None,
) -> dict:
    """The donor reached the hospital but failed the medical checkup.

    - no donation happened, so the last donation date is NOT changed
    - the donor is paused for a few days (they can also press "I am well now")
    - the unit is given back, and the nearest backup donor is confirmed
    """
    today = today or date.today()

    donor = db.query(Donor).filter(Donor.id == alert.donor_id).first()
    if donor is not None:
        donor.status = "paused"
        donor.eligible_after = today + timedelta(days=CHECKUP_FAIL_PAUSE_DAYS)
        donor.reason = (
            "You did not pass the checkup this time. Please rest and press "
            "'I am well now' when you feel better."
        )

    return release_confirmed(db, request, alert, "checkup_failed", now)