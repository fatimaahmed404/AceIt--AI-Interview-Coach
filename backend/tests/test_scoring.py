"""Unit tests for the centralised scoring module."""
from ml.visual import scoring


def test_eye_contact_score_scales_percentage():
    assert scoring.score_eye_contact({"available": True, "percentage": 78.0}) == 7.8
    assert scoring.score_eye_contact({"available": True, "percentage": 100.0}) == 10.0
    assert scoring.score_eye_contact({"available": True, "percentage": 0.0}) == 0.0


def test_eye_contact_unavailable_returns_none():
    assert scoring.score_eye_contact({"available": False}) is None


def test_posture_score_uses_percentage_and_stability():
    high = scoring.score_posture({"available": True, "good_posture_percentage": 90, "stability": 1.0})
    low = scoring.score_posture({"available": True, "good_posture_percentage": 20, "stability": 0.0})
    assert high > low
    assert 0 <= low <= 10 and 0 <= high <= 10


def test_expression_score_prefers_engaged():
    engaged = scoring.score_expression(
        {"available": True, "distribution": {"confident": 80, "neutral": 20, "confused": 0, "nervous": 0}})
    nervous = scoring.score_expression(
        {"available": True, "distribution": {"confident": 0, "neutral": 0, "confused": 20, "nervous": 80}})
    assert engaged > nervous


def test_head_movement_penalised_by_looking_down():
    stable = scoring.score_head_movement({"available": True, "stability": 1.0, "looking_down_frequency": 0})
    distracted = scoring.score_head_movement({"available": True, "stability": 1.0, "looking_down_frequency": 100})
    assert stable > distracted


def test_score_visual_combines_components():
    agg = {
        "eye_contact": {"available": True, "percentage": 80},
        "posture": {"available": True, "good_posture_percentage": 80, "stability": 0.8},
        "facial_expression": {"available": True,
                              "distribution": {"confident": 50, "neutral": 50, "confused": 0, "nervous": 0}},
        "head_movement": {"available": True, "stability": 0.9, "looking_down_frequency": 0},
    }
    result = scoring.score_visual(agg)
    assert result["score"] is not None
    assert set(result["components"]) == {"eye_contact", "posture", "facial_expression", "head_movement"}
    assert 0 <= result["score"] <= 10


def test_overall_renormalises_missing_modalities():
    # Only text present -> overall equals text score.
    assert scoring.score_overall(voice=None, text=8.0, visual=None) == 8.0
    # All present -> somewhere between the inputs.
    combined = scoring.score_overall(voice=6.0, text=8.0, visual=7.0)
    assert 6.0 <= combined <= 8.0


def test_overall_all_missing_returns_none():
    assert scoring.score_overall(None, None, None) is None
