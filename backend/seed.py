from datetime import datetime

from database import Base, engine, SessionLocal
import models  # noqa: F401
from models import Donor
from rules.distance import distance_km

# Demo hospital
HOSPITAL_NAME = "AIIMS Delhi"
HOSPITAL_LAT, HOSPITAL_LON = 28.5672, 77.2100

# phone, name, area, lat, lon, blood group, sex, age, weight, status, reason
SEED_DONORS = [
    # Near (inside 15 km)
    ("9000000001", "Aman Verma",    "Lajpat Nagar",   28.5677, 77.2433, "B-",  "male",   28, 70, "active",     ""),
    ("9000000002", "Neha Sharma",   "Saket",          28.5245, 77.2066, "O-",  "female", 31, 58, "active",     ""),
    ("9000000003", "Rohit Gupta",   "Karol Bagh",     28.6519, 77.1909, "A+",  "male",   35, 75, "active",     ""),
    ("9000000004", "Pooja Singh",   "Janakpuri",      28.6219, 77.0878, "AB+", "female", 26, 55, "active",     ""),
    ("9000000005", "Kunal Mehra",   "Hauz Khas",      28.5494, 77.2001, "B-",  "male",   17, 52, "not_active", "You are under 18, so you can't donate yet."),
    # 15 to 30 km
    ("9000000006", "Vikram Yadav",  "Rohini",         28.7041, 77.1025, "O-",  "male",   40, 80, "active",     ""),
    ("9000000007", "Sana Khan",     "Noida Sector 62",28.6270, 77.3650, "B+",  "female", 29, 60, "active",     ""),
    ("9000000008", "Arjun Malhotra","Gurugram Sec 29",28.4595, 77.0266, "B-",  "male",   33, 72, "active",     ""),
    ("9000000009", "Ritu Jain",     "Faridabad",      28.4089, 77.3178, "A-",  "female", 27, 57, "active",     ""),
    # 30 to 45 km
    ("9000000010", "Deepak Kumar",  "Manesar",        28.3500, 76.9400, "O-",  "male",   30, 68, "active",     ""),
    ("9000000011", "Imran Ali",     "Greater Noida",  28.4744, 77.5040, "O+",  "male",   24, 66, "active",     ""),
    # 45 to 60 km
    ("9000000012", "Anita Rao",     "Sonipat",        28.9931, 77.0151, "B-",  "female", 32, 62, "active",     ""),
    ("9000000013", "Sunil Chauhan", "Modinagar",      28.8330, 77.5740, "O-",  "male",   38, 78, "active",     ""),
]


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Remove old demo donors (phones starting with 90000), then add fresh ones
        db.query(Donor).filter(Donor.phone.like("90000%")).delete(synchronize_session=False)

        print(f"Distances from {HOSPITAL_NAME}\n")
        for phone, name, area, lat, lon, group, sex, age, weight, status, reason in SEED_DONORS:
            db.add(Donor(
                phone=phone, name=name, state="Delhi NCR", city=area,
                latitude=lat, longitude=lon, age=age, sex=sex, weight_kg=weight,
                blood_group=group, component="whole_blood",
                last_donation_date=None, status=status,
                reason=reason or "You can donate. The hospital will do the final check.",
                eligible_after=None, consent_given_at=datetime.utcnow(),
            ))
            d = distance_km(HOSPITAL_LAT, HOSPITAL_LON, lat, lon)
            print(f"{name:16} {area:16} {group:4} {d:5.1f} km  {status}")
        db.commit()
        print(f"\nAdded {len(SEED_DONORS)} demo donors.")
    finally:
        db.close()


if __name__ == "__main__":
    main()