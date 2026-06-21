"""the voice seam: gated, opt-in, and never allowed to break the conversation.
the real audio (Piper/Vosk) is verified on a machine with a mic; here it's mocked."""

import tempfile
import unittest

import echoself_core
from core import datastore
from voice import tts, stt


class TestVoiceGating(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._old = datastore.DATA_DIR
        datastore.DATA_DIR = self._tmp.name
        self._saved = (tts.available, tts.speak, stt.available, stt.listen)

    def tearDown(self):
        tts.available, tts.speak, stt.available, stt.listen = self._saved
        datastore.DATA_DIR = self._old
        self._tmp.cleanup()

    def test_availability_is_a_bool(self):
        self.assertIn(echoself_core.tts_available(), (True, False))
        self.assertIn(echoself_core.stt_available(), (True, False))

    def test_silent_by_default(self):
        self.assertFalse(echoself_core.speak("hi"))
        self.assertEqual(echoself_core.listen(), "")

    def test_cannot_enable_without_the_engine(self):
        tts.available = lambda: False
        self.assertFalse(echoself_core.set_speak(True))
        self.assertFalse(echoself_core.voice_speaking())

    def test_speaks_when_on_and_available(self):
        said = {}
        tts.available = lambda: True
        tts.speak = lambda t: said.__setitem__("t", t)
        self.assertTrue(echoself_core.set_speak(True))
        self.assertTrue(echoself_core.voice_speaking())
        self.assertTrue(echoself_core.speak("hello"))
        self.assertEqual(said["t"], "hello")

    def test_a_broken_voice_never_raises(self):
        def boom(t):
            raise RuntimeError("no audio device")
        tts.available = lambda: True
        tts.speak = boom
        echoself_core.set_speak(True)
        self.assertFalse(echoself_core.speak("hi"))   # swallowed, stays silent

    def test_listens_when_on(self):
        stt.available = lambda: True
        stt.listen = lambda: "hello there"
        self.assertTrue(echoself_core.set_listen(True))
        self.assertEqual(echoself_core.listen(), "hello there")


if __name__ == "__main__":
    unittest.main()
