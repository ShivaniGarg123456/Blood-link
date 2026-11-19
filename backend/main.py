from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine
import models  # noqa: F401
from routes import auth, donors

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


@app.get("/")
def home():
    return {"message": "BloodLink backend is running"}