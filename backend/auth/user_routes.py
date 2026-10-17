"""
User profile and account-settings routes (mounted at /api/user).

Data-retention policy for account deletion (documented here and in the README):
  When a user deletes their account we HARD-DELETE the account record and all
  personally-identifying auth data (sessions, tokens). The user's interview
  sessions (db.sessions) and mock sessions (db.mock_sessions) are ANONYMISED
  rather than deleted: their `user_id` is removed so no interview content
  remains linked to an identifiable person, but aggregate/analytics data is not
  orphaned in an inconsistent way. Any stored video files are already deleted
  immediately after analysis (DELETE_VIDEO_AFTER_ANALYSIS), so no recordings
  persist to clean up. This avoids leaving the account in an inconsistent state
  while respecting that the user asked to remove their identity from the system.
"""
import logging

from flask import Blueprint, request, jsonify

from . import models
from .models import public_user, valid_email
from .security import verify_password
from .middleware import login_required, current_user, get_db
from . import session as session_mod

log = logging.getLogger("aceit.user")

user_bp = Blueprint("user", __name__)


def _db():
    return get_db()


@user_bp.route("/profile", methods=["GET"])
@login_required
def get_profile():
    return jsonify({"user": public_user(current_user())}), 200


@user_bp.route("/profile", methods=["PATCH"])
@login_required
def update_profile():
    """
    Update mutable profile fields. Only `full_name` can be changed here.
    Email changes require a dedicated verification flow and are intentionally
    not allowed through this endpoint (prevents account takeover by email swap).
    """
    data = request.get_json(silent=True) or {}
    updates = {}

    if "full_name" in data:
        name = (data.get("full_name") or "").strip()
        if len(name) < 2:
            return jsonify({"error": "Please enter a valid full name."}), 400
        updates["full_name"] = name

    # Explicitly reject email changes via this endpoint (mass-assignment guard).
    if "email" in data and valid_email(data.get("email", "")):
        return jsonify({
            "error": "Changing your email requires verification and is not supported here.",
        }), 400

    if not updates:
        return jsonify({"error": "No valid fields to update."}), 400

    db = _db()
    user = current_user()
    models.set_user_fields(db, user["_id"], updates)
    fresh = models.find_user_by_id(db, user["_id"])
    return jsonify({"user": public_user(fresh)}), 200


@user_bp.route("/sessions", methods=["GET"])
@login_required
def list_sessions():
    """List the user's active sessions (for a 'where you're signed in' view)."""
    from flask import g
    db = _db()
    user = current_user()
    out = []
    for s in models.list_sessions(db, user["_id"]):
        out.append({
            "id": str(s["_id"]),
            "created_at": s.get("created_at").isoformat() if s.get("created_at") else None,
            "last_seen_at": s.get("last_seen_at").isoformat() if s.get("last_seen_at") else None,
            "user_agent": s.get("user_agent", ""),
            "current": s.get("session_hash") == getattr(g, "session_hash", None),
        })
    return jsonify({"sessions": out}), 200


@user_bp.route("/account", methods=["DELETE"])
@login_required
def delete_account():
    """
    Delete the account. Requires recent authentication by re-supplying the
    current password. Anonymises interview data per the retention policy above.
    """
    data = request.get_json(silent=True) or {}
    password = data.get("password") or ""
    db = _db()
    user = current_user()

    # Require reauthentication for this destructive action.
    if not verify_password(user["password_hash"], password):
        return jsonify({"error": "Password is incorrect."}), 400

    uid = str(user["_id"])

    # 1) Anonymise interview + mock sessions (unlink from the identity).
    db.sessions.update_many({"user_id": uid}, {"$set": {"user_id": None, "anonymized": True}})
    db.mock_sessions.update_many({"user_id": uid}, {"$set": {"user_id": None, "anonymized": True}})

    # 2) Remove all auth data (sessions + tokens).
    models.delete_all_sessions(db, uid)
    db.auth_tokens.delete_many({"user_id": uid})

    # 3) Delete the user record.
    db.users.delete_one({"_id": user["_id"]})

    resp = jsonify({"message": "Your account has been deleted."})
    session_mod.clear_session_cookies(resp)
    return resp, 200
