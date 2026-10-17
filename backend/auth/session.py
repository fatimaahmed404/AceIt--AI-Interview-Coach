"""
Session + CSRF cookie management.

A login creates a server-side session document (storing only a SHA-256 hash of
the opaque session id). The raw session id is sent to the browser in an
HttpOnly, SameSite cookie. A separate, non-HttpOnly CSRF cookie holds a token
the SPA echoes back in the X-CSRF-Token header (double-submit pattern) so
state-changing requests cannot be forged cross-site.

Nothing sensitive is ever placed in localStorage; the frontend never sees the
session id (HttpOnly) and only mirrors the CSRF token header.
"""
from datetime import timedelta

import config
from .security import generate_token, hash_token, constant_time_equals
from . import models


def _max_age(remember):
    if remember:
        return int(timedelta(days=config.SESSION_LIFETIME_DAYS).total_seconds())
    return int(timedelta(hours=config.SESSION_SHORT_HOURS).total_seconds())


def start_session(db, response, user_id, remember=False, user_agent=None):
    """Create a session, set the session + CSRF cookies on `response`."""
    raw_session = generate_token(32)
    csrf = generate_token(24)
    max_age = _max_age(remember)
    expires_at = models.now() + timedelta(seconds=max_age)

    models.create_session(
        db, user_id, hash_token(raw_session), expires_at, user_agent=user_agent
    )

    common = dict(
        max_age=max_age,
        secure=config.COOKIE_SECURE,
        samesite=config.COOKIE_SAMESITE,
        domain=config.COOKIE_DOMAIN,
        path="/",
    )
    # Session cookie: HttpOnly (JS cannot read it).
    response.set_cookie(config.SESSION_COOKIE_NAME, raw_session, httponly=True, **common)
    # CSRF cookie: readable by JS so the SPA can echo it in a header.
    response.set_cookie(config.CSRF_COOKIE_NAME, csrf, httponly=False, **common)
    return raw_session, csrf


def clear_session_cookies(response):
    for name in (config.SESSION_COOKIE_NAME, config.CSRF_COOKIE_NAME):
        response.set_cookie(
            name, "", max_age=0, expires=0, path="/",
            secure=config.COOKIE_SECURE, samesite=config.COOKIE_SAMESITE,
            domain=config.COOKIE_DOMAIN,
            httponly=(name == config.SESSION_COOKIE_NAME),
        )


def get_session_from_request(db, request):
    """Return (user_doc, session_hash) for a valid session cookie, else (None, None)."""
    raw = request.cookies.get(config.SESSION_COOKIE_NAME)
    if not raw:
        return None, None
    session_hash = hash_token(raw)
    sess = models.find_session(db, session_hash)
    if not sess:
        return None, None
    # TTL index removes expired sessions, but double-check in case of clock skew.
    if models.is_expired(sess.get("expires_at")):
        models.delete_session(db, session_hash)
        return None, None
    user = models.find_user_by_id(db, sess["user_id"])
    if not user:
        models.delete_session(db, session_hash)
        return None, None
    return user, session_hash


def csrf_ok(request):
    """Validate the double-submit CSRF token for state-changing requests."""
    cookie = request.cookies.get(config.CSRF_COOKIE_NAME, "")
    header = request.headers.get("X-CSRF-Token", "")
    if not cookie or not header:
        return False
    return constant_time_equals(cookie, header)
