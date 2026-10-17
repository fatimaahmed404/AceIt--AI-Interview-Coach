"""
Authentication routes (Flask blueprint, mounted at /api/auth and /api/user).

Security posture:
  * Passwords hashed with Argon2id; only hashes stored.
  * Server-side sessions via HttpOnly cookie + double-submit CSRF.
  * Generic responses to avoid account enumeration (register/login/forgot).
  * Rate limiting on register/login/forgot/verify-reset/resend.
  * Verification tokens and reset OTPs stored as hashes with expiry + single use.
  * Password reset / change revokes other sessions and emails a notification.
  * Email delivery failures are surfaced, never reported as success.
"""
import logging
from datetime import timedelta

from flask import Blueprint, request, jsonify, g, make_response

import config
from utils import mailer
from utils.email_service import EmailDeliveryError
from . import models
from .models import (
    normalize_email, public_user, STATUS_ACTIVE,
    PURPOSE_VERIFY, PURPOSE_RESET,
)
from .security import (
    hash_password, verify_password, needs_rehash,
    generate_token, hash_token, generate_otp, constant_time_equals,
)
from .validators import validate_registration, password_errors
from . import session as session_mod
from .middleware import (
    login_required, current_user, rate_limit, me_payload, get_db,
)

log = logging.getLogger("aceit.auth")

auth_bp = Blueprint("auth", __name__)

# Generic messages (anti-enumeration).
GENERIC_FORGOT = ("If an account exists for that email, a reset code has been sent.")
GENERIC_LOGIN_FAIL = "Invalid email or password."


def _db():
    return get_db()


def _issue_verification(db, user):
    """Create + email a fresh verification token. Returns delivery status."""
    raw = generate_token(32)
    expires = models.now() + timedelta(hours=config.EMAIL_VERIFY_TOKEN_HOURS)
    models.invalidate_tokens(db, user["_id"], PURPOSE_VERIFY)
    models.create_token(db, user["_id"], PURPOSE_VERIFY, hash_token(raw), expires)
    return mailer.send_verification(user["email"], user.get("full_name"), raw)


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------
@auth_bp.route("/register", methods=["POST"])
@rate_limit("register")
def register():
    data = request.get_json(silent=True) or {}
    cleaned, errors = validate_registration(data)
    if errors:
        return jsonify({"error": "Validation failed.", "fields": errors}), 400

    db = _db()
    existing = models.find_user_by_email(db, cleaned["email"])
    if existing:
        # Do not reveal that the email exists; return a generic 202-style result.
        # The user is told to check their email either way.
        return jsonify({
            "message": "Registration received. Please check your email to verify your account.",
        }), 202

    try:
        user = models.create_user(
            db, cleaned["full_name"], cleaned["email"], hash_password(cleaned["password"])
        )
    except Exception as exc:  # noqa: BLE001 - unique-index race -> treat as existing
        log.info("register insert rejected: %s", exc.__class__.__name__)
        return jsonify({
            "message": "Registration received. Please check your email to verify your account.",
        }), 202

    status = "console"
    try:
        status = _issue_verification(db, user)
    except EmailDeliveryError:
        log.error("Verification email failed to send for new user")
        # Account exists but email failed; tell the user to retry resend.
        return jsonify({
            "message": "Account created, but the verification email could not be sent. "
                       "Please use 'resend verification' shortly.",
            "email_delivery": "failed",
        }), 201

    return jsonify({
        "message": "Account created. Please check your email to verify your account.",
        "email_delivery": status,
    }), 201


# ---------------------------------------------------------------------------
# Verify email
# ---------------------------------------------------------------------------
@auth_bp.route("/verify-email", methods=["POST"])
def verify_email():
    data = request.get_json(silent=True) or {}
    token = (data.get("token") or "").strip()
    if not token:
        return jsonify({"error": "Verification token is required."}), 400

    db = _db()
    rec = models.find_token_by_hash(db, PURPOSE_VERIFY, hash_token(token))
    if not rec:
        return jsonify({"error": "Invalid or expired verification link."}), 400
    user = models.find_user_by_id(db, rec["user_id"])
    if not user:
        return jsonify({"error": "Invalid or expired verification link."}), 400

    # Already verified -> handle gracefully (idempotent).
    if user.get("email_verified"):
        models.consume_token(db, rec["_id"])
        return jsonify({"message": "Email already verified. You can log in."}), 200

    if rec.get("consumed") or models.is_expired(rec.get("expires_at")):
        return jsonify({"error": "This verification link has expired or already been used."}), 400

    # Mark verified, consume token, activate account.
    models.consume_token(db, rec["_id"])
    models.set_user_fields(db, user["_id"], {
        "email_verified": True,
        "status": STATUS_ACTIVE,
    })

    # Send welcome email once (don't block verification on email failure).
    if not user.get("welcome_sent"):
        try:
            mailer.send_welcome(user["email"], user.get("full_name"))
            models.set_user_fields(db, user["_id"], {"welcome_sent": True})
        except EmailDeliveryError:
            log.warning("Welcome email failed to send (non-fatal)")

    return jsonify({"message": "Email verified successfully. You can now log in."}), 200


