"""
Data-access layer for authentication.

Collections (MongoDB, same database as the rest of AceIt):
  users            - one document per account
  auth_sessions    - server-side sessions (one per login); enables revocation
  auth_tokens      - email-verification tokens and password-reset OTPs

Design notes:
  * A unique index on the normalised email enforces one-account-per-email at
    the database level.
  * Only HASHES of session ids / verification tokens / reset codes are stored.
  * Sessions and reset tokens carry an `expires_at`; a TTL index on
    auth_sessions lets Mongo expire stale sessions automatically.
  * The public user view never includes the password hash or token hashes.
"""
import re
from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Account status values.
STATUS_PENDING = "pending_verification"
STATUS_ACTIVE = "active"
STATUS_DISABLED = "disabled"

# Token purposes.
PURPOSE_VERIFY = "email_verify"
PURPOSE_RESET = "password_reset"


def now():
    return datetime.now(timezone.utc)


def _aware(dt):
    """
    MongoDB returns naive datetimes (UTC) by default. Normalise any datetime to
    timezone-aware UTC so comparisons with now() never raise.
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def is_expired(dt):
    """True if the (possibly naive) datetime is in the past."""
    dt = _aware(dt)
    return dt is not None and dt < now()


def normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def valid_email(email: str) -> bool:
    return bool(EMAIL_RE.match(email or ""))


def ensure_indexes(db):
    """Create indexes idempotently. Safe to call on every startup."""
    db.users.create_index("email", unique=True)
    db.auth_sessions.create_index("session_hash", unique=True)
    db.auth_sessions.create_index("user_id")
    # TTL index: Mongo removes sessions after they expire.
    db.auth_sessions.create_index("expires_at", expireAfterSeconds=0)
    db.auth_tokens.create_index("token_hash")
    db.auth_tokens.create_index([("user_id", 1), ("purpose", 1)])
    db.auth_tokens.create_index("expires_at", expireAfterSeconds=0)


def public_user(doc):
    """Strip sensitive fields before returning a user to the client."""
    if not doc:
        return None
    return {
        "id": str(doc["_id"]),
        "full_name": doc.get("full_name", ""),
        "email": doc.get("email", ""),
        "email_verified": bool(doc.get("email_verified", False)),
        "status": doc.get("status", STATUS_PENDING),
        "created_at": doc.get("created_at").isoformat() if doc.get("created_at") else None,
        "last_login_at": doc.get("last_login_at").isoformat() if doc.get("last_login_at") else None,
        "auth_provider": doc.get("auth_provider", "password"),
    }


# --- Users -----------------------------------------------------------------
def find_user_by_email(db, email):
    return db.users.find_one({"email": normalize_email(email)})


def find_user_by_id(db, user_id):
    try:
        return db.users.find_one({"_id": ObjectId(user_id)})
    except (InvalidId, TypeError):
        return None


def create_user(db, full_name, email, password_hash):
    doc = {
        "full_name": full_name.strip(),
        "email": normalize_email(email),
        "password_hash": password_hash,
        "email_verified": False,
        "status": STATUS_PENDING,
        "auth_provider": "password",
        "welcome_sent": False,
        "created_at": now(),
        "updated_at": now(),
        "last_login_at": None,
    }
    result = db.users.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


def set_user_fields(db, user_id, fields):
    fields["updated_at"] = now()
    db.users.update_one({"_id": ObjectId(user_id)}, {"$set": fields})


# --- Sessions --------------------------------------------------------------
def create_session(db, user_id, session_hash, expires_at, user_agent=None):
    doc = {
        "user_id": str(user_id),
        "session_hash": session_hash,
        "created_at": now(),
        "expires_at": expires_at,
        "last_seen_at": now(),
        # Store only a coarse UA string for the user's own session list; no IPs.
        "user_agent": (user_agent or "")[:200],
    }
    db.auth_sessions.insert_one(doc)
    return doc


def find_session(db, session_hash):
    return db.auth_sessions.find_one({"session_hash": session_hash})


def touch_session(db, session_hash):
    db.auth_sessions.update_one(
        {"session_hash": session_hash}, {"$set": {"last_seen_at": now()}}
    )


def delete_session(db, session_hash):
    db.auth_sessions.delete_one({"session_hash": session_hash})


def delete_all_sessions(db, user_id, except_hash=None):
    query = {"user_id": str(user_id)}
    if except_hash:
        query["session_hash"] = {"$ne": except_hash}
    return db.auth_sessions.delete_many(query).deleted_count


def list_sessions(db, user_id):
    return list(db.auth_sessions.find({"user_id": str(user_id)}).sort("created_at", -1))


# --- Tokens (verification + reset) -----------------------------------------
def create_token(db, user_id, purpose, token_hash, expires_at, extra=None):
    doc = {
        "user_id": str(user_id),
        "purpose": purpose,
        "token_hash": token_hash,
        "expires_at": expires_at,
        "consumed": False,
        "attempts": 0,
        "created_at": now(),
    }
    if extra:
        doc.update(extra)
    db.auth_tokens.insert_one(doc)
    return doc


def find_active_token(db, user_id, purpose):
    """Most recent unconsumed, unexpired token for a user+purpose."""
    return db.auth_tokens.find_one(
        {
            "user_id": str(user_id),
            "purpose": purpose,
            "consumed": False,
            "expires_at": {"$gt": now()},
        },
        sort=[("created_at", -1)],
    )


def find_token_by_hash(db, purpose, token_hash):
    return db.auth_tokens.find_one(
        {"purpose": purpose, "token_hash": token_hash}
    )


def consume_token(db, token_id):
    db.auth_tokens.update_one(
        {"_id": token_id}, {"$set": {"consumed": True, "consumed_at": now()}}
    )


def increment_token_attempts(db, token_id):
    db.auth_tokens.update_one({"_id": token_id}, {"$inc": {"attempts": 1}})
    doc = db.auth_tokens.find_one({"_id": token_id})
    return doc.get("attempts", 0) if doc else 0


def invalidate_tokens(db, user_id, purpose):
    """Consume all outstanding tokens of a purpose (e.g. after a reset)."""
    db.auth_tokens.update_many(
        {"user_id": str(user_id), "purpose": purpose, "consumed": False},
        {"$set": {"consumed": True, "consumed_at": now()}},
    )
