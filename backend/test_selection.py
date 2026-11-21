from datetime import datetime, timedelta

from database import SessionLocal
import models  # noqa: F401
from models import BloodRequest, Alert, Donor
from selection import resolve_request, mark_no_show

db = SessionLocal()
base = datetime.utcnow()
made = []


def setup(units):
    req = BloodRequest(
        receiver_phone="9111111111", receiver_name="Test Receiver",
        blood_group="B-", units_needed=units, hospital="AIIMS Delhi",
        latitude=28.5672, longitude=77.2100,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    made.append(req.id)
    alerts = {}
    for phone, name, dist in [("9000000001", "Aman", 3.0),
                              ("9000000002", "Neha", 5.0),
                              ("9000000012", "Anita", 9.0)]:
        donor = db.query(Donor).filter(Donor.phone == phone).first()
        a = Alert(request_id=req.id, donor_id=donor.id, distance_km=dist,
                  expires_at=base + timedelta(seconds=180))
        db.add(a)
        alerts[name] = a
    db.commit()
    return req, alerts


def respond(alert, answer, seconds):
    alert.response = answer
    alert.responded_at = base + timedelta(seconds=seconds)
    db.commit()


def show(label, req, alerts):
    states = {name: a.response for name, a in alerts.items()}
    print(f"   {label}")
    print(f"      {states}")
    print(f"      request: {req.status}, units {req.units_accepted}/{req.units_needed}")


try:
    print("TEST 1: far donor accepts first, nearer donors still deciding (1 unit)")
    req, al = setup(1)
    respond(al["Anita"], "accepted", 0)
    resolve_request(db, req, now=base + timedelta(seconds=1))
    show("1 second later (should WAIT)", req, al)
    resolve_request(db, req, now=base + timedelta(seconds=16))
    show("16 seconds later (window over, confirm Anita)", req, al)

    print("\nTEST 2: a nearer donor accepts inside the window (1 unit)")
    req, al = setup(1)
    respond(al["Anita"], "accepted", 0)
    respond(al["Aman"], "accepted", 5)
    resolve_request(db, req, now=base + timedelta(seconds=5))
    show("Aman (nearest) wins, Anita becomes standby", req, al)

    print("\nTEST 3: the confirmed donor is a no-show")
    mark_no_show(db, req, al["Aman"], now=base + timedelta(seconds=600))
    show("Aman no-show, standby Anita is promoted", req, al)

    print("\nTEST 4: nearer donors decline, so no waiting (1 unit)")
    req, al = setup(1)
    respond(al["Anita"], "accepted", 0)
    respond(al["Aman"], "declined", 3)
    respond(al["Neha"], "declined", 3)
    resolve_request(db, req, now=base + timedelta(seconds=3))
    show("Anita confirmed right away", req, al)

    print("\nTEST 5: 2 units needed, 3 donors accept at the same time")
    req, al = setup(2)
    for name in ("Anita", "Neha", "Aman"):
        respond(al[name], "accepted", 2)
    resolve_request(db, req, now=base + timedelta(seconds=2))
    show("two nearest confirmed, the third is standby", req, al)
finally:
    for rid in made:
        db.query(Alert).filter(Alert.request_id == rid).delete()
        db.query(BloodRequest).filter(BloodRequest.id == rid).delete()
    db.commit()
    db.close()