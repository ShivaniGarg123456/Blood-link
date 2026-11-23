import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine
import models  # noqa: F401
import scheduler
from routes import auth, donors, blood_requests, donor_alerts, geo

Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the scheduler when the server starts, stop it when the server stops
    task = asyncio.create_task(scheduler.run_forever())
    yield
    task.cancel()


app = FastAPI(title="BloodLink API", lifespan=lifespan)

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
app.include_router(geo.router)


@app.get("/")
def home():
    return {"message": "BloodLink backend is running"}