@auth_bp.route("/resend-verification", methods=["POST"])
@rate_limit("resend", identifier="email")
def resend_verification():
    data = request.get_json(silent=True) or {}
    email = normalize_email(data.get("email"))
    db = _db()
    user = models.find_user_by_email(db, email)
    generic = jsonify({"message": "If that account exists and is unverified, a new link has been sent."})
    if not user or user.get("email_verified"):
        return generic, 200

    # Resend cooldown based on the last verification token's creation time.
    last = models.find_active_token(db, user["_id"], PURPOSE_VERIFY)
    if last and (models.now() - models._aware(last["created_at"])).total_seconds() < config.RESEND_COOLDOWN_SECONDS:
        return jsonify({"error": "Please wait before requesting another email."}), 429

    try:
        _issue_verification(db, user)
    except EmailDeliveryError:
        return jsonify({"error": "Could not send verification email. Try again later."}), 502
    return generic, 200


# ---------------------------------------------------------------------------
# Login / logout / me
# ---------------------------------------------------------------------------
@auth_bp.route("/login", methods=["POST"])
@rate_limit("login", identifier="email")
def login():
    data = request.get_json(silent=True) or {}
    email = normalize_email(data.get("email"))
    password = data.get("password") or ""
    remember = bool(data.get("remember"))

    db = _db()
    user = models.find_user_by_email(db, email)
    # Always run a hash verification to reduce timing differences.
    stored = user.get("password_hash") if user else "$argon2id$v=19$m=65536,t=3,p=2$" + "A" * 22
    ok = verify_password(stored, password) if user else (verify_password(stored, password) or False)

    if not user or not ok:
        return jsonify({"error": GENERIC_LOGIN_FAIL}), 401

    if user.get("status") == models.STATUS_DISABLED:
        return jsonify({"error": "This account has been disabled."}), 403

    if not user.get("email_verified"):
        return jsonify({
            "error": "Please verify your email before logging in.",
            "needs_verification": True,
        }), 403

    # Opportunistic rehash if parameters changed.
    if needs_rehash(user["password_hash"]):
        models.set_user_fields(db, user["_id"], {"password_hash": hash_password(password)})

    models.set_user_fields(db, user["_id"], {"last_login_at": models.now()})

    resp = make_response(jsonify(me_payload(user)))
    session_mod.start_session(
        db, resp, user["_id"], remember=remember,
        user_agent=request.headers.get("User-Agent", ""),
    )
    return resp, 200


@auth_bp.route("/logout", methods=["POST"])
def logout():
    db = _db()
    # CSRF check for the logout POST if a session exists.
    if current_user() and not session_mod.csrf_ok(request):
        return jsonify({"error": "Invalid or missing CSRF token."}), 403
    session_hash = getattr(g, "session_hash", None)
    if session_hash:
        models.delete_session(db, session_hash)
    resp = make_response(jsonify({"message": "Logged out."}))
    session_mod.clear_session_cookies(resp)
    return resp, 200


@auth_bp.route("/logout-all", methods=["POST"])
@login_required
def logout_all():
    db = _db()
    user = current_user()
    models.delete_all_sessions(db, user["_id"])
    resp = make_response(jsonify({"message": "Signed out of all sessions."}))
    session_mod.clear_session_cookies(resp)
    return resp, 200


@auth_bp.route("/me", methods=["GET"])
def me():
    user = current_user()
    if not user:
        return jsonify({"user": None}), 200
    return jsonify(me_payload(user)), 200


# ---------------------------------------------------------------------------
# Forgot password (OTP flow)
# ---------------------------------------------------------------------------
@auth_bp.route("/forgot-password", methods=["POST"])
@rate_limit("forgot", identifier="email")
def forgot_password():
    data = request.get_json(silent=True) or {}
    email = normalize_email(data.get("email"))
    db = _db()
    user = models.find_user_by_email(db, email)

    # Generic response regardless of whether the account exists.
    if user:
        otp = generate_otp(6)
        expires = models.now() + timedelta(minutes=config.RESET_OTP_MINUTES)
        models.invalidate_tokens(db, user["_id"], PURPOSE_RESET)
        models.create_token(db, user["_id"], PURPOSE_RESET, hash_token(otp), expires)
        try:
            mailer.send_password_reset(user["email"], user.get("full_name"), otp)
        except EmailDeliveryError:
            log.error("Password reset email failed to send")
            # Still return generic to avoid enumeration; user can retry.
    return jsonify({"message": GENERIC_FORGOT}), 200


