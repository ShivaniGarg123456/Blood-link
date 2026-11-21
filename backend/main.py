from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine
import models  # noqa: F401
from routes import auth, donors, blood_requests, donor_alerts

Base.metadata.create_all(bind=engine)

app = FastAPI(title="BloodLink API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(donors.router)
app.include_router(donor_alerts.router)
app.include_router(blood_requests.router)


@app.get("/")
def home():
    return {"message": "BloodLink backend is running"}