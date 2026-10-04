"""
Eye-contact / gaze-direction estimation from Face Mesh iris landmarks.

Approach (camera-relative gaze):
For each eye we take the iris centre (mean of the 4 iris landmarks) and
express it relative to the eye corners (horizontal) and eyelids (vertical).
A value near 0.5 on both axes means the iris sits in the middle of the eye,
i.e. the candidate is looking roughly toward the camera. Offsets beyond the
configured thresholds are classified as looking left/right/up/down.

This is a geometric interpretation on top of the deep-learning landmark
model (MediaPipe Face Mesh with iris refinement), as specified by the
project proposal (468 keypoints + gaze vectors relative to the webcam plane).
"""
import numpy as np

from config import GAZE_H_THRESHOLD, GAZE_V_THRESHOLD
from .face_analysis import LEFT_IRIS, RIGHT_IRIS, LEFT_EYE, RIGHT_EYE

STATE_CAMERA = "looking_at_camera"
STATE_LEFT = "looking_left"
STATE_RIGHT = "looking_right"
STATE_UP = "looking_up"
STATE_DOWN = "looking_down"
STATE_NO_FACE = "face_not_detected"


def _iris_ratio(landmarks, iris_idx, eye):
    """Return (h_ratio, v_ratio) of iris centre within the eye box, 0..1."""
    iris = landmarks[iris_idx].mean(axis=0)
    left = landmarks[eye["left"]]
    right = landmarks[eye["right"]]
    top = landmarks[eye["top"]]
    bottom = landmarks[eye["bottom"]]

    eye_w = np.linalg.norm(right - left)
    eye_h = np.linalg.norm(bottom - top)
    if eye_w < 1e-3 or eye_h < 1e-3:
        return None

    # Horizontal: project iris onto the (left->right) axis.
    h = np.dot(iris - left, (right - left)) / (eye_w ** 2)
    # Vertical: project iris onto the (top->bottom) axis.
    v = np.dot(iris - top, (bottom - top)) / (eye_h ** 2)
    return float(h), float(v)


def estimate_eye_contact(landmarks):
    """
    Classify gaze from Face Mesh landmarks (np.ndarray (N,2)).

    Returns {"state": <STATE_*>, "h_offset": float, "v_offset": float}
    where offsets are absolute deviations from centre (0 = dead centre).
    Returns None if the required landmarks are not usable.
    """
    if landmarks is None or len(landmarks) < 478:
        return None

    ratios = []
    for iris_idx, eye in ((LEFT_IRIS, LEFT_EYE), (RIGHT_IRIS, RIGHT_EYE)):
        r = _iris_ratio(landmarks, iris_idx, eye)
        if r is not None:
            ratios.append(r)
    if not ratios:
        return None

    h = float(np.mean([r[0] for r in ratios]))
    v = float(np.mean([r[1] for r in ratios]))
    h_off = h - 0.5
    v_off = v - 0.5

    if abs(h_off) <= GAZE_H_THRESHOLD and abs(v_off) <= GAZE_V_THRESHOLD:
        state = STATE_CAMERA
    elif abs(h_off) >= abs(v_off):
        state = STATE_RIGHT if h_off > 0 else STATE_LEFT
    else:
        state = STATE_DOWN if v_off > 0 else STATE_UP

    return {
        "state": state,
        "h_offset": round(abs(h_off), 4),
        "v_offset": round(abs(v_off), 4),
    }
