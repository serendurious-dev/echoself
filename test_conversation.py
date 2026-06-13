"""tests for the multi-turn thread: she holds context, deepens instead of
repeating, opens to the user's real time of day, keeps nothing on disk, and never
lets a crisis reach the model."""

import datetime
import tempfile
import unittest

from core import companion, datastore, timeofday


class TestTimeOfDay(unittest.TestCase):

    def test_dayparts_split_the_clock(self):
        at = lambda h: datetime.datetime(2026, 6, 13, h, 0)
        self.assertEqual(timeofday.daypart(at(2)),  "deep_night")
        self.assertEqual(timeofday.daypart(at(6)),  "early_morning")
        self.assertEqual(timeofday.daypart(at(10)), "morning")
        self.assertEqual(timeofday.daypart(at(14)), "afternoon")
        self.assertEqual(timeofday.daypart(at(19)), "evening")
        self.assertEqual(timeofday.daypart(at(23)), "night")

    def test_late_softens(self):
        self.assertTrue(timeofday.is_late(datetime.datetime(2026, 6, 13, 1, 0)))
        self.assertFalse(timeofday.is_late(datetime.datetime(2026, 6, 13, 10, 0)))


class TestConversationThread(unittest.TestCase):

    def setUp(self):
        # the Conversation loads the drift on creation; sandbox it so these read
        # a clean slate, not whatever's in the real data dir
        self._tmp = tempfile.TemporaryDirectory()
        self._old = datastore.DATA_DIR
        datastore.DATA_DIR = self._tmp.name

    def tearDown(self):
        datastore.DATA_DIR = self._old
        self._tmp.cleanup()

    def _conv(self, hour=14):
        # offline (no llm injected, no key in the test env), with a fixed clock
        return companion.Conversation(now=datetime.datetime(2026, 6, 13, hour, 0))

    def test_opener_fits_the_users_time(self):
        night = self._conv(hour=2).open()
        self.assertIn(night, companion.OPENERS["deep_night"])
        day = self._conv(hour=10).open()
        self.assertIn(day, companion.OPENERS["morning"])

    def test_first_heavy_feeling_invites_more(self):
        conv = self._conv()
        conv.open()
        r = conv.say("honestly I feel so empty and tired")
        self.assertEqual(r["emotion"], "sadness")
        self.assertIn("?", r["reply"])              # a follow-up keeps the thread open

    def test_staying_on_a_feeling_deepens_instead_of_repeating(self):
        conv = self._conv()
        conv.open()
        r1 = conv.say("I feel so empty and sad")
        r2 = conv.say("still sad, it won't lift")
        self.assertNotEqual(r1["reply"], r2["reply"])
        # the second turn comes from the deepen pool - she goes with you, no
        # second interrogation
        self.assertIn(r2["reply"], companion.RESPONSES["sadness"]["deepen"])

    def test_she_does_not_repeat_herself_across_a_thread(self):
        conv = self._conv()
        conv.open()
        said = ["I feel empty and sad", "still sad", "so sad and low"]
        replies = [conv.say(s)["reply"] for s in said]
        self.assertEqual(len(set(replies)), len(replies))

    def test_joy_is_savored_not_questioned_on_the_way_in(self):
        conv = self._conv()
        conv.open()
        r = conv.say("today was wonderful, I feel proud and hopeful")
        self.assertEqual(r["emotion"], "joy")
        self.assertIn(r["reply"], companion.RESPONSES["joy"]["lines"])

    def test_crisis_ends_the_thread_into_real_help(self):
        conv = self._conv()
        conv.open()
        r = conv.say("I'm so tired of everything, I want to die")
        self.assertTrue(r["crisis"])
        self.assertIn("109", r["reply"])
        self.assertTrue(conv.ended)


class TestFriendVsTeacher(unittest.TestCase):
    # she reads how you are and how you've been, and answers as the right one - a
    # friend when you're hurting, a gentle teacher when you're just dodging.

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._old = datastore.DATA_DIR
        datastore.DATA_DIR = self._tmp.name

    def tearDown(self):
        datastore.DATA_DIR = self._old
        self._tmp.cleanup()

    def _state(self, s):
        datastore.save_json("user_model.json", {"last_state": s})

    def _conv(self):
        return companion.Conversation(now=datetime.datetime(2026, 6, 13, 19, 0))

    def test_the_stance_rules(self):
        self.assertEqual(companion.stance("sadness", "Avoiding"), "friend")   # hurting wins
        self.assertEqual(companion.stance("neutral", "Avoiding"), "teacher")  # dodging
        self.assertEqual(companion.stance("neutral", "Flowing"), "friend")
        self.assertEqual(companion.stance("joy", "Avoiding"), "celebrate")
        self.assertEqual(companion.stance("neutral", None), "friend")         # no read yet

    def test_teacher_when_youre_capable_and_dodging(self):
        self._state("Avoiding")
        conv = self._conv()
        conv.open()
        r = conv.say("eh, i didn't really do much today")        # neutral + avoiding
        self.assertTrue(any(r["reply"].startswith(l) for l in companion.TEACHER["lines"]))
        self.assertIn("?", r["reply"])                            # and she asks the question

    def test_always_a_friend_when_youre_hurting_even_if_avoiding(self):
        self._state("Avoiding")
        conv = self._conv()
        conv.open()
        r = conv.say("honestly i feel so empty and worthless")    # heavy -> friend, never teacher
        self.assertFalse(any(r["reply"].startswith(l) for l in companion.TEACHER["lines"]))


class TestThreadKeepsNothing(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._old = datastore.DATA_DIR
        datastore.DATA_DIR = self._tmp.name

    def tearDown(self):
        datastore.DATA_DIR = self._old
        self._tmp.cleanup()

    def test_the_words_live_only_in_memory(self):
        conv = companion.Conversation(now=datetime.datetime(2026, 6, 13, 14, 0))
        conv.open()
        conv.say("I feel so alone tonight")
        conv.say("nobody really sees me")
        # the thread is in RAM
        self.assertTrue(any(role == "you" for role, _t, _e in conv.history))
        # but the Conversation itself wrote nothing - logging the emotion is the
        # caller's separate, word-free choice
        self.assertEqual(companion.recent_emotions(), [])


class TestThreadAndTheModel(unittest.TestCase):

    def test_model_gets_the_thread(self):
        captured = {}

        def fake_llm(text, emo, stance, history=None):
            captured["history"] = history
            return "a model line, in context"

        conv = companion.Conversation(llm=fake_llm,
                                      now=datetime.datetime(2026, 6, 13, 14, 0))
        conv.open()
        conv.say("hey")
        r = conv.say("I'm anxious about tomorrow")
        self.assertEqual(r["reply"], "a model line, in context")
        self.assertIsNotNone(captured["history"])
        self.assertGreaterEqual(len(captured["history"]), 2)   # opener + first exchange

    def test_a_plain_three_arg_model_still_works(self):
        def old_llm(text, emo, stance):
            return "three-arg reply"

        conv = companion.Conversation(llm=old_llm,
                                      now=datetime.datetime(2026, 6, 13, 14, 0))
        conv.open()
        self.assertEqual(conv.say("hello")["reply"], "three-arg reply")

    def test_crisis_never_reaches_the_model(self):
        def must_not_run(*a, **k):
            raise AssertionError("a crisis message must never reach the model")

        conv = companion.Conversation(llm=must_not_run,
                                      now=datetime.datetime(2026, 6, 13, 14, 0))
        conv.open()
        self.assertTrue(conv.say("I want to die")["crisis"])


if __name__ == "__main__":
    unittest.main()
