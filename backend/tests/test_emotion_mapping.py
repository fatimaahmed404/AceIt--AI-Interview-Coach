"""Unit tests for the emotion mapping layer (no model load required)."""
from ml.visual import emotion_analysis as ea


def test_all_fer_classes_mapped():
    for cls in ea.FER_CLASSES:
        assert cls in ea.RAW_TO_INTERVIEW


def test_mapped_values_are_valid_categories():
    for mapped in ea.RAW_TO_INTERVIEW.values():
        assert mapped in ea.INTERVIEW_CATEGORIES


def test_specific_mappings():
    assert ea.RAW_TO_INTERVIEW["happy"] == "confident"
    assert ea.RAW_TO_INTERVIEW["neutral"] == "neutral"
    assert ea.RAW_TO_INTERVIEW["fear"] == "nervous"
    assert ea.RAW_TO_INTERVIEW["angry"] == "nervous"


def test_model_info_declares_pretrained():
    info = ea.model_info()
    assert info["pretrained"] is True
    assert info["trained_from_scratch"] is False
    assert info["raw_classes"] == ea.FER_CLASSES
