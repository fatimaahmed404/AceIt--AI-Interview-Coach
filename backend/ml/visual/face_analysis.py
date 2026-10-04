"""
Face detection and landmark extraction using MediaPipe Face Mesh.

MediaPipe Face Mesh is a deep-learning model that regresses 468 (or 478 with
`refine_landmarks=True`, which adds 10 iris landmarks) 3D facial keypoints
from a single image. We use it as the shared front-end for:
    - emotion CNN (we crop the face bounding box from the landmarks)
    - eye-contact / gaze estimation (eye + iris landmarks)
    - head-pose estimation (a stable subset of landmarks + solvePnP)

This module only *produces* landmarks and a face crop. The interpretation
lives in eye_contact.py, gaze.py and emotion_analysis.py so each concern is
isolated.
"""
import logging

import numpy as np

from config import FACE_MIN_CONFIDENCE

log = logging.getLogger("aceit.face")

# Landmark indices (MediaPipe Face Mesh canonical topology).
# Iris landmarks require refine_landmarks=True.
LEFT_IRIS = [474, 475, 476, 477]
RIGHT_IRIS = [469, 470, 471, 472]
# Eye corners / lids used to build a local eye box.
LEFT_EYE = {"left": 263, "right": 362, "top": 386, "bottom": 374}
RIGHT_EYE = {"left": 133, "right": 33, "top": 159, "bottom": 145}
# Subset used for head-pose solvePnP (nose tip, chin, eye corners, mouth corners).
POSE_LANDMARKS = {
    "nose_tip": 1,
    "chin": 152,
    "left_eye_corner": 263,
    "right_eye_corner": 33,
    "left_mouth": 291,
    "right_mouth": 61,
}


class FaceMesh:
    """Lazy wrapper over mediapipe.solutions.face_mesh."""

    def __init__(self):
        self._mesh = None
        self._load_error = None

    def _ensure(self):
        if self._mesh is not None or self._load_error is not None:
            return
        try:
            import mediapipe as mp

            self._mesh = mp.solutions.face_mesh.FaceMesh(
                static_image_mode=True,
                max_num_faces=2,
                refine_landmarks=True,
                min_detection_confidence=FACE_MIN_CONFIDENCE,
            )
            log.info("MediaPipe Face Mesh initialised")
        except Exception as exc:  # noqa: BLE001
            self._load_error = str(exc)
            log.warning("Face Mesh unavailable: %s", exc)

    @property
    def available(self):
        self._ensure()
        return self._mesh is not None

    def process(self, frame_bgr):
        """
        Run Face Mesh on one BGR frame.

        Returns a dict:
            {"face_detected": bool,
             "multiple_faces": bool,
             "landmarks": np.ndarray (N, 2) pixel coords of primary face or None,
             "face_crop": BGR np.ndarray or None,
             "frame_size": (w, h)}
        """
        self._ensure()
        h, w = frame_bgr.shape[:2]
        result = {
            "face_detected": False,
            "multiple_faces": False,
            "landmarks": None,
            "face_crop": None,
            "frame_size": (w, h),
        }
        if self._mesh is None:
            return result
        try:
            import cv2

            rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            out = self._mesh.process(rgb)
        except Exception as exc:  # noqa: BLE001 - isolate per-frame failures
            log.debug("Face Mesh failed on a frame: %s", exc)
            return result

        if not out.multi_face_landmarks:
            return result

        result["face_detected"] = True
        result["multiple_faces"] = len(out.multi_face_landmarks) > 1

        # Primary face = the first (MediaPipe returns the most prominent first).
        lm = out.multi_face_landmarks[0].landmark
        pts = np.array([[p.x * w, p.y * h] for p in lm], dtype=np.float32)
        result["landmarks"] = pts

        # Build a padded face crop for the emotion CNN.
        xs, ys = pts[:, 0], pts[:, 1]
        x1, y1 = int(max(0, xs.min())), int(max(0, ys.min()))
        x2, y2 = int(min(w, xs.max())), int(min(h, ys.max()))
        pad_x = int((x2 - x1) * 0.1)
        pad_y = int((y2 - y1) * 0.1)
        x1, y1 = max(0, x1 - pad_x), max(0, y1 - pad_y)
        x2, y2 = min(w, x2 + pad_x), min(h, y2 + pad_y)
        if x2 > x1 and y2 > y1:
            result["face_crop"] = frame_bgr[y1:y2, x1:x2].copy()
        return result

    def close(self):
        if self._mesh is not None:
            try:
                self._mesh.close()
            except Exception:  # noqa: BLE001
                pass
            self._mesh = None


def model_info():
    return {
        "name": "MediaPipe Face Mesh",
        "library": "mediapipe",
        "type": "Deep-learning facial landmark regression",
        "pretrained": True,
        "trained_from_scratch": False,
        "input": "RGB image frame",
        "output": "468 face landmarks + 10 iris landmarks (refine_landmarks=True)",
        "used_for": ["face detection", "eye contact / gaze", "head pose", "emotion face crop"],
    }
