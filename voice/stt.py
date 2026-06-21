"""she listens - local speech-to-text with Vosk.

offline and on this machine: your voice is turned into text right here and the
audio is dropped, never stored or sent. optional and off by default; needs the
voice extra and a downloaded Vosk model. point ECHOSELF_STT_MODEL at the model
folder, or drop one in voice/models/vosk/.

like tts.py, all the unverifiable audio bits are isolated here; if it's not
installed or it errors, the app just stays type-only."""

import importlib.util
import json
import os

MODEL_ENV = "ECHOSELF_STT_MODEL"
RATE      = 16000

_model = None   # cached Vosk model


def model_path():
    if os.environ.get(MODEL_ENV):
        return os.environ[MODEL_ENV]
    here = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models", "vosk")
    return here if os.path.isdir(here) else None


def available():
    if not all(importlib.util.find_spec(m) for m in ("vosk", "sounddevice")):
        return False
    return model_path() is not None


def _load():
    global _model
    if _model is None:
        from vosk import Model
        _model = Model(model_path())
    return _model


def listen(max_seconds=8.0, silence_tail=1.0):
    # record from the mic until a short silence (or the cap) and return the text.
    # the audio buffer is local and dropped when this returns. raises on failure.
    import queue
    import sounddevice as sd
    from vosk import KaldiRecognizer

    rec = KaldiRecognizer(_load(), RATE)
    q   = queue.Queue()
    sd_in = sd.RawInputStream(samplerate=RATE, blocksize=8000, dtype="int16",
                              channels=1, callback=lambda data, *a: q.put(bytes(data)))
    import time
    text, last_voice, start = "", time.time(), time.time()
    with sd_in:
        while time.time() - start < max_seconds:
            chunk = q.get()
            if rec.AcceptWaveform(chunk):
                piece = json.loads(rec.Result()).get("text", "")
                if piece:
                    text = (text + " " + piece).strip()
                    last_voice = time.time()
            elif time.time() - last_voice > silence_tail and text:
                break
    piece = json.loads(rec.FinalResult()).get("text", "")
    if piece:
        text = (text + " " + piece).strip()
    return text
