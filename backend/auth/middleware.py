"""
Authentication/authorization middleware and helpers.

- `init_auth(app, db)` stores the db handle and registers a before-request hook
  that resolves the current user from the session cookie (if any) and enforces
  CSRF on state-changing requests to protected endpoints.
- `@login_required` guards an endpoint; returns 401 if not authenticated.
- `current_user()` returns the resolved user document (or None).
- `rate_limit(bucket, key_suffix)` applies a configured rate limit.

The backend verifies the session itself on every request; hiding frontend
pages is never treated as authorization.
"""
import functools

from flask import g, request, jsonify

import config
from . import session as session_mod
from . import ratelimit
from .models import public_user

_db = None

# Methods that change state and therefore require a valid CSRF token.
_UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def init_auth(app, db):
    global _db
    _db = db

    @app.before_request
    def _load_user():  # noqa: ANN001
        g.current_user = None
        g.session_hash = None
        if request.method == "OPTIONS":
            return
        user, session_hash = session_mod.get_session_from_request(db, request)
        if user:
            g.current_user = user
            g.session_hash = session_hash


def get_db():
    return _db


def current_user():
    return getattr(g, "current_user", None)


def current_user_id():
    u = current_user()
    return str(u["_id"]) if u else None


def _unauthorized(msg="Authentication required."):
    return jsonify({"error": msg}), 401


def _csrf_failed():
    return jsonify({"error": "Invalid or missing CSRF token."}), 403


def login_required(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user():
            return _unauthorized()
        # Enforce CSRF for state-changing authenticated requests.
        if request.method in _UNSAFE_METHODS and not session_mod.csrf_ok(request):
            return _csrf_failed()
        return fn(*args, **kwargs)
    return wrapper


def verified_required(fn):
    """Like login_required, but also requires a verified email."""
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        user = current_user()
        if not user:
            return _unauthorized()
        if request.method in _UNSAFE_METHODS and not session_mod.csrf_ok(request):
            return _csrf_failed()
        if not user.get("email_verified"):
            return jsonify({"error": "Email not verified."}), 403
        return fn(*args, **kwargs)
    return wrapper


def rate_limit(bucket, identifier=""):
    """
    Decorator applying a configured rate limit. The key combines the bucket,
    the client IP, and an optional identifier (e.g. normalised email) resolved
    at call time from the request body.
    """
    max_req, window = config.RATE_LIMITS.get(bucket, (30, 60))

    def deco(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            ip = request.headers.get("X-Forwarded-For", request.remote_addr or "unknown").split(",")[0].strip()
            extra = ""
            if identifier == "email":
                body = request.get_json(silent=True) or {}
                extra = (body.get("email") or "").strip().lower()
            key = f"{bucket}:{ip}:{extra}"
            allowed, retry_after = ratelimit.check(key, max_req, window)
            if not allowed:
                resp = jsonify({"error": "Too many requests. Please try again later."})
                resp.headers["Retry-After"] = str(retry_after)
                return resp, 429
            return fn(*args, **kwargs)
        return wrapper
    return deco


def me_payload(user):
    """The /auth/me and login response body for a user."""
    return {"user": public_user(user)}
