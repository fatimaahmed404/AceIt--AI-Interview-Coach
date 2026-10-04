"""
Edge-case tests for the visual pipeline.

The deep-learning pipeline (MediaPipe/LiteRT) only runs in the dedicated
.venv-visual environment, so these tests are skipped unless the required
libraries are importable in the current interpreter.

Run them with:
    ../.venv-visual/bin/python -m pytest tests/test_pipeline_edge_cases.py
"""
import os
import tempfile

import pytest

mediapipe = pytest.importorskip("mediapipe")  # noqa: F841 - skip marker
pytest.importorskip("cv2")

from ml.visual.pipeline import analyze_video  # noqa: E402


def test_corrupted_video_returns_friendly_error():
    path = os.path.join(tempfile.gettempdir(), "aceit_corrupt.mp4")
    with open(path, "wb") as f:
        f.write(b"this is not a video file")
    try:
        result = analyze_video(path)
        assert result["ok"] is False
        assert isinstance(result["error"], str) and result["error"]
    finally:
        os.remove(path)


def test_missing_video_returns_error():
    result = analyze_video("/nonexistent/path/to/video.mp4")
    assert result["ok"] is False


def test_short_valid_video_runs():
    import numpy as np
    import cv2

    path = os.path.join(tempfile.gettempdir(), "aceit_short.mp4")
    vw = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"mp4v"), 25.0, (320, 240))
    for _ in range(10):  # ~0.4s
        vw.write(np.full((240, 320, 3), 200, np.uint8))
    vw.release()
    try:
        result = analyze_video(path)
        # No face in a blank frame -> ok True but visual sub-scores None.
        assert result["ok"] is True
        assert result["meta"]["frames_analyzed"] >= 1
    finally:
        os.remove(path)