@auth_bp.route("/verify-reset-code", methods=["POST"])
@rate_limit("verify_reset", identifier="email")
def verify_reset_code():
    data = request.get_json(silent=True) or {}
    email = normalize_email(data.get("email"))
    code = (data.get("code") or "").strip()
    db = _db()
    user = models.find_user_by_email(db, email)
    if not user or not code:
        return jsonify({"error": "Invalid or expired code."}), 400

    rec = models.find_active_token(db, user["_id"], PURPOSE_RESET)
    if not rec:
        return jsonify({"error": "Invalid or expired code."}), 400

    attempts = models.increment_token_attempts(db, rec["_id"])
    if attempts > config.RESET_OTP_MAX_ATTEMPTS:
        models.consume_token(db, rec["_id"])
        return jsonify({"error": "Too many incorrect attempts. Request a new code."}), 429

    if not constant_time_equals(rec["token_hash"], hash_token(code)):
        return jsonify({"error": "Invalid or expired code."}), 400

    # Code is valid: issue a short-lived single-use reset ticket so the client
    # can set a new password without resending the OTP.
    ticket = generate_token(24)
    models.set_user_fields(db, user["_id"], {})  # touch updated_at
    db.auth_tokens.update_one(
        {"_id": rec["_id"]},
        {"$set": {"reset_ticket_hash": hash_token(ticket), "verified": True}},
    )
    return jsonify({"message": "Code verified.", "reset_ticket": ticket}), 200


@auth_bp.route("/reset-password", methods=["POST"])
@rate_limit("verify_reset", identifier="email")
def reset_password():
    data = request.get_json(silent=True) or {}
    email = normalize_email(data.get("email"))
    ticket = (data.get("reset_ticket") or "").strip()
    new_password = data.get("new_password") or ""
    confirm = data.get("confirm_password")

    if confirm is not None and confirm != new_password:
        return jsonify({"error": "Passwords do not match."}), 400
    pw_err = password_errors(new_password)
    if pw_err:
        return jsonify({"error": pw_err}), 400

    db = _db()
    user = models.find_user_by_email(db, email)
    if not user or not ticket:
        return jsonify({"error": "Invalid or expired reset request."}), 400

    rec = models.find_active_token(db, user["_id"], PURPOSE_RESET)
    if (not rec or not rec.get("verified")
            or not rec.get("reset_ticket_hash")
            or not constant_time_equals(rec["reset_ticket_hash"], hash_token(ticket))):
        return jsonify({"error": "Invalid or expired reset request."}), 400

    # Update password, consume token, revoke all sessions, notify by email.
    models.set_user_fields(db, user["_id"], {"password_hash": hash_password(new_password)})
    models.consume_token(db, rec["_id"])
    models.invalidate_tokens(db, user["_id"], PURPOSE_RESET)
    models.delete_all_sessions(db, user["_id"])

    try:
        mailer.send_password_changed(user["email"], user.get("full_name"))
    except EmailDeliveryError:
        log.warning("Password-changed email failed (non-fatal)")

    # Do NOT auto-login; user returns to the login page with the new password.
    return jsonify({"message": "Password updated. Please log in with your new password."}), 200


# ---------------------------------------------------------------------------
# Change password (authenticated)
# ---------------------------------------------------------------------------
@auth_bp.route("/change-password", methods=["POST"])
@login_required
def change_password():
    data = request.get_json(silent=True) or {}
    current = data.get("current_password") or ""
    new_password = data.get("new_password") or ""
    confirm = data.get("confirm_password")

    db = _db()
    user = current_user()
    if not verify_password(user["password_hash"], current):
        return jsonify({"error": "Current password is incorrect."}), 400
    if confirm is not None and confirm != new_password:
        return jsonify({"error": "Passwords do not match."}), 400
    pw_err = password_errors(new_password)
    if pw_err:
        return jsonify({"error": pw_err}), 400
    if verify_password(user["password_hash"], new_password):
        return jsonify({"error": "New password must be different from the current one."}), 400

    models.set_user_fields(db, user["_id"], {"password_hash": hash_password(new_password)})
    # Revoke other sessions, keep the current one active.
    models.delete_all_sessions(db, user["_id"], except_hash=getattr(g, "session_hash", None))

    try:
        mailer.send_password_changed(user["email"], user.get("full_name"))
    except EmailDeliveryError:
        log.warning("Password-changed email failed (non-fatal)")

    return jsonify({"message": "Password changed successfully."}), 200
