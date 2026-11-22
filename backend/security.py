import os

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Keep this value fixed. If it changes, everyone is logged out.
SECRET_KEY = os.getenv("JWT_SECRET", "change-me-for-demo")
ALGORITHM = "HS256"

bearer = HTTPBearer()


def create_token(phone: str) -> str:
    """Login token for this phone number.

    It has no expiry. The user stays logged in until they log out
    (the app deletes the token) or delete their account.
    """
    return jwt.encode({"phone": phone}, SECRET_KEY, algorithm=ALGORITHM)


def get_current_phone(creds: HTTPAuthorizationCredentials = Depends(bearer)) -> str:
    """Use this in any endpoint that needs a logged-in user."""
    try:
        payload = jwt.decode(creds.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["phone"]
    except (jwt.PyJWTError, KeyError):
        raise HTTPException(status_code=401, detail="Invalid token")