"""tests for the portrait - what she remembers about you between sittings.

model A: distilled facts, never transcripts; readable and deletable; offline
gives patterns from the emotion rhythm, the model gives real content facts."""

import datetime
import tempfile
import unittest

from core import portrait, companion, datastore


class _DataDir(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._old = datastore.DATA_DIR
        datastore.DATA_DIR = self._tmp.name

    def tearDown(self):
        datastore.DATA_DIR = self._old
        self._tmp.cleanup()


class TestStore(_DataDir):

    def test_remember_and_read_back(self):
        portrait.remember("the thesis is heavy", kind="weight")
        texts = [f["text"] for f in portrait.facts()]
        self.assertIn("the thesis is heavy", texts)

    def test_saying_it_again_refreshes_not_duplicates(self):
        a = portrait.remember("running helps", kind="lift")
        b = portrait.remember("Running helps.", kind="lift")   # same fact, said again
        self.assertEqual(len(portrait.facts()), 1)
        self.assertGreater(b["weight"], a["weight"])           # it rose, didn't clone

    def test_forget_one_line(self):
        f = portrait.remember("a passing note")
        self.assertTrue(portrait.forget(f["id"]))
        self.assertEqual(portrait.facts(), [])

    def test_strongest_and_freshest_come_first(self):
        portrait.remember("weaker", kind="note")
        strong = portrait.remember("stronger", kind="note")
        portrait.remember("stronger", kind="note")            # bump it
        self.assertEqual(portrait.facts()[0]["text"], "stronger")
        self.assertEqual(portrait.facts()[0]["id"], strong["id"])


class TestStaleness(_DataDir):

    def test_old_patterns_fade_but_your_own_words_stay(self):
        old = (datetime.date.today() - datetime.timedelta(days=40))
        portrait.remember("weekends sat heavier", kind="pattern", source="pattern", when=old)
        portrait.remember("I want to learn the guitar", kind="goal", source="you", when=old)
        texts = [f["text"] for f in portrait.facts()]
        self.assertNotIn("weekends sat heavier", texts)        # pattern aged out (>21d)
        self.assertIn("I want to learn the guitar", texts)     # your own fact stays


class TestPatternsFromRhythm(_DataDir):

    def _log(self, emo, intensity, date):
        datastore.append_csv(companion.CONV_LOG, companion.CONV_FIELDS,
                             {"date": date.isoformat(), "time": "20:00",
                              "emotion": emo, "intensity": intensity})

    def test_a_dominant_feeling_becomes_a_pattern(self):
        for i in range(8):
            self._log("sadness", 0.6, datetime.date.today() - datetime.timedelta(days=i))
        found = portrait.refresh_patterns()
        self.assertTrue(any("sadness" in t for t in found))
        self.assertTrue(any(f["kind"] == "pattern" for f in portrait.facts()))

    def test_weekend_heaviness_is_noticed(self):
        d, we, wd = datetime.date(2026, 6, 1), 0, 0
        while we < 4 or wd < 4:
            if d.weekday() >= 5 and we < 4:
                self._log("sadness", 0.8, d); we += 1
            elif d.weekday() < 5 and wd < 4:
                self._log("sadness", 0.2, d); wd += 1
            d += datetime.timedelta(days=1)
        found = portrait.refresh_patterns()
        self.assertTrue(any("weekend" in t for t in found))

    def test_refresh_replaces_old_patterns(self):
        portrait.remember("stale pattern", kind="pattern", source="pattern")
        portrait.refresh_patterns()                            # no log data -> none found
        self.assertFalse(any(f["text"] == "stale pattern" for f in portrait.facts()))


class TestOpenerHint(_DataDir):

    def test_fresh_weight_is_what_she_opens_on(self):
        today = datetime.date.today()
        portrait.remember("the thesis", kind="weight", when=today)
        hint = portrait.opener_hint(today)
        self.assertIsNotNone(hint)
        self.assertEqual(hint["text"], "the thesis")

    def test_old_or_light_facts_are_not_surfaced(self):
        today = datetime.date.today()
        portrait.remember("an old weight", kind="weight",
                          when=today - datetime.timedelta(days=20))
        portrait.remember("just a note", kind="note", when=today)
        self.assertIsNone(portrait.opener_hint(today))


class TestConversationUsesPortrait(_DataDir):

    def _now(self, hour=14):
        return datetime.datetime(datetime.date.today().year, datetime.date.today().month,
                                 datetime.date.today().day, hour, 0)

    def test_she_opens_on_what_weighs_on_you(self):
        portrait.remember("the thesis", kind="weight", when=datetime.date.today())
        conv = companion.Conversation(now=self._now())
        self.assertIn("thesis", conv.open())

    def test_the_model_path_distills_a_fact_on_leaving(self):
        def fake_distill(history):
            return [{"kind": "weight", "text": "the thesis is hanging over them"}]

        conv = companion.Conversation(llm=lambda *a, **k: "ok",
                                      distiller=fake_distill, now=self._now())
        conv.open()
        conv.say("today was rough")
        conv.end()
        kept = [f["text"] for f in portrait.facts()]
        self.assertTrue(any("thesis" in t for t in kept))
        self.assertTrue(all(f["source"] != "you" for f in portrait.facts()))

    def test_offline_leaving_invents_no_content_facts(self):
        conv = companion.Conversation(now=self._now())     # no model, no distiller
        conv.open()
        conv.say("I feel a little sad")
        conv.end()
        # one row isn't enough for a pattern, and offline can't honestly pull a
        # content fact - so she keeps nothing rather than guessing
        self.assertEqual(portrait.facts(), [])


if __name__ == "__main__":
    unittest.main()
