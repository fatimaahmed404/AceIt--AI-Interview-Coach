"""Unit tests for eye-contact / gaze geometry (pure numpy, no model)."""
import numpy as np

from ml.visual import eye_contact as ec
from ml.visual.face_analysis import LEFT_IRIS, RIGHT_IRIS, LEFT_EYE, RIGHT_EYE


def _make_landmarks(iris_h=0.5, iris_v=0.5):
    """
    Build a synthetic 478-landmark array where both eyes have corners and
    lids at known positions and the iris sits at (iris_h, iris_v) within each
    eye box. Coordinates are in arbitrary pixel space.
    """
    pts = np.zeros((478, 2), dtype=np.float32)

    def place_eye(eye, iris_idx, cx):
        left = np.array([cx - 20, 100], dtype=np.float32)
        right = np.array([cx + 20, 100], dtype=np.float32)
        top = np.array([cx, 90], dtype=np.float32)
        bottom = np.array([cx, 110], dtype=np.float32)
        pts[eye["left"]] = left
        pts[eye["right"]] = right
        pts[eye["top"]] = top
        pts[eye["bottom"]] = bottom
        # Iris x comes from the horizontal fraction, iris y from the vertical
        # fraction. estimate_eye_contact projects onto each axis independently,
        # so place the iris at the matching x,y within the eye box.
        iris_x = left[0] + iris_h * (right[0] - left[0])
        iris_y = top[1] + iris_v * (bottom[1] - top[1])
        for idx in iris_idx:
            pts[idx] = np.array([iris_x, iris_y], dtype=np.float32)

    place_eye(LEFT_EYE, LEFT_IRIS, 200)
    place_eye(RIGHT_EYE, RIGHT_IRIS, 100)
    return pts


def test_centered_iris_is_looking_at_camera():
    lm = _make_landmarks(iris_h=0.5, iris_v=0.5)
    result = ec.estimate_eye_contact(lm)
    assert result is not None
    assert result["state"] == ec.STATE_CAMERA


def test_iris_far_right_not_camera():
    lm = _make_landmarks(iris_h=0.95, iris_v=0.5)
    result = ec.estimate_eye_contact(lm)
    assert result is not None
    assert result["state"] != ec.STATE_CAMERA


def test_too_few_landmarks_returns_none():
    assert ec.estimate_eye_contact(np.zeros((100, 2))) is None
    assert ec.estimate_eye_contact(None) is None
