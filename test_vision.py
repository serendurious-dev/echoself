"""the affect mirror's testable core: face geometry, the baseline, the learned map.
the webcam loop (vision/capture) is live I/O, verified on a real machine, not here."""

import tempfile
import unittest

import echoself_core
from core import datastore
from vision import features, capture
from vision.expression_model import BaselineMapper, Mirror, torch_available


def _face(mouth_l_y, mouth_r_y, top_y, bot_y, eye_v=10, brow_y=-12):
    # a face with eyes 100 apart (unit=100); tweak the mouth/eye/brow to taste
    return {
        "eye_l_out": (0, 0), "eye_r_out": (100, 0),
        "eye_l_top": (20, -eye_v / 2), "eye_l_bot": (20, eye_v / 2),
        "eye_r_top": (80, -eye_v / 2), "eye_r_bot": (80, eye_v / 2),
        "mouth_l": (30, mouth_l_y), "mouth_r": (70, mouth_r_y),
        "mouth_top": (50, top_y), "mouth_bot": (50, bot_y),
        "brow_l": (20, brow_y), "brow_r": (80, brow_y),
    }


class TestFeatureGeometry(unittest.TestCase):

    def test_smile_reads_positive_curve_frown_negative(self):
        smile = features.features_from_keypoints(_face(60, 60, 64, 70))  # corners up
        frown = features.features_from_keypoints(_face(72, 72, 60, 66))  # corners down
        self.assertGreater(smile["mouth_curve"], 0)
        self.assertLess(frown["mouth_curve"], 0)

    def test_open_eyes_read_more_than_closed(self):
        wide   = features.features_from_keypoints(_face(60, 60, 64, 66, eye_v=24))
        sleepy = features.features_from_keypoints(_face(60, 60, 64, 66, eye_v=4))
        self.assertGreater(wide["eye_open"], sleepy["eye_open"])

    def test_scale_invariant(self):
        # same face, twice as far: features barely move (scaled by eye distance)
        near = features.features_from_keypoints(_face(60, 60, 64, 70))
        kp   = {k: (x * 2, y * 2) for k, (x, y) in _face(60, 60, 64, 70).items()}
        far  = features.features_from_keypoints(kp)
        self.assertAlmostEqual(near["mouth_curve"], far["mouth_curve"], places=5)


class TestBaseline(unittest.TestCase):

    def setUp(self):
        self.b = BaselineMapper()

    def test_each_band(self):
        self.assertEqual(self.b.predict({"mouth_curve": 0.15, "mouth_open": 0.3,
                                         "eye_open": 0.3, "brow": 0.1, "tilt": 0}), "celebrating")
        self.assertEqual(self.b.predict({"mouth_curve": 0.07, "mouth_open": 0.1,
                                         "eye_open": 0.3, "brow": 0.1, "tilt": 0}), "happy")
        self.assertEqual(self.b.predict({"mouth_curve": 0.0, "mouth_open": 0.1,
                                         "eye_open": 0.1, "brow": 0.0, "tilt": 0}), "drift")
        self.assertEqual(self.b.predict({"mouth_curve": 0.0, "mouth_open": 0.1,
                                         "eye_open": 0.3, "brow": -0.05, "tilt": 0}), "thinking")
        self.assertEqual(self.b.predict({"mouth_curve": -0.05, "mouth_open": 0.1,
                                         "eye_open": 0.3, "brow": 0.0, "tilt": 0}), "patient")
        self.assertEqual(self.b.predict({"mouth_curve": 0.0, "mouth_open": 0.1,
                                         "eye_open": 0.3, "brow": 0.0, "tilt": 0}), "neutral")


class TestMirror(unittest.TestCase):

    def test_uses_baseline_before_calibration(self):
        m = Mirror()
        feat = {"mouth_curve": 0.07, "mouth_open": 0.1, "eye_open": 0.3, "brow": 0.1, "tilt": 0}
        self.assertEqual(m.to_expression(feat), "happy")

    @unittest.skipUnless(torch_available(), "needs pytorch")
    def test_learns_your_expressions_from_demonstrations(self):
        m = Mirror()
        happy   = {"mouth_curve": 0.2, "mouth_open": 0.3, "eye_open": 0.3, "brow": 0.1, "tilt": 0}
        thinking = {"mouth_curve": -0.1, "mouth_open": 0.05, "eye_open": 0.3, "brow": -0.1, "tilt": 0}
        drift   = {"mouth_curve": 0.0, "mouth_open": 0.1, "eye_open": 0.08, "brow": 0.0, "tilt": 0}
        demos = ([(happy, "happy")] * 8 + [(thinking, "thinking")] * 8 + [(drift, "drift")] * 8)
        self.assertTrue(m.calibrate(demos))
        self.assertEqual(m.to_expression(happy), "happy")
        self.assertEqual(m.to_expression(thinking), "thinking")
        self.assertEqual(m.to_expression(drift), "drift")


class TestCalibration(unittest.TestCase):
    # teaching the model your faces, saving it, and getting it back

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._old = datastore.DATA_DIR
        datastore.DATA_DIR = self._tmp.name
        self.demos = (
            [({"mouth_curve": 0.2, "mouth_open": 0.3, "eye_open": 0.3, "brow": 0.1, "tilt": 0}, "happy")] * 8 +
            [({"mouth_curve": -0.1, "mouth_open": 0.05, "eye_open": 0.3, "brow": -0.1, "tilt": 0}, "thinking")] * 8 +
            [({"mouth_curve": 0.0, "mouth_open": 0.1, "eye_open": 0.08, "brow": 0.0, "tilt": 0}, "drift")] * 8
        )
        self.happy = {"mouth_curve": 0.2, "mouth_open": 0.3, "eye_open": 0.3, "brow": 0.1, "tilt": 0}

    def tearDown(self):
        datastore.DATA_DIR = self._old
        self._tmp.cleanup()

    @unittest.skipUnless(torch_available(), "needs pytorch")
    def test_calibrate_saves_and_reloads(self):
        self.assertTrue(echoself_core.calibrate_mirror(self.demos))
        self.assertTrue(echoself_core.mirror_calibrated())
        # a fresh Mirror loaded from disk still knows your faces
        m = echoself_core.load_mirror()
        self.assertTrue(m.calibrated())
        self.assertEqual(m.to_expression(self.happy), "happy")

    def test_no_calibration_means_baseline(self):
        m = echoself_core.load_mirror()
        self.assertFalse(m.calibrated())
        # baseline still gives a sensible read
        self.assertEqual(m.to_expression(self.happy), "celebrating")


class TestMirrorGate(unittest.TestCase):
    # opt-in, off by default, and only switchable on when the deps are installed

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._old = datastore.DATA_DIR
        datastore.DATA_DIR = self._tmp.name
        self._avail = capture.available

    def tearDown(self):
        capture.available = self._avail
        datastore.DATA_DIR = self._old
        self._tmp.cleanup()

    def test_off_by_default(self):
        self.assertFalse(echoself_core.mirror_enabled())

    def test_cannot_turn_on_without_the_deps(self):
        capture.available = lambda: False
        self.assertFalse(echoself_core.set_mirror(True))
        self.assertFalse(echoself_core.mirror_enabled())

    def test_turns_on_when_opted_in_and_installed(self):
        capture.available = lambda: True
        self.assertTrue(echoself_core.set_mirror(True))
        self.assertTrue(echoself_core.mirror_enabled())
        echoself_core.set_mirror(False)
        self.assertFalse(echoself_core.mirror_enabled())


if __name__ == "__main__":
    unittest.main()
