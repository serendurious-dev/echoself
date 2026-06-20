"""turn a handful of named face points into a few normalized feelings-of-the-face.

pure geometry, no camera and no model - capture.py pulls the named points out of
mediapipe and hands them here. everything is scaled by the distance between the
eyes, so it doesn't matter how near or far the face is from the lens."""

import math

# the read we extract per frame, in a fixed order for the model
FEATURES = ["mouth_curve", "mouth_open", "eye_open", "brow", "tilt"]

# the named points capture.py must provide (each an (x, y))
KEYPOINTS = ["eye_l_out", "eye_r_out", "eye_l_top", "eye_l_bot", "eye_r_top",
             "eye_r_bot", "mouth_l", "mouth_r", "mouth_top", "mouth_bot",
             "brow_l", "brow_r"]


def _dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _mid_y(a, b):
    return (a[1] + b[1]) / 2.0


def features_from_keypoints(kp):
    # returns the feature dict. y grows downward (image coords), so "higher on the
    # face" means a smaller y - the signs below account for that.
    unit = _dist(kp["eye_l_out"], kp["eye_r_out"]) or 1e-6   # interocular = the ruler

    corners_y = _mid_y(kp["mouth_l"], kp["mouth_r"])
    center_y  = _mid_y(kp["mouth_top"], kp["mouth_bot"])
    mouth_curve = (center_y - corners_y) / unit        # + = corners lifted = smile
    mouth_open  = _dist(kp["mouth_top"], kp["mouth_bot"]) / unit

    eye_open = ((_dist(kp["eye_l_top"], kp["eye_l_bot"]) +
                 _dist(kp["eye_r_top"], kp["eye_r_bot"])) / 2.0) / unit

    brow_y = _mid_y(kp["brow_l"], kp["brow_r"])
    lid_y  = _mid_y(kp["eye_l_top"], kp["eye_r_top"])
    brow   = (lid_y - brow_y) / unit                   # + = brows lifted, - = furrowed

    dx = kp["eye_r_out"][0] - kp["eye_l_out"][0]
    dy = kp["eye_r_out"][1] - kp["eye_l_out"][1]
    tilt = math.atan2(dy, dx)                          # head roll, radians

    return {"mouth_curve": mouth_curve, "mouth_open": mouth_open,
            "eye_open": eye_open, "brow": brow, "tilt": tilt}


def to_vector(feat):
    return [float(feat[f]) for f in FEATURES]
