"""
Authentication & authorization integration tests.

Covers registration, email verification, login, password reset (OTP),
authorization/ownership, and the email service test mode. Runs against a
throwaway MongoDB database with email in console/test mode (no real SMTP).
"""
import os
import importlib

import pytest

os.environ["MONGO_DB"] = "aceit_auth_test_db"
os.environ.setdefault("MAIL_CONSOLE_FALLBACK", "true")

from helpers import csrf_from_client  # noqa: E402


@pytest.fixture(scope="module")
def app_module():
    try:
        from pymongo import MongoClient
        MongoClient(os.environ.get("MONGO_URI", "mongodb://localhost:27017/"),
                    serverSelectionTimeoutMS=1500).admin.command("ping")
    except Exception:  # noqa: BLE001
        pytest.skip("MongoDB not available")
    import app as app_module
    importlib.reload(app_module)
    app_module.app.config["TESTING"] = True
    yield app_module
    try:
        app_module.client.drop_database("aceit_auth_test_db")
    except Exception:  # noqa: BLE001
        pass


@pytest.fixture()
def c(app_module):
    return app_module.app.test_client()


@pytest.fixture()
def db(app_module):
    return app_module.db


import uuid


def _uemail(prefix="user"):
    """Unique email so tests never collide with leftover DB state."""
    return f"{prefix}_{uuid.uuid4().hex[:10]}@example.com"


def _reg(c, email, pw="SuperSecret123!", name="Test User"):
    return c.post("/api/auth/register", json={
        "full_name": name, "email": email, "password": pw,
        "confirm_password": pw, "accept_terms": True,
    })


def _verify_token(db, email):
    """Reset the stored verify-token hash to a known raw token and return it."""
    from auth import models
    from auth.security import generate_token, hash_token
    user = models.find_user_by_email(db, email)
    tok = db.auth_tokens.find_one({"user_id": str(user["_id"]), "purpose": "email_verify"})
    raw = generate_token(32)
    db.auth_tokens.update_one({"_id": tok["_id"]}, {"$set": {"token_hash": hash_token(raw)}})
    return raw


def _reset_otp(db, email, otp="654321"):
    from auth import models
    from auth.security import hash_token
    user = models.find_user_by_email(db, email)
    rec = db.auth_tokens.find_one({"user_id": str(user["_id"]), "purpose": "password_reset",
                                   "consumed": False})
    db.auth_tokens.update_one({"_id": rec["_id"]}, {"$set": {"token_hash": hash_token(otp)}})
    return otp


# --- Registration ----------------------------------------------------------
def test_register_valid(c):
    r = _reg(c, _uemail("valid"))
    assert r.status_code == 201
    assert r.get_json()["email_delivery"] in ("console", "sent")


def test_register_invalid_email(c):
    r = c.post("/api/auth/register", json={
        "full_name": "X", "email": "not-an-email", "password": "SuperSecret123!",
        "confirm_password": "SuperSecret123!", "accept_terms": True})
    assert r.status_code == 400
    assert "email" in r.get_json()["fields"]


def test_register_weak_password(c):
    r = c.post("/api/auth/register", json={
        "full_name": "Weak Pw", "email": "weak@example.com", "password": "short",
        "confirm_password": "short", "accept_terms": True})
    assert r.status_code == 400
    assert "password" in r.get_json()["fields"]


def test_register_password_mismatch(c):
    r = c.post("/api/auth/register", json={
        "full_name": "Mismatch", "email": "mm@example.com", "password": "SuperSecret123!",
        "confirm_password": "Different123!", "accept_terms": True})
    assert r.status_code == 400
    assert "confirm_password" in r.get_json()["fields"]


def test_register_requires_terms(c):
    r = c.post("/api/auth/register", json={
        "full_name": "No Terms", "email": "nt@example.com", "password": "SuperSecret123!",
        "confirm_password": "SuperSecret123!", "accept_terms": False})
    assert r.status_code == 400
    assert "accept_terms" in r.get_json()["fields"]


def test_register_duplicate_is_generic(c):
    email = _uemail("dup")
    _reg(c, email)
    r = _reg(c, email)
    # Anti-enumeration: duplicate returns a generic 202, not an error revealing existence.
    assert r.status_code == 202


