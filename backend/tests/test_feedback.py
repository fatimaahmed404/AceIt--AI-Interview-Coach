"""Unit tests for feedback generation (descriptive, non-psychological)."""
from ml.visual import feedback, scoring


def _agg(eye_pct=80, good_posture=80, dominant="neutral", nervous=10, down=5):
    return {
        "frames_analyzed": 50,
        "face_detected_frames": 50,
        "multiple_faces_detected": False,
        "eye_contact": {"available": True, "percentage": eye_pct},
        "posture": {"available": True, "good_posture_percentage": good_posture, "stability": 0.8},
        "facial_expression": {"available": True, "dominant": dominant,
                              "nervous_expression_frequency": nervous,
                              "distribution": {"confident": 40, "neutral": 40, "confused": 10, "nervous": 10}},
        "head_movement": {"available": True, "stability": 0.9, "looking_down_frequency": down},
    }


def test_feedback_covers_all_available_metrics():
    agg = _agg()
    scores = scoring.score_visual(agg)
    tips = feedback.generate_feedback(agg, scores)
    categories = {t["category"] for t in tips}
    assert {"Eye contact", "Posture", "Facial expression", "Head movement"} <= categories


def test_feedback_is_descriptive_not_psychological():
    agg = _agg(dominant="nervous", nervous=60)
    scores = scoring.score_visual(agg)
    tips = feedback.generate_feedback(agg, scores)
    joined = " ".join(t["message"].lower() for t in tips)
    # Must never make a direct psychological claim.
    assert "you are nervous" not in joined
    # Should reference the configured category framing instead.
    assert "nervous-expression category" in joined


def test_no_face_adds_recording_note():
    agg = {
        "frames_analyzed": 30, "face_detected_frames": 0, "multiple_faces_detected": False,
        "eye_contact": {"available": False}, "posture": {"available": False},
        "facial_expression": {"available": False}, "head_movement": {"available": False},
    }
    scores = scoring.score_visual(agg)
    tips = feedback.generate_feedback(agg, scores)
    assert any(t["category"] == "Recording" for t in tips)
