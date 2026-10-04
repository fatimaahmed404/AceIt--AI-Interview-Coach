"""Unit tests for temporal aggregation (pure python)."""
from ml.visual import aggregation


def _frame(ts, face=True, emotion="neutral", eye_state="looking_at_camera",
           head_event=None, posture_state="good_posture"):
    return {
        "timestamp": ts,
        "face_detected": face,
        "multiple_faces": False,
        "emotion": {"emotion": emotion, "raw_emotion": emotion, "confidence": 0.8,
                    "distribution": {"confident": 25, "nervous": 25, "confused": 25, "neutral": 25}} if face else None,
        "eye": {"state": eye_state, "h_offset": 0.1, "v_offset": 0.1} if face else None,
        "head": {"yaw": 1.0, "pitch": 1.0, "roll": 1.0, "event": head_event} if face else None,
        "posture": {"state": posture_state, "shoulder_symmetry": 0.05, "head_drop": 0.8},
    }


def test_eye_contact_percentage():
    frames = [_frame(i * 0.2, eye_state="looking_at_camera") for i in range(8)]
    frames += [_frame(i * 0.2, eye_state="looking_left") for i in range(2)]
    agg = aggregation.aggregate(frames)
    assert agg["eye_contact"]["available"]
    assert agg["eye_contact"]["percentage"] == 80.0


def test_face_not_detected_does_not_count_against_eye_contact():
    frames = [_frame(i, eye_state="looking_at_camera") for i in range(5)]
    frames += [_frame(i, face=False) for i in range(5)]  # no face -> excluded
    agg = aggregation.aggregate(frames)
    # Only 5 valid face frames, all looking at camera -> 100%.
    assert agg["eye_contact"]["valid_frames"] == 5
    assert agg["eye_contact"]["percentage"] == 100.0


def test_dominant_emotion():
    frames = [_frame(i, emotion="confident") for i in range(7)]
    frames += [_frame(i, emotion="nervous") for i in range(3)]
    agg = aggregation.aggregate(frames)
    assert agg["facial_expression"]["dominant"] == "confident"
    assert agg["facial_expression"]["nervous_expression_frequency"] == 30.0


def test_posture_framing_aware():
    frames = [_frame(i, posture_state="good_posture") for i in range(5)]
    frames += [_frame(i, posture_state="body_not_detected") for i in range(5)]
    agg = aggregation.aggregate(frames)
    # 5 detected posture frames, all good -> 100%, the not-detected are excluded.
    assert agg["posture"]["valid_frames"] == 5
    assert agg["posture"]["good_posture_percentage"] == 100.0


def test_timeline_collapses_consecutive_events():
    frames = [_frame(i * 0.2, eye_state="looking_left") for i in range(5)]
    agg = aggregation.aggregate(frames)
    looking_left = [t for t in agg["timeline"] if t["event"] == "looking_left"]
    # Consecutive identical events collapse into fewer entries than frames.
    assert len(looking_left) < 5


def test_empty_frames_no_crash():
    agg = aggregation.aggregate([])
    assert agg["frames_analyzed"] == 0
    assert agg["eye_contact"]["available"] is False
    assert agg["facial_expression"]["available"] is False