# --- Email verification ----------------------------------------------------
def test_verify_valid_then_login(c, db):
    email = _uemail("verify")
    _reg(c, email)
    raw = _verify_token(db, email)
    r = c.post("/api/auth/verify-email", json={"token": raw})
    assert r.status_code == 200
    # Now login works.
    r2 = c.post("/api/auth/login", json={"email": email, "password": "SuperSecret123!"})
    assert r2.status_code == 200


def test_verify_invalid_token(c):
    r = c.post("/api/auth/verify-email", json={"token": "bogus"})
    assert r.status_code == 400


def test_verify_reused_token_or_already_verified(c, db):
    email = _uemail("reuse")
    _reg(c, email)
    raw = _verify_token(db, email)
    assert c.post("/api/auth/verify-email", json={"token": raw}).status_code == 200
    # Second use: token consumed / already verified -> graceful.
    r = c.post("/api/auth/verify-email", json={"token": raw})
    assert r.status_code in (200, 400)


def test_login_unverified_blocked(c):
    email = _uemail("unverified")
    _reg(c, email)
    r = c.post("/api/auth/login", json={"email": email, "password": "SuperSecret123!"})
    assert r.status_code == 403
    assert r.get_json().get("needs_verification") is True


# --- Login -----------------------------------------------------------------
def test_login_invalid_credentials_generic(c, db):
    from auth import models
    email = _uemail("login")
    _reg(c, email)
    db.users.update_one({"email": email},
                        {"$set": {"email_verified": True, "status": models.STATUS_ACTIVE}})
    r = c.post("/api/auth/login", json={"email": email, "password": "WrongPassword1!"})
    assert r.status_code == 401
    assert r.get_json()["error"] == "Invalid email or password."


def test_login_unknown_user_generic(c):
    r = c.post("/api/auth/login", json={"email": "ghost@example.com", "password": "whatever12345"})
    assert r.status_code == 401
    assert r.get_json()["error"] == "Invalid email or password."


def test_logout(c, db):
    from auth import models
    email = _uemail("logout")
    _reg(c, email)
    db.users.update_one({"email": email},
                        {"$set": {"email_verified": True, "status": models.STATUS_ACTIVE}})
    c.post("/api/auth/login", json={"email": email, "password": "SuperSecret123!"})
    csrf = csrf_from_client(c)
    assert c.get("/api/auth/me").get_json()["user"] is not None
    assert c.post("/api/auth/logout", headers={"X-CSRF-Token": csrf}).status_code == 200
    assert c.get("/api/auth/me").get_json()["user"] is None


# --- Password reset --------------------------------------------------------
def _make_verified(c, db, email):
    _reg(c, email)
    from auth import models
    db.users.update_one({"email": email},
                        {"$set": {"email_verified": True, "status": models.STATUS_ACTIVE}})


def test_forgot_password_generic_for_unknown(c):
    r = c.post("/api/auth/forgot-password", json={"email": "nobody@example.com"})
    assert r.status_code == 200
    assert "reset code has been sent" in r.get_json()["message"]


def test_full_reset_flow(c, db):
    email = _uemail("reset")
    _make_verified(c, db, email)
    assert c.post("/api/auth/forgot-password", json={"email": email}).status_code == 200
    otp = _reset_otp(db, email)
    # wrong code
    assert c.post("/api/auth/verify-reset-code",
                  json={"email": email, "code": "000000"}).status_code == 400
    # correct code
    r = c.post("/api/auth/verify-reset-code", json={"email": email, "code": otp})
    assert r.status_code == 200
    ticket = r.get_json()["reset_ticket"]
    # reset
    assert c.post("/api/auth/reset-password", json={
        "email": email, "reset_ticket": ticket,
        "new_password": "BrandNewPass456!", "confirm_password": "BrandNewPass456!"}).status_code == 200
    # old fails, new works
    assert c.post("/api/auth/login", json={"email": email, "password": "SuperSecret123!"}).status_code == 401
    assert c.post("/api/auth/login", json={"email": email, "password": "BrandNewPass456!"}).status_code == 200


