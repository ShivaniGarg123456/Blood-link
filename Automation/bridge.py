"""The ONLY file that touches the backend's code. If a backend name changes, fix it here.

The backend uses flat imports (`from database import ...`), so run from the backend folder:
    cd backend
    PYTHONPATH=.. uvicorn automation.server:app --reload
(running from backend/ keeps the same bloodlink.db file the backend uses)
"""
from contextlib import contextmanager
from datetime import timedelta

from database import SessionLocal           # backend
from models import Alert, BloodRequest, Donor  # backend

from .scheduler import advance


@contextmanager
def session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _snap(alert, donor, req):
    """Plain dict, so the rest of automation never sees database objects."""
    return {
        "alert_id": alert.id, "request_id": alert.request_id, "donor_id": donor.id,
        "donor_name": donor.name, "donor_phone": donor.phone, "response": alert.response,
        "sent_at": alert.sent_at, "expires_at": alert.expires_at,
        "distance_km": round(alert.distance_km, 1) if alert.distance_km is not None else 0.0,
        "blood_group": req.blood_group, "component": req.component, "hospital": req.hospital,
        "urgency": req.urgency, "receiver_name": req.receiver_name, "receiver_phone": req.receiver_phone,
    }


class Bridge:
    def _rows(self, db):
        return db.query(Alert, Donor, BloodRequest).filter(
            Alert.donor_id == Donor.id, Alert.request_id == BloodRequest.id)

    def snapshots(self, now, hours=24):
        """Alerts the worker cares about: waiting for an answer, or just confirmed / put on standby."""
        with session() as db:
            rows = self._rows(db).filter(
                Alert.response.in_(("pending", "confirmed", "standby")),
                Alert.sent_at > now - timedelta(hours=hours)).all()
            return [_snap(a, d, r) for a, d, r in rows]

    def snapshot(self, alert_id):
        with session() as db:
            row = self._rows(db).filter(Alert.id == alert_id).first()
            return _snap(*row) if row else None

    def donor_exists(self, donor_id):
        with session() as db:
            return db.query(Donor).filter(Donor.id == donor_id).first() is not None

    def donor_id_for_phone(self, phone):
        with session() as db:
            donor = db.query(Donor).filter(Donor.phone == phone).first()
            return donor.id if donor else None

    def scheduler_tick(self, now):
        from config import next_radius           # backend
        from matching import wave_is_finished    # backend
        from selection import resolve_request    # backend
        from waves import send_wave              # backend
        with session() as db:
            db.query(Alert).filter(Alert.response == "pending", Alert.expires_at <= now).update(
                {"response": "expired"}, synchronize_session=False)
            db.commit()
            for req in db.query(BloodRequest).filter(BloodRequest.status == "open").all():
                advance(db, req, now, resolve=resolve_request, wave_is_finished=wave_is_finished,
                        next_radius=next_radius, send_wave=send_wave)

    def _respond(self, alert_id, fn_name):
        """Calls the backend's own accept/decline/status function, so its rules stay the single source of truth."""
        from fastapi import HTTPException
        from routes import donor_alerts          # backend
        with session() as db:
            alert = db.query(Alert).filter(Alert.id == alert_id).first()
            donor = db.query(Donor).filter(Donor.id == alert.donor_id).first() if alert else None
            if donor is None:
                return {"ok": False, "detail": "Alert not found."}
            try:
                view = getattr(donor_alerts, fn_name)(alert_id, phone=donor.phone, db=db)
            except HTTPException as e:
                return {"ok": False, "detail": str(e.detail)}
            return {"ok": True, **view}

    def accept(self, alert_id):
        return self._respond(alert_id, "accept_alert")

    def decline(self, alert_id):
        return self._respond(alert_id, "decline_alert")