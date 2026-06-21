"""the live webcam loop - the only part that touches a camera.

mediapipe reads the frame ON THIS MACHINE, we pull a few named points out of it,
turn them into features, and DROP the frame. no image is ever stored or sent. the
loop runs in a background thread and only ever hands back an expression name.

needs the optional deps (requirements-vision.txt). verified on a real machine with
a camera, not in the test suite - everything testable lives in features.py and
expression_model.py."""

import importlib.util
import threading

from vision import features
from vision.expression_model import Mirror

# mediapipe face-mesh landmark indices for the points features.py wants. standard
# 468-point mesh; left/right are the image's, which is fine - the geometry is symmetric.
_IDX = {
    "eye_l_out": 33,  "eye_r_out": 263,
    "eye_l_top": 159, "eye_l_bot": 145, "eye_r_top": 386, "eye_r_bot": 374,
    "mouth_l": 61, "mouth_r": 291, "mouth_top": 13, "mouth_bot": 14,
    "brow_l": 105, "brow_r": 334,
}


def available():
    return all(importlib.util.find_spec(m) is not None for m in ("cv2", "mediapipe"))


def _keypoints(landmarks, w, h):
    return {name: (landmarks[i].x * w, landmarks[i].y * h) for name, i in _IDX.items()}


def collect_demos(labels, seconds_each=2.0, camera=0, on_label=None):
    # for each expression name in `labels`, watch the camera for a couple seconds
    # and gather face-feature samples. returns [(feature_dict, label), ...]. frames
    # are read and dropped, never stored. on_label(label) lets the screen show a
    # prompt before each one.
    import time
    import cv2
    import mediapipe as mp
    demos = []
    cap   = cv2.VideoCapture(camera)
    mesh  = mp.solutions.face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=False)
    try:
        for label in labels:
            if on_label:
                on_label(label)
            t_end = time.time() + seconds_each
            while time.time() < t_end and cap.isOpened():
                ok, frame = cap.read()
                if not ok:
                    continue
                h, w = frame.shape[:2]
                res = mesh.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                frame = None
                if not res.multi_face_landmarks:
                    continue
                kp = _keypoints(res.multi_face_landmarks[0].landmark, w, h)
                demos.append((features.features_from_keypoints(kp), label))
    finally:
        cap.release()
        mesh.close()
    return demos


class MirrorRunner:
    # runs the camera in a thread and calls on_expression(name) as your face moves.
    # call stop() to release the camera. the frame never leaves this method.

    def __init__(self, mirror=None, camera=0):
        self.mirror   = mirror or Mirror()
        self.camera   = camera
        self._stop    = threading.Event()
        self._thread  = None
        self.last     = "neutral"

    def start(self, on_expression):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, args=(on_expression,), daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=1.0)

    def _run(self, on_expression):
        import cv2
        import mediapipe as mp
        cap  = cv2.VideoCapture(self.camera)
        mesh = mp.solutions.face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=False)
        try:
            while not self._stop.is_set() and cap.isOpened():
                ok, frame = cap.read()
                if not ok:
                    continue
                h, w = frame.shape[:2]
                res = mesh.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                frame = None   # dropped, always, before anything else
                if not res.multi_face_landmarks:
                    continue
                kp   = _keypoints(res.multi_face_landmarks[0].landmark, w, h)
                name = self.mirror.to_expression(features.features_from_keypoints(kp))
                self.last = name
                on_expression(name)
                # ~12 reads a second is plenty for an expression, and it stops the
                # camera thread from pegging a whole core. wait() also wakes on stop.
                self._stop.wait(0.08)
        finally:
            cap.release()
            mesh.close()
