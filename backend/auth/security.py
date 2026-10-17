"""
Low-level security primitives: password hashing, secure token/OTP generation,
hashing of tokens at rest, and constant-time comparison.

- Passwords are hashed with Argon2id (via argon2-cffi).
- Verification/reset tokens and session ids are random, high-entropy values.
  We store only a SHA-256 hash of them in the database so a DB leak does not
  expose usable tokens.
- OTP codes are compared in constant time.
"""
import hmac
import hashlib
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError

# Argon2id with sensible interactive-login parameters.
_ph = PasswordHasher(
    time_cost=3,
    memory_cost=64 * 1024,  # 64 MB
    parallelism=2,
)


# --- Passwords -------------------------------------------------------------
def hash_password(password: str) -> str:
    """Return an Argon2id hash string for the given password."""
    return _ph.hash(password)


def verify_password(stored_hash: str, password: str) -> bool:
    """Constant-time-ish verification of a password against its stored hash."""
    if not stored_hash:
        return False
    try:
        return _ph.verify(stored_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError, Exception):  # noqa: BLE001
        return False


def needs_rehash(stored_hash: str) -> bool:
    try:
        return _ph.check_needs_rehash(stored_hash)
    except Exception:  # noqa: BLE001
        return False


# --- Opaque tokens (session ids, verification tokens, reset tokens) --------
def generate_token(nbytes: int = 32) -> str:
    """Cryptographically secure URL-safe random token."""
    return secrets.token_urlsafe(nbytes)


def hash_token(token: str) -> str:
    """SHA-256 hash of a token for storage at rest."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def constant_time_equals(a: str, b: str) -> bool:
    """Timing-safe string comparison."""
    return hmac.compare_digest(str(a), str(b))


# --- OTP codes -------------------------------------------------------------
def generate_otp(digits: int = 6) -> str:
    """Generate a numeric OTP with no modulo bias."""
    lo = 10 ** (digits - 1)
    hi = (10 ** digits) - 1
    return str(secrets.randbelow(hi - lo + 1) + lo)
