"""Run the backend WITH automation, without editing any backend file.

    cd backend
    PYTHONPATH=.. uvicorn automation.server:app --reload

It imports the backend's `app` (backend/main.py), starts the alert worker + wave timer in the background,
and adds these routes:
  GET  /automation/telegram-link        (donor logged in) -> link that connects their Telegram
  POST /automation/telegram/webhook     (only if TELEGRAM_MODE=webhook)
  GET  /a/{token}   POST /a/{token}/accept     accept page opened from the Telegram message link
  GET  /automation/health
NOT run in the build sandbox (no FastAPI / SQLAlchemy there): run it once and fix typos first.
"""
import html
import logging
import os
import secrets
import threading
import time

from fastapi import Depends, HTTPException, Request
from fastapi.responses import HTMLResponse

from main import app                       # backend/main.py, untouched
from security import get_current_phone     # backend login (JWT)

from . import messages as M
from .bridge import Bridge
from .channels import TelegramChannel
from .links import verify_token
from .responder import respond
from .store import Store
from .telegram_link import handle_update, poll_forever, start_link
from .tts import GTTS, NullTTS
from .worker import Worker

log = logging.getLogger("bloodlink.automation")

SECRET = os.getenv("BLOODLINK_SECRET") or secrets.token_hex(16)
if not os.getenv("BLOODLINK_SECRET"):
    log.warning("BLOODLINK_SECRET not set: links stop working after a restart. Set it in your environment.")
BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://localhost:8000")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
BOT_USERNAME = os.getenv("TELEGRAM_BOT_USERNAME", "")
TELEGRAM_MODE = os.getenv("TELEGRAM_MODE", "poll")   # poll = local dev, webhook = deployed with https
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "hi")
CONFIRM_SECONDS = int(os.getenv("CONFIRM_WINDOW_SECONDS", "15"))
RECEIVER_CHAT_IDS = dict(p.split(":", 1) for p in os.getenv("RECEIVER_CHAT_IDS", "").split(",") if ":" in p)

bridge, store = Bridge(), Store()
tg = TelegramChannel(BOT_TOKEN) if BOT_TOKEN else None
channels = {"telegram": tg} if tg else {}
audio_dir = os.getenv("AUDIO_DIR") or os.path.join(os.path.dirname(__file__), "audio_cache")
tts = GTTS(audio_dir) if os.getenv("ENABLE_TTS", "1") == "1" else NullTTS()
worker = Worker(bridge, store, channels, secret=SECRET, base_url=BASE_URL, tts=tts,
                default_language=DEFAULT_LANGUAGE, receiver_chat_ids=RECEIVER_CHAT_IDS,
                run_scheduler=os.getenv("RUN_SCHEDULER", "1") == "1", confirm_seconds=CONFIRM_SECONDS)

_started = False


def _start_background():
    global _started
    if _started:
        return
    _started = True

    def loop():
        while True:
            try:
                worker.tick()
            except Exception:
                log.exception("worker tick failed")
            time.sleep(1)

    threading.Thread(target=loop, daemon=True, name="alert-worker").start()
    if tg and TELEGRAM_MODE == "poll":
        threading.Thread(target=poll_forever, daemon=True, name="tg-poll",
                         args=(bridge, store, tg, SECRET, DEFAULT_LANGUAGE, CONFIRM_SECONDS)).start()


_start_background()


def _page(title, body):
    return (f"<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>"
            f"<title>{html.escape(title)}</title><body style='font-family:sans-serif;max-width:480px;margin:2rem auto;padding:0 1rem'>"
            f"<h2>{html.escape(title)}</h2>{body}</body>")


@app.get("/automation/health")
def health():
    return {"telegram": bool(tg), "mode": TELEGRAM_MODE if tg else None, "tts": type(tts).__name__,
            "scheduler": worker.run_scheduler, "recent_deliveries": list(worker.log)[-10:]}


@app.get("/automation/telegram-link")
def telegram_link(phone: str = Depends(get_current_phone)):
    donor_id = bridge.donor_id_for_phone(phone)
    if donor_id is None or not BOT_USERNAME:
        raise HTTPException(status_code=404, detail="Not registered as a donor, or TELEGRAM_BOT_USERNAME not set.")
    return {"url": start_link(BOT_USERNAME, SECRET, donor_id)}


@app.post("/automation/telegram/webhook")
async def telegram_webhook(request: Request):
    if tg:
        handle_update(bridge, store, tg, await request.json(), SECRET, DEFAULT_LANGUAGE, CONFIRM_SECONDS)
    return {"ok": True}


@app.get("/a/{token}")
def accept_page(token: str):
    aid = verify_token(SECRET, "a", token)
    snap = bridge.snapshot(aid) if aid else None
    if snap is None:
        return HTMLResponse(_page("Invalid link", "<p>This link is not valid.</p>"), status_code=404)
    if snap["response"] != "pending":
        return HTMLResponse(_page("Request closed", f"<p>{html.escape(M.render('closed', 'en'))}</p>"))
    body = (f"<p><b>{html.escape(snap['blood_group'])}</b> needed at <b>{html.escape(snap['hospital'])}</b>"
            f" ({snap['distance_km']} km away).</p>"
            f"<form method=post action='/a/{html.escape(token)}/accept'>"
            f"<button style='font-size:1.4rem;padding:1rem 2rem'>✅ Accept</button></form>")
    return HTMLResponse(_page("Blood needed near you", body))


@app.post("/a/{token}/accept")
def accept_action(token: str):
    aid = verify_token(SECRET, "a", token)
    snap = bridge.snapshot(aid) if aid else None
    if snap is None:
        return HTMLResponse(_page("Invalid link", "<p>This link is not valid.</p>"), status_code=404)
    lang = store.language(snap["donor_id"]) or DEFAULT_LANGUAGE
    text, _ = respond(bridge, store, aid, "acc", lang, CONFIRM_SECONDS)
    return HTMLResponse(_page("BloodLink", f"<p>{html.escape(text)}</p>"))
