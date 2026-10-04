"""
Posture / body analysis using MediaPipe Pose.

MediaPipe Pose is a deep-learning model (BlazePose) that regresses 33 body
landmarks. We use the upper-body subset (shoulders, ears, nose) to assess:

    - shoulder symmetry  (are the shoulders roughly level?)
    - neck/head forward  (is the head dropping toward the chest -> slouch?)
    - torso alignment    (vertical offset of head above the shoulder line)

Framing-aware: if the required upper-body landmarks are not visible (low
visibility score) we return "body_not_detected" and do NOT penalise the
candidate. Only confidently-detected frames contribute to the posture score.
"""
import logging

import numpy as np

from config import POSE_MIN_CONFIDENCE

log = logging.getLogger("aceit.posture")

STATE_GOOD = "good_posture"
STATE_SLIGHT = "slightly_slouched"
STATE_SLOUCHED = "slouched"
STATE_UNSTABLE = "unstable"
STATE_NO_BODY = "body_not_detected"

# BlazePose landmark indices.
L_SHOULDER, R_SHOULDER = 11, 12
L_EAR, R_EAR = 7, 8
NOSE = 0
_VIS_THRESHOLD = 0.5


class PostureAnalyzer:
    """Lazy wrapper over mediapipe.solutions.pose."""

    def __init__(self):
        self._pose = None
        self._load_error = None

    def _ensure(self):
        if self._pose is not None or self._load_error is not None:
            return
        try:
            import mediapipe as mp

            self._pose = mp.solutions.pose.Pose(
                static_image_mode=True,
                model_complexity=1,
                min_detection_confidence=POSE_MIN_CONFIDENCE,
            )
            log.info("MediaPipe Pose initialised")
        except Exception as exc:  # noqa: BLE001
            self._load_error = str(exc)
            log.warning("MediaPipe Pose unavailable: %s", exc)

    @property
    def available(self):
        self._ensure()
        return self._pose is not None

    def process(self, frame_bgr):
        """
        Return {"state", "shoulder_symmetry", "head_drop"} or
        {"state": STATE_NO_BODY} when upper body is not reliably visible.
        """
        self._ensure()
        if self._pose is None:
            return {"state": STATE_NO_BODY}
        try:
            import cv2

            rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            out = self._pose.process(rgb)
        except Exception as exc:  # noqa: BLE001 - isolate per-frame failures
            log.debug("Pose failed on a frame: %s", exc)
            return {"state": STATE_NO_BODY}

        if not out.pose_landmarks:
            return {"state": STATE_NO_BODY}

        lm = out.pose_landmarks.landmark
        ls, rs = lm[L_SHOULDER], lm[R_SHOULDER]
        # Require both shoulders to be visible, else framing excludes the body.
        if ls.visibility < _VIS_THRESHOLD or rs.visibility < _VIS_THRESHOLD:
            return {"state": STATE_NO_BODY}

        shoulder_width = abs(ls.x - rs.x) + 1e-6
        # Shoulder symmetry: vertical difference normalised by shoulder width.
        symmetry = abs(ls.y - rs.y) / shoulder_width
        shoulder_mid_y = (ls.y + rs.y) / 2.0

        # Head position: use ears/nose whichever is visible.
        head_y = None
        if lm[L_EAR].visibility > _VIS_THRESHOLD and lm[R_EAR].visibility > _VIS_THRESHOLD:
            head_y = (lm[L_EAR].y + lm[R_EAR].y) / 2.0
        elif lm[NOSE].visibility > _VIS_THRESHOLD:
            head_y = lm[NOSE].y

        # head_drop: how close the head is to the shoulder line (normalised).
        # Larger value = head higher above shoulders = more upright.
        head_drop = None
        if head_y is not None:
            head_drop = (shoulder_mid_y - head_y) / shoulder_width

        state = STATE_GOOD
        if head_drop is not None:
            if head_drop < 0.35:
                state = STATE_SLOUCHED
            elif head_drop < 0.6:
                state = STATE_SLIGHT
        if symmetry > 0.18:
            # Markedly uneven shoulders -> treat as (at least) slight slouch.
            state = STATE_SLOUCHED if state == STATE_SLOUCHED else STATE_SLIGHT

        return {
            "state": state,
            "shoulder_symmetry": round(float(symmetry), 4),
            "head_drop": round(float(head_drop), 4) if head_drop is not None else None,
        }

    def close(self):
        if self._pose is not None:
            try:
                self._pose.close()
            except Exception:  # noqa: BLE001
                pass
            self._pose = None


def model_info():
    return {
        "name": "MediaPipe Pose (BlazePose)",
        "library": "mediapipe",
        "type": "Deep-learning body-landmark regression",
        "pretrained": True,
        "trained_from_scratch": False,
        "input": "RGB image frame",
        "output": "33 body landmarks with visibility scores",
        "used_for": ["posture / slouch detection", "shoulder symmetry", "body stability"],
    }
