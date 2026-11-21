"""Signed tokens for accept links and Telegram /start linking (stdlib only)."""
import hashlib
import hmac


def make_token(secret: str, kind: str, ident: int) -> str:
    sig = hmac.new(secret.encode(), f"{kind}:{ident}".encode(), hashlib.sha256).hexdigest()[:16]
    return f"{ident}_{sig}"  # only [0-9a-f_] so it is valid in URLs and Telegram start params


def verify_token(secret: str, kind: str, token: str):
    try:
        ident, sig = token.split("_", 1)
        good = hmac.new(secret.encode(), f"{kind}:{int(ident)}".encode(), hashlib.sha256).hexdigest()[:16]
    except (ValueError, AttributeError):
        return None
    return int(ident) if hmac.compare_digest(sig, good) else None
