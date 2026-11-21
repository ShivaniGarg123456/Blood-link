"""Alert worker: reads the backend's database, sends alerts, runs the wave timer.

Ping ladder (fractions of the alert window, so it also fits a 20-30 s demo timer):
  0.00  Telegram text with Accept / Decline buttons   (the alert page rings by itself, see web/siren.js)
  0.33  Telegram voice clip (falls back to a text reminder if there is no TTS)
  0.66  Telegram reminder with time left
Pings stop as soon as the alert is no longer pending. After a donor is confirmed or put on standby
they get the matching message once. Call tick() about once a second.
All times are UTC, like the backend.
"""
import collections
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime

from . import messages as M
from .channels import DeliveryResult, Message
from .links import make_token

log = logging.getLogger("bloodlink.automation")


@dataclass(frozen=True)
class Step:
    at: float      # fraction of the alert window
    kind: str      # alert | audio | reminder
    groups: tuple  # each group = channels tried in order until one works; every group runs


DEFAULT_LADDER = (
    Step(0.00, "alert", (("telegram",),)),
    Step(0.33, "audio", (("telegram",),)),
    Step(0.66, "reminder", (("telegram",),)),
)


@dataclass
class Party:
    name: str
    phone: str
    language: str = "en"
    chat_id: str = None
    id: int = None


class Worker:
    def __init__(self, bridge, store, channels, *, secret, base_url, ladder=DEFAULT_LADDER, tts=None,
                 default_language="hi", receiver_chat_ids=None, receiver_language="hi",
                 clock=datetime.utcnow, async_send=True, run_scheduler=True, confirm_seconds=15):
        self.bridge, self.store, self.channels = bridge, store, channels
        self.secret, self.base_url = secret, base_url.rstrip("/")
        self.ladder, self.tts = ladder, tts
        self.default_language = default_language
        self.receiver_chat_ids = receiver_chat_ids or {}
        self.receiver_language = receiver_language
        self.clock, self.run_scheduler, self.confirm_seconds = clock, run_scheduler, confirm_seconds
        self.log = collections.deque(maxlen=1000)
        self._pool = ThreadPoolExecutor(max_workers=4) if async_send else None

    # ---- timer: call about once a second ----
    def tick(self, now=None):
        now = now or self.clock()
        if self.run_scheduler:
            self.bridge.scheduler_tick(now)
        for snap in self.bridge.snapshots(now):
            self._handle(snap, now)

    def _handle(self, snap, now):
        aid = snap["alert_id"]
        if snap["response"] == "pending":
            if snap["expires_at"] <= now:
                return
            span = (snap["expires_at"] - snap["sent_at"]).total_seconds()
            age = (now - snap["sent_at"]).total_seconds()
            idx = self.store.next_step(aid)
            while idx < len(self.ladder) and age >= span * self.ladder[idx].at:
                self.store.set_step(aid, idx + 1)       # (after a restart, overdue pings go out together)
                self._submit(self._send_step, snap, idx)
                idx += 1
        elif snap["response"] in ("confirmed", "standby"):
            if self.store.last_event(aid) != snap["response"]:
                self.store.set_event(aid, snap["response"])
                self._submit(self._send_event, snap)
            if snap["response"] == "confirmed" and not self.store.receiver_done(aid):
                self.store.set_receiver_done(aid)
                self._submit(self._send_to_receiver, snap)

    # ---- sending ----
    def _lang(self, donor_id):
        lang = self.store.language(donor_id) or self.default_language
        return lang if lang in ("en", "hi") else "en"

    def _party(self, snap):
        return Party(snap["donor_name"], snap["donor_phone"], self._lang(snap["donor_id"]),
                     self.store.chat_id(snap["donor_id"]), snap["donor_id"])

    def _submit(self, fn, *args):
        if self._pool:
            self._pool.submit(self._safe, fn, *args)
        else:
            fn(*args)

    def _safe(self, fn, *args):
        try:
            fn(*args)
        except Exception as e:  # a delivery bug must never stop the timer
            log.exception("automation task failed")
            self.log.append({"error": repr(e)})

    def _send_step(self, snap, idx):
        step, party = self.ladder[idx], self._party(snap)
        msg = self._build(step.kind, snap, party.language, self.clock())
        fresh = self.bridge.snapshot(snap["alert_id"])   # answered while we prepared the message?
        if not fresh or fresh["response"] != "pending" or fresh["expires_at"] <= self.clock():
            return
        self._deliver(step.groups, party, msg)

    def _build(self, kind, snap, lang, now):
        link = f"{self.base_url}/a/{make_token(self.secret, 'a', snap['alert_id'])}"
        left = (snap["expires_at"] - now).total_seconds()
        f = dict(group=snap["blood_group"], spoken=M.spoken_group(snap["blood_group"], lang),
                 comp=M.component_label(snap["component"], lang), km=snap["distance_km"],
                 hospital=snap["hospital"], left=M.human_window(left, lang), link=link,
                 window=M.human_window((snap["expires_at"] - snap["sent_at"]).total_seconds(), lang))
        voice = M.render("voice", lang, **f)
        audio = None
        if kind == "audio":
            audio = self.tts.synth(voice, lang) if self.tts else None
            if audio is None:
                kind = "reminder"  # no clip -> still nudge the donor
        text_kind = {"alert": "alert", "reminder": "reminder", "audio": "audio_caption"}[kind]
        return Message(kind=kind, text=M.render(text_kind, lang, **f), voice_text=voice, language=lang,
                       link=link, audio_path=audio, alert_id=snap["alert_id"],
                       request_id=snap["request_id"], donor_id=snap["donor_id"], seconds_left=int(left))

    def _send_event(self, snap):
        party = self._party(snap)
        kind = "confirmed_donor" if snap["response"] == "confirmed" else "standby"
        msg = Message(kind=kind, text=M.describe_response(snap, party.language, self.confirm_seconds),
                      language=party.language, alert_id=snap["alert_id"], request_id=snap["request_id"],
                      donor_id=snap["donor_id"])
        self._deliver((("telegram",),), party, msg)

    def _send_to_receiver(self, snap):
        chat = self.receiver_chat_ids.get(snap["receiver_phone"])
        if not chat:
            return  # only a demo receiver linked via RECEIVER_CHAT_IDS gets a Telegram message
        party = Party(snap["receiver_name"], snap["receiver_phone"], self.receiver_language, chat)
        msg = Message(kind="confirmed_receiver", language=self.receiver_language,
                      request_id=snap["request_id"],
                      text=M.render("confirmed_receiver", self.receiver_language,
                                    donor_name=snap["donor_name"], donor_phone=snap["donor_phone"]))
        self._deliver((("telegram",),), party, msg)

    def _deliver(self, groups, party, msg):
        for group in groups:
            for name in group:
                ch = self.channels.get(name)
                if ch is None or not ch.available(party):
                    continue
                try:
                    res = ch.send(party, msg)
                except Exception as e:
                    res = DeliveryResult(False, name, repr(e))
                self.log.append({"alert_id": msg.alert_id, "kind": msg.kind, "channel": name,
                                 "ok": res.ok, "detail": res.detail})
                if res.ok:
                    break  # first working channel in the group wins
