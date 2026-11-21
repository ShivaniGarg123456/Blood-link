"""Automation's own tiny database (a sqlite file), so we never touch the backend's tables."""
import os
import sqlite3
import threading


class Store:
    def __init__(self, path=None):
        path = path or os.getenv("AUTOMATION_DB") or os.path.join(os.path.dirname(__file__), "automation.db")
        self._db = sqlite3.connect(path, check_same_thread=False)
        self._lock = threading.Lock()
        with self._lock:
            self._db.executescript("""
                CREATE TABLE IF NOT EXISTS tg (donor_id INTEGER PRIMARY KEY, chat_id TEXT, language TEXT);
                CREATE TABLE IF NOT EXISTS ladder (alert_id INTEGER PRIMARY KEY, step INTEGER);
                CREATE TABLE IF NOT EXISTS events (alert_id INTEGER PRIMARY KEY, response TEXT);
                CREATE TABLE IF NOT EXISTS receiver_sent (alert_id INTEGER PRIMARY KEY);
            """)

    def _run(self, sql, args=()):
        with self._lock:
            self._db.execute(sql, args)
            self._db.commit()

    def _one(self, sql, args=()):
        with self._lock:
            row = self._db.execute(sql, args).fetchone()
        return row[0] if row else None

    # Telegram link + language, per donor
    def link_chat(self, donor_id, chat_id):
        self._run("INSERT INTO tg(donor_id, chat_id) VALUES(?, ?) "
                  "ON CONFLICT(donor_id) DO UPDATE SET chat_id = excluded.chat_id", (donor_id, str(chat_id)))

    def chat_id(self, donor_id):
        return self._one("SELECT chat_id FROM tg WHERE donor_id = ?", (donor_id,))

    def donor_for_chat(self, chat_id):
        return self._one("SELECT donor_id FROM tg WHERE chat_id = ?", (str(chat_id),))

    def set_language(self, donor_id, lang):
        self._run("INSERT INTO tg(donor_id, language) VALUES(?, ?) "
                  "ON CONFLICT(donor_id) DO UPDATE SET language = excluded.language", (donor_id, lang))

    def language(self, donor_id):
        return self._one("SELECT language FROM tg WHERE donor_id = ?", (donor_id,))

    # which ping of the ladder an alert has reached
    def next_step(self, alert_id):
        return self._one("SELECT step FROM ladder WHERE alert_id = ?", (alert_id,)) or 0

    def set_step(self, alert_id, step):
        self._run("INSERT OR REPLACE INTO ladder(alert_id, step) VALUES(?, ?)", (alert_id, step))

    # which result message (confirmed / standby) the donor has already been told
    def last_event(self, alert_id):
        return self._one("SELECT response FROM events WHERE alert_id = ?", (alert_id,))

    def set_event(self, alert_id, response):
        self._run("INSERT OR REPLACE INTO events(alert_id, response) VALUES(?, ?)", (alert_id, response))

    def receiver_done(self, alert_id):
        return self._one("SELECT 1 FROM receiver_sent WHERE alert_id = ?", (alert_id,)) is not None

    def set_receiver_done(self, alert_id):
        self._run("INSERT OR IGNORE INTO receiver_sent(alert_id) VALUES(?)", (alert_id,))
