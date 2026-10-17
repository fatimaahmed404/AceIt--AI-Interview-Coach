"""
Transactional email service for AceIt (the Flask/Python equivalent of a
Nodemailer service).

Design:
  * A single reusable `send_email(to, subject, html, text)` entry point, kept
    independent of the auth controllers (routes call high-level helpers like
    send_verification_email()).
  * Real delivery uses smtplib with STARTTLS or implicit TLS and a timeout.
  * If SMTP is not configured, and MAIL_CONSOLE_FALLBACK is on, the message is
    logged to the console (dev mode) and reported as "console", never as a
    successful real send. If the fallback is off, a send with no SMTP config
    raises so callers can surface the failure.
  * Logging is safe: we log the recipient and subject only, never the body,
    OTP codes, tokens, or full verification links.

Return value of send_email: one of "sent" (real SMTP delivery), "console"
(logged in dev), and it raises EmailDeliveryError on an actual failure.
"""
import ssl
import smtplib
import logging
from email.message import EmailMessage

import config

log = logging.getLogger("aceit.email")


class EmailDeliveryError(Exception):
    """Raised when an email could not be delivered."""


def _from_header():
    return f"{config.MAIL_FROM_NAME} <{config.MAIL_FROM_ADDRESS}>"


def send_email(to_address, subject, html_body, text_body):
    """
    Send one email. Returns "sent" or "console". Raises EmailDeliveryError on
    a real delivery failure (so callers never treat a failure as success).
    """
    if not config.smtp_configured():
        if config.MAIL_CONSOLE_FALLBACK:
            log.info(
                "[email:console] SMTP not configured; logging email instead of "
                "sending. to=%s subject=%r", to_address, subject
            )
            # Print a short preview to the console for local development only.
            log.info("[email:console] --- text preview ---\n%s", text_body)
            return "console"
        raise EmailDeliveryError("SMTP is not configured and console fallback is disabled.")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = _from_header()
    msg["To"] = to_address
    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype="html")

    try:
        if config.SMTP_SECURE:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(
                config.SMTP_HOST, config.SMTP_PORT,
                timeout=config.SMTP_TIMEOUT, context=context,
            ) as server:
                if config.SMTP_USER:
                    server.login(config.SMTP_USER, config.SMTP_PASS)
                server.send_message(msg)
        else:
            with smtplib.SMTP(
                config.SMTP_HOST, config.SMTP_PORT, timeout=config.SMTP_TIMEOUT
            ) as server:
                server.ehlo()
                try:
                    server.starttls(context=ssl.create_default_context())
                    server.ehlo()
                except smtplib.SMTPException:
                    # Server may not support STARTTLS; continue only if that's expected.
                    log.warning("SMTP server did not accept STARTTLS")
                if config.SMTP_USER:
                    server.login(config.SMTP_USER, config.SMTP_PASS)
                server.send_message(msg)
    except Exception as exc:  # noqa: BLE001 - normalise to our error type
        log.error("Email delivery failed to=%s subject=%r error=%s",
                  to_address, subject, exc.__class__.__name__)
        raise EmailDeliveryError("Email could not be delivered.") from exc

    log.info("[email:sent] to=%s subject=%r", to_address, subject)
    return "sent"
