"""Input validation for auth requests."""
import config
from .models import valid_email, normalize_email


def validate_registration(data):
    """Return (cleaned, errors). cleaned has full_name, email, password."""
    errors = {}
    full_name = (data.get("full_name") or "").strip()
    email = normalize_email(data.get("email"))
    password = data.get("password") or ""
    confirm = data.get("confirm_password")
    accepted = data.get("accept_terms")

    if len(full_name) < 2:
        errors["full_name"] = "Please enter your full name."
    if not valid_email(email):
        errors["email"] = "Please enter a valid email address."
    pw_error = password_errors(password)
    if pw_error:
        errors["password"] = pw_error
    if confirm is not None and confirm != password:
        errors["confirm_password"] = "Passwords do not match."
    if not accepted:
        errors["accept_terms"] = "You must accept the terms and privacy policy."

    return {"full_name": full_name, "email": email, "password": password}, errors


def password_errors(password):
    """Return an error string if the password is too weak, else None."""
    if not password or len(password) < config.PASSWORD_MIN_LENGTH:
        return f"Password must be at least {config.PASSWORD_MIN_LENGTH} characters."
    checks = [
        any(c.islower() for c in password),
        any(c.isupper() for c in password),
        any(c.isdigit() for c in password),
        any(not c.isalnum() for c in password),
    ]
    if sum(checks) < 3:
        return ("Password must include at least three of: lowercase, uppercase, "
                "number, and symbol.")
    return None
