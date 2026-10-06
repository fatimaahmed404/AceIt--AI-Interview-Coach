"""
Central configuration for AceIt.

All tunable constants live here so weights/thresholds are not hard-coded
across multiple files. Secrets (API keys, DB URI) are read from a .env file in
the backend directory (git-ignored) or from real environment variables.
Copy backend/.env.example to backend/.env and fill in your own values.
"""
import os


def _load_dotenv():
    """
    Minimal .env loader (no external dependency required).

    Reads KEY=VALUE lines from backend/.env and populates os.environ for any
    key that is not already set in the real environment. If python-dotenv is
    installed it is used instead for completeness.
    """
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if not os.path.exists(env_path):
        return
    try:
        from dotenv import load_dotenv  # type: ignore
        load_dotenv(env_path)
        return
    except Exception:
        pass
    try:
        with open(env_path, "r", encoding="utf-8") as fh:
            for raw in fh:
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key, value = key.strip(), value.strip().strip('"').strip("'")
                os.environ.setdefault(key, value)
    except OSError:
        pass


_load_dotenv()


def _get_float(name, default):
    try:
        return float(os.environ.get(name, default))
    except (TypeError, ValueError):
        return float(default)


def _get_int(name, default):
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return int(default)


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/interview_coach")
MONGO_DB = os.environ.get("MONGO_DB", "interview_coach")

# ---------------------------------------------------------------------------
# External API keys (read from backend/.env or the environment; never hard-coded).
# ---------------------------------------------------------------------------
ASSEMBLYAI_API_KEY = os.environ.get("ASSEMBLYAI_API_KEY", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-20b")

# ---------------------------------------------------------------------------
# Deep Learning / visual pipeline
# ---------------------------------------------------------------------------
# How many frames per second to analyse. The source video is usually 25-30 FPS;
# analysing every frame is wasteful, so we sample intelligently.
ANALYSIS_FPS = _get_float("ANALYSIS_FPS", 5.0)

# Hard cap on the number of frames analysed for a single video (safety valve for
# very long recordings so a request can never run unbounded).
MAX_FRAMES = _get_int("MAX_FRAMES", 900)

# Minimum face-detection confidence for MediaPipe modules.
FACE_MIN_CONFIDENCE = _get_float("FACE_MIN_CONFIDENCE", 0.5)
POSE_MIN_CONFIDENCE = _get_float("POSE_MIN_CONFIDENCE", 0.5)

# A frame is "looking at camera" when the estimated horizontal + vertical gaze
# offset stays within these normalised thresholds (0 = dead centre, 1 = edge).
GAZE_H_THRESHOLD = _get_float("GAZE_H_THRESHOLD", 0.22)
GAZE_V_THRESHOLD = _get_float("GAZE_V_THRESHOLD", 0.25)

# Head-pose angle thresholds (degrees) for flagging extreme positions.
HEAD_YAW_THRESHOLD = _get_float("HEAD_YAW_THRESHOLD", 30.0)
HEAD_PITCH_DOWN_THRESHOLD = _get_float("HEAD_PITCH_DOWN_THRESHOLD", 20.0)
HEAD_TILT_THRESHOLD = _get_float("HEAD_TILT_THRESHOLD", 25.0)

# Where temporary uploaded videos are written during processing.
TEMP_DIR = os.environ.get("ACEIT_TEMP_DIR", os.path.join(os.path.dirname(__file__), "temp_uploads"))

# Delete the uploaded video after analysis finishes (privacy-friendly default).
DELETE_VIDEO_AFTER_ANALYSIS = os.environ.get("DELETE_VIDEO_AFTER_ANALYSIS", "true").lower() == "true"


# ---------------------------------------------------------------------------
# Scoring weights (all configurable, documented in docs/deep-learning.md)
# ---------------------------------------------------------------------------
# Weights that combine the four visual sub-scores into one "visual" score /10.
VISUAL_WEIGHTS = {
    "eye_contact": _get_float("W_EYE_CONTACT", 0.30),
    "posture": _get_float("W_POSTURE", 0.25),
    "facial_expression": _get_float("W_EXPRESSION", 0.25),
    "head_movement": _get_float("W_HEAD", 0.20),
}

# Weights that combine the three modalities (voice/text/visual) into the overall
# score. These degrade gracefully: if a modality is missing it is dropped and the
# remaining weights are renormalised (see ml/visual/scoring.py).
OVERALL_WEIGHTS = {
    "voice": _get_float("W_VOICE", 0.30),
    "text": _get_float("W_TEXT", 0.35),
    "visual": _get_float("W_VISUAL", 0.35),
}
