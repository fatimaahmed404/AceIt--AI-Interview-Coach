"""Shared test helpers for auth-related tests."""


def csrf_from_client(client):
    """Return the CSRF token the server set as a cookie on this test client."""
    # Werkzeug's test client needs an explicit domain for localhost cookies.
    for dom in ("localhost", "127.0.0.1", None):
        try:
            c = client.get_cookie("aceit_csrf", domain=dom)
            if c is not None:
                return c.value
        except Exception:  # noqa: BLE001
            continue
    # Fallback: read the internal cookie jar directly.
    jar = getattr(client, "_cookies", {})
    for key, cookie in jar.items():
        if (isinstance(key, tuple) and key[-1] == "aceit_csrf"):
            return cookie.value
    return None


def register_verify_login(client, db, email, password="SuperSecret123!", name="Test User"):
    """
    Register a user, force-verify them in the DB, log in, and return
    (user_doc, csrf_token). Exercises the real auth endpoints; email runs in
    console/test mode so nothing is actually sent.
    """
    from auth import models

    client.post("/api/auth/register", json={
        "full_name": name, "email": email, "password": password,
        "confirm_password": password, "accept_terms": True,
    })
    user = models.find_user_by_email(db, email)
    db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"email_verified": True, "status": models.STATUS_ACTIVE}},
    )
    client.post("/api/auth/login", json={"email": email, "password": password})
    return models.find_user_by_email(db, email), csrf_from_client(client)
