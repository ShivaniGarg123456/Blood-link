"""Telegram side: link a donor's chat with a signed /start token, choose language, handle Accept/Decline buttons."""
import logging
import time

from . import messages as M
from .links import make_token, verify_token
from .responder import respond

log = logging.getLogger("bloodlink.automation")


def start_link(bot_username, secret, donor_id):
    """Shown to the logged-in donor. Opening it links their Telegram chat to their donor id."""
    return f"https://t.me/{bot_username}?start={make_token(secret, 'd', donor_id)}"


def handle_update(bridge, store, tg, update, secret, default_language="hi", confirm_seconds=15):
    msg = update.get("message")
    if msg and (msg.get("text") or "").startswith("/"):
        chat_id = msg["chat"]["id"]
        parts = msg["text"].split(maxsplit=1)
        command = parts[0].split("@")[0].lower()
        if command == "/start":
            donor_id = verify_token(secret, "d", parts[1]) if len(parts) > 1 else None
            if donor_id is None or not bridge.donor_exists(donor_id):
                tg.send_text(chat_id, "This link is not valid. Please open the link shown in the BloodLink app.")
                return "invalid"
            store.link_chat(donor_id, chat_id)
            tg.send_text(chat_id, M.render("linked", store.language(donor_id) or default_language))
            return "linked"
        if command in ("/hindi", "/english"):
            donor_id = store.donor_for_chat(chat_id)
            if donor_id is None:
                return "not_linked"
            lang = "hi" if command == "/hindi" else "en"
            store.set_language(donor_id, lang)
            tg.send_text(chat_id, M.render("language_set", lang))
            return "language"
        return "ignored"

    cb = update.get("callback_query")
    if cb:
        try:
            action, aid = cb["data"].split(":")
            alert_id = int(aid)
        except (ValueError, KeyError):
            tg.answer_callback(cb["id"], "This alert is no longer valid.")
            return "invalid"
        snap = bridge.snapshot(alert_id)
        chat_id = cb["message"]["chat"]["id"]
        if snap is None:
            tg.answer_callback(cb["id"], M.render("closed", default_language))
            return "invalid"
        if store.chat_id(snap["donor_id"]) != str(chat_id):
            tg.answer_callback(cb["id"], "Not allowed.")  # button pressed from someone else's chat
            return "forbidden"
        lang = store.language(snap["donor_id"]) or default_language
        text, _ = respond(bridge, store, alert_id, action, lang, confirm_seconds)
        tg.answer_callback(cb["id"], text)
        tg.send_text(chat_id, text)
        return action
    return "ignored"


def poll_forever(bridge, store, tg, secret, default_language="hi", confirm_seconds=15, stop=lambda: False):
    """Local-dev mode (no public URL needed): long-poll Telegram for updates."""
    try:
        tg.delete_webhook()
    except Exception:
        log.exception("deleteWebhook failed")
    offset = 0
    while not stop():
        try:
            for upd in tg.get_updates(offset, 25):
                offset = upd["update_id"] + 1
                handle_update(bridge, store, tg, upd, secret, default_language, confirm_seconds)
        except Exception:
            log.exception("telegram polling error")
            time.sleep(3)
