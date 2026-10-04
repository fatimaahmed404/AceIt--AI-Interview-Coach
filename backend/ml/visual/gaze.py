"""
Head-pose / head-position estimation from Face Mesh landmarks.

We solve the classic Perspective-n-Point (PnP) problem: given a small set of
3D canonical face points and their 2D projections (from the deep-learning
landmark model), OpenCV's solvePnP recovers the head rotation, which we
convert to yaw / pitch / roll (tilt) in degrees.

    yaw   -> turning left/right
    pitch -> looking up/down
    roll  -> head tilt (sideways)

These angles feed the head-movement metric. We only flag *extreme* or
*repeated* positions as events, so natural movement is not penalised.
"""
import logging

import numpy as np

from config import HEAD_YAW_THRESHOLD, HEAD_PITCH_DOWN_THRESHOLD, HEAD_TILT_THRESHOLD
from .face_analysis import POSE_LANDMARKS

log = logging.getLogger("aceit.gaze")

# Canonical 3D model points (approximate, in an arbitrary face-centred frame).
_MODEL_POINTS = np.array([
    [0.0, 0.0, 0.0],        # nose tip
    [0.0, -63.6, -12.5],    # chin
    [43.3, 32.7, -26.0],    # left eye corner
    [-43.3, 32.7, -26.0],   # right eye corner
    [28.9, -28.9, -24.1],   # left mouth corner
    [-28.9, -28.9, -24.1],  # right mouth corner
], dtype=np.float64)

_ORDER = ["nose_tip", "chin", "left_eye_corner", "right_eye_corner", "left_mouth", "right_mouth"]


def estimate_head_pose(landmarks, frame_size):
    """
    Return {"yaw", "pitch", "roll", "event"} in degrees, or None.

    event is one of: None, "looking_down", "turned_away", "head_tilt".
    """
    if landmarks is None or len(landmarks) < 468:
        return None
    try:
        import cv2

        image_points = np.array(
            [landmarks[POSE_LANDMARKS[name]] for name in _ORDER], dtype=np.float64
        )
        w, h = frame_size
        focal = float(w)
        center = (w / 2.0, h / 2.0)
        camera_matrix = np.array(
            [[focal, 0, center[0]], [0, focal, center[1]], [0, 0, 1]], dtype=np.float64
        )
        dist = np.zeros((4, 1))
        ok, rvec, _ = cv2.solvePnP(
            _MODEL_POINTS, image_points, camera_matrix, dist, flags=cv2.SOLVEPNP_ITERATIVE
        )
        if not ok:
            return None
        rot, _ = cv2.Rodrigues(rvec)
        sy = np.sqrt(rot[0, 0] ** 2 + rot[1, 0] ** 2)
        pitch = np.degrees(np.arctan2(-rot[2, 0], sy))
        yaw = np.degrees(np.arctan2(rot[1, 0], rot[0, 0]))
        roll = np.degrees(np.arctan2(rot[2, 1], rot[2, 2]))
    except Exception as exc:  # noqa: BLE001 - isolate per-frame failures
        log.debug("Head-pose estimation failed on a frame: %s", exc)
        return None

    # Normalise to intuitive ranges.
    yaw = float(((yaw + 180) % 360) - 180)
    roll = float(((roll + 180) % 360) - 180)
    pitch = float(pitch)

    event = None
    if pitch > HEAD_PITCH_DOWN_THRESHOLD:
        event = "looking_down"
    elif abs(yaw) > HEAD_YAW_THRESHOLD:
        event = "turned_away"
    elif abs(roll) > HEAD_TILT_THRESHOLD:
        event = "head_tilt"

    return {
        "yaw": round(yaw, 2),
        "pitch": round(pitch, 2),
        "roll": round(roll, 2),
        "event": event,
    }
