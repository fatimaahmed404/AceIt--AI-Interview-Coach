"""
High-level transactional-email helpers used by the auth routes.

These keep email composition out of the controllers and return the delivery
status ("sent" | "console") or raise EmailDeliveryError. Each helper logs only
non-sensitive metadata (recipient + type), never the token/OTP/link.
"""
import logging

from utils import email_service, email_templates

log = logging.getLogger("aceit.mailer")


def send_verification(to_address, full_name, token):
    subject, html, text = email_templates.verification_email(full_name, token)
    return email_service.send_email(to_address, subject, html, text)


def send_password_reset(to_address, full_name, otp):
    subject, html, text = email_templates.password_reset_email(full_name, otp)
    return email_service.send_email(to_address, subject, html, text)


def send_password_changed(to_address, full_name):
    subject, html, text = email_templates.password_changed_email(full_name)
    return email_service.send_email(to_address, subject, html, text)


def send_welcome(to_address, full_name):
    subject, html, text = email_templates.welcome_email(full_name)
    return email_service.send_email(to_address, subject, html, text)
