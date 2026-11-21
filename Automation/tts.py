"""Text-to-speech for the Telegram audio clip. Optional: no TTS -> text reminder is sent instead."""
import hashlib
import os


class NullTTS:
    def synth(self, text, lang):
        return None


class GTTS:
    """Needs `pip install gTTS` and internet. Clips are cached by text, so a repeat is instant."""

    def __init__(self, directory="audio_cache"):
        self.directory = directory
        os.makedirs(directory, exist_ok=True)

    def synth(self, text, lang):
        path = os.path.join(self.directory, hashlib.sha1(f"{lang}:{text}".encode()).hexdigest()[:16] + ".mp3")
        if os.path.exists(path):
            return path
        try:
            from gtts import gTTS
            gTTS(text=text, lang="hi" if lang == "hi" else "en", tld="co.in").save(path)
            return path
        except Exception:
            return None
