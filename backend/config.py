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


def _get_bool(name, default):
    val = os.environ.get(name)
    if val is None:
        return bool(default)
    return str(val).strip().lower() in ("1", "true", "yes", "on")


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


# ===========================================================================
# Authentication & account management
# ===========================================================================

# App environment: "development" or "production". Controls secure-cookie flags.
APP_ENV = os.environ.get("APP_ENV", "development").lower()
IS_PRODUCTION = APP_ENV == "production"

# Server-side secret used to sign the CSRF token (NOT the session id itself,
# which is a random opaque token stored in the DB). Must be set in production.
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-insecure-secret-change-me")

# Public URLs. Email links and redirects use FRONTEND_URL; never hard-code
# localhost in templates.
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173").rstrip("/")
BACKEND_URL = os.environ.get("BACKEND_URL", "http://127.0.0.1:5000").rstrip("/")

# Explicit CORS allowlist (comma-separated). Credentials are only sent to these
# origins. Never use a wildcard with credentials.
CORS_ORIGINS = [
    o.strip() for o in os.environ.get(
        "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",") if o.strip()
]

# ---- Session cookie ----
SESSION_COOKIE_NAME = os.environ.get("SESSION_COOKIE_NAME", "aceit_session")
CSRF_COOKIE_NAME = os.environ.get("CSRF_COOKIE_NAME", "aceit_csrf")
# Lifetime of a login session (days). "Remember me" uses the full lifetime;
# a non-remembered login uses a shorter window.
SESSION_LIFETIME_DAYS = _get_int("SESSION_LIFETIME_DAYS", 30)
SESSION_SHORT_HOURS = _get_int("SESSION_SHORT_HOURS", 12)
# SameSite policy: "Lax" for same-site, "None" required for cross-site cookies
# over HTTPS. Default Lax in dev (localhost is treated as secure by browsers).
COOKIE_SAMESITE = os.environ.get("COOKIE_SAMESITE", "Lax")
# Secure flag: forced on in production; configurable in dev.
COOKIE_SECURE = _get_bool("COOKIE_SECURE", IS_PRODUCTION)
# Optional cookie domain (leave empty for host-only cookies).
COOKIE_DOMAIN = os.environ.get("COOKIE_DOMAIN", "") or None

# ---- Password policy ----
PASSWORD_MIN_LENGTH = _get_int("PASSWORD_MIN_LENGTH", 12)

# ---- Token / OTP lifetimes ----
EMAIL_VERIFY_TOKEN_HOURS = _get_int("EMAIL_VERIFY_TOKEN_HOURS", 24)
RESET_OTP_MINUTES = _get_int("RESET_OTP_MINUTES", 10)
RESET_OTP_MAX_ATTEMPTS = _get_int("RESET_OTP_MAX_ATTEMPTS", 5)
RESEND_COOLDOWN_SECONDS = _get_int("RESEND_COOLDOWN_SECONDS", 60)

# ---- Rate limits (max requests / window seconds) ----
RATE_LIMITS = {
    "login": (_get_int("RL_LOGIN_MAX", 10), _get_int("RL_LOGIN_WINDOW", 300)),
    "register": (_get_int("RL_REGISTER_MAX", 5), _get_int("RL_REGISTER_WINDOW", 3600)),
    "forgot": (_get_int("RL_FORGOT_MAX", 5), _get_int("RL_FORGOT_WINDOW", 3600)),
    "verify_reset": (_get_int("RL_VERIFY_RESET_MAX", 10), _get_int("RL_VERIFY_RESET_WINDOW", 900)),
    "resend": (_get_int("RL_RESEND_MAX", 5), _get_int("RL_RESEND_WINDOW", 3600)),
}

# ---- Max request body size (bytes) for non-upload JSON endpoints ----
MAX_JSON_BODY_BYTES = _get_int("MAX_JSON_BODY_BYTES", 64 * 1024)

# ===========================================================================
# SMTP email (Nodemailer-equivalent for the Python/Flask backend)
# ===========================================================================
# When SMTP is not configured, the email service falls back to logging the
# message to the console (dev mode) so the app still runs, and it NEVER reports
# a send as successful when it was not actually delivered.
SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = _get_int("SMTP_PORT", 587)
SMTP_SECURE = _get_bool("SMTP_SECURE", False)  # True = implicit TLS (port 465)
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")
SMTP_TIMEOUT = _get_int("SMTP_TIMEOUT", 15)
MAIL_FROM_NAME = os.environ.get("MAIL_FROM_NAME", "AceIt")
MAIL_FROM_ADDRESS = os.environ.get("MAIL_FROM_ADDRESS", "no-reply@aceit.local")
# Force the console-only transport (used by tests and local dev without SMTP).
MAIL_CONSOLE_FALLBACK = _get_bool("MAIL_CONSOLE_FALLBACK", True)


def smtp_configured():
    """True only when enough SMTP settings exist to attempt a real send."""
    return bool(SMTP_HOST and SMTP_PORT and MAIL_FROM_ADDRESS)
