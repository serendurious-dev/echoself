"""her voice - local neural text-to-speech with Piper.

offline and on this machine: nothing she says is sent anywhere. optional and off
by default; needs the voice extra (requirements-voice.txt) and a downloaded Piper
voice model. point ECHOSELF_TTS_MODEL at a .onnx voice, or drop one in voice/models/.

all the heavy, hard-to-verify bits live here on purpose - if it isn't installed,
or it errors, the app just stays text-only."""

import glob
import importlib.util
import os

MODEL_ENV = "ECHOSELF_TTS_MODEL"

_voice = None   # cached PiperVoice


def _models_dir():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")


def model_path():
    # an explicit env path wins; otherwise the first .onnx voice in voice/models/
    if os.environ.get(MODEL_ENV):
        return os.environ[MODEL_ENV]
    found = sorted(glob.glob(os.path.join(_models_dir(), "*.onnx")))
    return found[0] if found else None


def available():
    # deps present AND a voice model on disk - cheap, never loads the model
    if not all(importlib.util.find_spec(m) for m in ("piper", "sounddevice", "numpy")):
        return False
    return model_path() is not None


def _load():
    global _voice
    if _voice is None:
        from piper.voice import PiperVoice
        _voice = PiperVoice.load(model_path())
    return _voice


def speak(text):
    # synthesize and play, without blocking the caller. raises on any failure so
    # the caller can fall back to silence. (Piper's API has shifted across
    # versions - this targets the raw-PCM stream; adjust here if your build differs.)
    import numpy as np
    import sounddevice as sd
    voice = _load()
    pcm = b"".join(voice.synthesize_stream_raw(text))
    audio = np.frombuffer(pcm, dtype=np.int16)
    rate  = getattr(voice.config, "sample_rate", 22050)
    sd.play(audio, rate)


def stop():
    try:
        import sounddevice as sd
        sd.stop()
    except Exception:
        pass
