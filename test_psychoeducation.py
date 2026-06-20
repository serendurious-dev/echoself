"""psychoeducation: a normalizing word on what a feeling is doing, in the acute moments."""

import unittest

from psychology import psychoeducation
from core.companion import Conversation


class TestPsychoeducationKB(unittest.TestCase):

    def test_entries_have_a_line_and_a_source(self):
        for emo in ("fear", "sadness", "anger", "shame", "grief", "loneliness", "numbness", "overwhelm"):
            note = psychoeducation.explain(emo)
            self.assertIsNotNone(note, emo)
            self.assertTrue(note["line"] and note["source"], emo)

    def test_unknown_feeling_has_no_note(self):
        self.assertIsNone(psychoeducation.line("joy"))


class TestPsychoeducationInTalk(unittest.TestCase):

    def test_panic_offer_leads_with_what_is_happening(self):
        c = Conversation()
        c.say("i'm so terrified and panicking and scared")
        r = c.say("i'm so terrified and panicking and scared")
        self.assertIn(psychoeducation.line("fear"), r["reply"])   # the normalizing word
        from psychology import frameworks
        self.assertIn(frameworks.offer_line("dbt_tipp"), r["reply"])  # still offers the tool

    def test_mild_fear_does_not_lecture(self):
        c = Conversation()
        c.say("i'm a bit anxious")
        r = c.say("i'm a bit anxious")
        self.assertNotIn(psychoeducation.line("fear"), r["reply"])


if __name__ == "__main__":
    unittest.main()
