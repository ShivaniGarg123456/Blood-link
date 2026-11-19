import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

SECRET_KEY = os.getenv("JWT_SECRET", "change-me-for-demo")
ALGORITHM = "HS256"
TOKEN_DAYS = 7

bearer = HTTPBearer()


def create_token(phone: str) -> str:
    """Make a login token that remembers this phone number."""
    expires = datetime.now(timezone.utc) + timedelta(days=TOKEN_DAYS)
    return jwt.encode({"phone": phone, "exp": expires}, SECRET_KEY, algorithm=ALGORITHM)


def get_current_phone(creds: HTTPAuthorizationCredentials = Depends(bearer)) -> str:
    """Use this in any endpoint that needs a logged-in user."""
    try:
        payload = jwt.decode(creds.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["phone"]
    except (jwt.PyJWTError, KeyError):
        raise HTTPException(status_code=401, detail="Invalid or expired token")