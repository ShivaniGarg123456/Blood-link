"""Delivery channels. One class per channel, all with the same two methods, so adding
WhatsApp later means adding one class here. Only Telegram + the in-app alert page are built."""
import json
import threading
import urllib.request
import uuid
from dataclasses import dataclass
from typing import Optional


@dataclass
class Message:
    kind: str                      # alert | audio | reminder | confirmed_donor | confirmed_receiver | standby
    text: str
    voice_text: str = ""           # what the alert page speaks aloud
    language: str = "en"
    link: str = ""
    accept_url: str = ""
    audio_path: Optional[str] = None
    alert_id: Optional[int] = None
    request_id: Optional[int] = None
    donor_id: Optional[int] = None
    seconds_left: int = 0


@dataclass
class DeliveryResult:
    ok: bool
    channel: str
    detail: str = ""


class Channel:
    name = "base"

    def available(self, party) -> bool:
        return True

    def send(self, party, msg: Message) -> DeliveryResult:
        raise NotImplementedError


def default_http(url, data=None, headers=None, timeout=10):
    req = urllib.request.Request(url, data=data, headers=headers or {}, method="POST" if data is not None else "GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status, resp.read()


def build_multipart(fields: dict, file_field: str, path: str, mime="audio/mpeg"):
    boundary = uuid.uuid4().hex
    parts = [f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
             for k, v in fields.items()]
    with open(path, "rb") as fh:
        blob = fh.read()
    name = path.replace("\\", "/").rsplit("/", 1)[-1]
    parts.append((f'--{boundary}\r\nContent-Disposition: form-data; name="{file_field}"; filename="{name}"\r\n'
                  f'Content-Type: {mime}\r\n\r\n').encode() + blob + b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())
    return b"".join(parts), f"multipart/form-data; boundary={boundary}"


BUTTONS = {"en": ("✅ Accept", "❌ Can't come"), "hi": ("✅ स्वीकार करें", "❌ नहीं आ सकता")}


class TelegramChannel(Channel):
    """Donor must press /start once on the bot (see telegram_link.py) so we get a chat_id."""
    name = "telegram"

    def __init__(self, token, http=default_http, api_base="https://api.telegram.org"):
        self.base = f"{api_base}/bot{token}"
        self.http = http

    def available(self, party):
        return bool(getattr(party, "chat_id", None))

    def _call(self, method, payload, timeout=10):
        _, body = self.http(f"{self.base}/{method}", json.dumps(payload).encode(),
                            {"Content-Type": "application/json"}, timeout)
        data = json.loads(body)
        if not data.get("ok"):
            raise RuntimeError(data.get("description", "telegram error"))
        return data.get("result")

    def _keyboard(self, msg):
        if msg.kind not in ("alert", "audio", "reminder") or msg.alert_id is None:
            return None
        yes, no = BUTTONS.get(msg.language, BUTTONS["en"])
        return {"inline_keyboard": [[{"text": yes, "callback_data": f"acc:{msg.alert_id}"},
                                     {"text": no, "callback_data": f"dec:{msg.alert_id}"}]]}

    def send(self, party, msg):
        kb = self._keyboard(msg)
        if msg.kind == "audio" and msg.audio_path:
            fields = {"chat_id": party.chat_id, "caption": msg.text}
            if kb:
                fields["reply_markup"] = json.dumps(kb)
            body, ctype = build_multipart(fields, "audio", msg.audio_path)
            _, raw = self.http(f"{self.base}/sendAudio", body, {"Content-Type": ctype}, 30)
            if not json.loads(raw).get("ok"):
                raise RuntimeError("sendAudio failed")
        else:
            payload = {"chat_id": party.chat_id, "text": msg.text}
            if kb:
                payload["reply_markup"] = kb
            self._call("sendMessage", payload)
        return DeliveryResult(True, self.name)

    # helpers used by telegram_link.py
    def send_text(self, chat_id, text):
        return self._call("sendMessage", {"chat_id": chat_id, "text": text})

    def answer_callback(self, callback_id, text):
        return self._call("answerCallbackQuery", {"callback_query_id": callback_id, "text": text[:190]})

    def get_updates(self, offset=0, timeout=25):
        return self._call("getUpdates", {"offset": offset, "timeout": timeout,
                                         "allowed_updates": ["message", "callback_query"]}, timeout + 5)

    def delete_webhook(self):
        return self._call("deleteWebhook", {})


class InAppChannel(Channel):
    """Queue read by the donor's alert page (web/siren.js polls poll()). This is the siren path."""
    name = "in_app"

    def __init__(self, clock, is_active=lambda alert_id: True):
        self.clock = clock
        self.is_active = is_active  # set by the dispatcher
        self._queue = {}
        self._lock = threading.Lock()

    def send(self, party, msg):
        with self._lock:
            item = {"alert_id": msg.alert_id, "request_id": msg.request_id, "kind": msg.kind,
                    "text": msg.text, "voice_text": msg.voice_text, "language": msg.language,
                    "accept_url": msg.accept_url, "expires_at": self.clock().timestamp() + msg.seconds_left}
            self._queue.setdefault(party.id, []).append(item)
        return DeliveryResult(True, self.name)

    def poll(self, donor_id):
        now = self.clock().timestamp()
        alerts, events, keep = [], [], []
        with self._lock:
            for it in self._queue.get(donor_id, []):
                if it["kind"] == "alert":
                    if it["expires_at"] > now and self.is_active(it["alert_id"]):
                        keep.append(it)
                        alerts.append({**{k: it[k] for k in ("alert_id", "request_id", "text", "voice_text",
                                                             "language", "accept_url")},
                                       "seconds_left": int(it["expires_at"] - now)})
                else:
                    events.append({"kind": it["kind"], "text": it["text"]})  # delivered once
            self._queue[donor_id] = keep
        return {"alerts": alerts, "events": events}