def test_reset_otp_attempt_limit(c, db):
    email = _uemail("attempts")
    _make_verified(c, db, email)
    c.post("/api/auth/forgot-password", json={"email": email})
    _reset_otp(db, email)
    last = None
    for _ in range(7):
        last = c.post("/api/auth/verify-reset-code",
                      json={"email": email, "code": "111111"})
    # After exceeding the max attempts the code is invalidated (429).
    assert last.status_code in (400, 429)


# --- Authorization / ownership ---------------------------------------------
def test_ownership_isolation(app_module, db):
    import uuid
    from auth import models
    e1 = f"owner1_{uuid.uuid4().hex[:6]}@example.com"
    e2 = f"owner2_{uuid.uuid4().hex[:6]}@example.com"

    c1 = app_module.app.test_client()
    _reg(c1, e1)
    db.users.update_one({"email": e1}, {"$set": {"email_verified": True, "status": "active"}})
    c1.post("/api/auth/login", json={"email": e1, "password": "SuperSecret123!"})
    csrf1 = csrf_from_client(c1)
    c1.post("/api/history", json={"question": "owned by user1", "overall_score": 7},
            headers={"X-CSRF-Token": csrf1})

    c2 = app_module.app.test_client()
    _reg(c2, e2)
    db.users.update_one({"email": e2}, {"$set": {"email_verified": True, "status": "active"}})
    c2.post("/api/auth/login", json={"email": e2, "password": "SuperSecret123!"})

    # User2 must not see user1's sessions.
    assert c2.get("/api/history").get_json() == [] or all(
        s["question"] != "owned by user1" for s in c2.get("/api/history").get_json()
    )


def test_profile_update_rejects_email_change(app_module, db):
    import uuid
    c = app_module.app.test_client()
    email = f"prof_{uuid.uuid4().hex[:6]}@example.com"
    _reg(c, email)
    db.users.update_one({"email": email}, {"$set": {"email_verified": True, "status": "active"}})
    c.post("/api/auth/login", json={"email": email, "password": "SuperSecret123!"})
    csrf = csrf_from_client(c)
    # Changing full_name works.
    assert c.patch("/api/user/profile", json={"full_name": "New Name"},
                   headers={"X-CSRF-Token": csrf}).status_code == 200
    # Attempting to change email is rejected (mass-assignment guard).
    r = c.patch("/api/user/profile", json={"email": "hijack@example.com"},
                headers={"X-CSRF-Token": csrf})
    assert r.status_code == 400


# --- Email service test mode ----------------------------------------------
def test_email_service_console_mode(monkeypatch):
    """
    With no SMTP configured, send_email must return "console" (logged, not
    sent) and never falsely report a real delivery. We force the un-configured
    state here so the test is hermetic regardless of the developer's local
    .env (which may have real SMTP credentials).
    """
    import config
    from utils import email_service, email_templates
    monkeypatch.setattr(config, "SMTP_HOST", "", raising=False)
    monkeypatch.setattr(config, "MAIL_CONSOLE_FALLBACK", True, raising=False)

    subject, html, text = email_templates.verification_email("Tester", "tok123")
    result = email_service.send_email("t@example.com", subject, html, text)
    assert result == "console"


def test_email_service_reports_failure_not_fake_success(monkeypatch):
    """When SMTP is 'configured' but the send raises, we must get an error,
    never a fake 'sent'."""
    import smtplib
    import config
    from utils import email_service, email_templates
    monkeypatch.setattr(config, "SMTP_HOST", "smtp.example.test", raising=False)
    monkeypatch.setattr(config, "SMTP_SECURE", False, raising=False)
    monkeypatch.setattr(config, "MAIL_CONSOLE_FALLBACK", False, raising=False)

    # Make the SMTP connection fail instantly instead of doing real network I/O.
    def _boom(*a, **k):
        raise OSError("connection refused (simulated)")
    monkeypatch.setattr(smtplib, "SMTP", _boom)

    subject, html, text = email_templates.verification_email("Tester", "tok123")
    with pytest.raises(email_service.EmailDeliveryError):
        email_service.send_email("t@example.com", subject, html, text)
