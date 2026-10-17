"""
Branded HTML + plain-text email templates for AceIt.

Each builder returns (subject, html, text). Links use config.FRONTEND_URL so we
never hard-code localhost or a production domain. Templates never include the
user's password or other sensitive account data.
"""
import html as _html

import config

BRAND = "AceIt"
ACCENT = "#534AB7"


def _shell(title, body_html):
    """Wrap content in a simple, email-client-safe branded layout."""
    return f"""\
<!DOCTYPE html>
<html>
  <body style="margin:0;padding:0;background:#f4f4f7;font-family:Arial,Helvetica,sans-serif;color:#1a1a2e;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f7;padding:24px 0;">
      <tr><td align="center">
        <table role="presentation" width="480" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:12px;overflow:hidden;border:1px solid #e6e6ef;">
          <tr><td style="background:{ACCENT};padding:18px 24px;">
            <span style="color:#ffffff;font-size:18px;font-weight:600;">{BRAND}</span>
            <span style="color:#d9d6f5;font-size:13px;"> — AI Interview Coach</span>
          </td></tr>
          <tr><td style="padding:24px;">
            <h2 style="margin:0 0 12px;font-size:18px;color:#1a1a2e;">{_html.escape(title)}</h2>
            {body_html}
          </td></tr>
          <tr><td style="padding:16px 24px;background:#fafafd;border-top:1px solid #e6e6ef;">
            <p style="margin:0;font-size:11px;color:#8a8aa0;">
              You received this email because an action was requested for your {BRAND} account.
              If this wasn't you, you can safely ignore it.
            </p>
          </td></tr>
        </table>
      </td></tr>
    </table>
  </body>
</html>"""


def verification_email(full_name, token):
    link = f"{config.FRONTEND_URL}/verify-email?token={token}"
    subject = f"Verify your {BRAND} email address"
    greeting = f"Hi {_html.escape(full_name or 'there')},"
    body = f"""
      <p style="font-size:14px;line-height:1.6;">{greeting}</p>
      <p style="font-size:14px;line-height:1.6;">
        Welcome to {BRAND}! Please confirm your email address to activate your account.
      </p>
      <p style="text-align:center;margin:24px 0;">
        <a href="{link}" style="background:{ACCENT};color:#fff;text-decoration:none;
           padding:11px 22px;border-radius:8px;font-size:14px;display:inline-block;">
          Verify email address
        </a>
      </p>
      <p style="font-size:12px;color:#6a6a80;line-height:1.6;">
        This link expires in {config.EMAIL_VERIFY_TOKEN_HOURS} hours. If the button
        doesn't work, copy and paste this link into your browser:<br>
        <span style="color:{ACCENT};word-break:break-all;">{link}</span>
      </p>
    """
    text = (
        f"{greeting}\n\nWelcome to {BRAND}! Verify your email address to activate "
        f"your account:\n{link}\n\nThis link expires in "
        f"{config.EMAIL_VERIFY_TOKEN_HOURS} hours. If you didn't sign up, ignore "
        f"this email.\n"
    )
    return subject, _shell("Verify your email", body), text


def password_reset_email(full_name, otp):
    subject = f"Your {BRAND} password reset code"
    greeting = f"Hi {_html.escape(full_name or 'there')},"
    body = f"""
      <p style="font-size:14px;line-height:1.6;">{greeting}</p>
      <p style="font-size:14px;line-height:1.6;">
        Use the code below to reset your {BRAND} password:
      </p>
      <p style="text-align:center;margin:20px 0;">
        <span style="font-size:30px;font-weight:700;letter-spacing:6px;color:{ACCENT};
          background:#eeedfe;padding:12px 22px;border-radius:8px;display:inline-block;">{otp}</span>
      </p>
      <p style="font-size:12px;color:#6a6a80;line-height:1.6;">
        This code expires in {config.RESET_OTP_MINUTES} minutes. If it expires,
        request a new one from the password reset page. If you didn't request a
        password reset, you can safely ignore this email — your password will not change.
      </p>
    """
    text = (
        f"{greeting}\n\nYour {BRAND} password reset code is: {otp}\n\n"
        f"It expires in {config.RESET_OTP_MINUTES} minutes. If you didn't request "
        f"a reset, ignore this email.\n"
    )
    return subject, _shell("Password reset code", body), text


def password_changed_email(full_name):
    subject = f"Your {BRAND} password was changed"
    greeting = f"Hi {_html.escape(full_name or 'there')},"
    reset_link = f"{config.FRONTEND_URL}/forgot-password"
    body = f"""
      <p style="font-size:14px;line-height:1.6;">{greeting}</p>
      <p style="font-size:14px;line-height:1.6;">
        This is a confirmation that the password for your {BRAND} account was just changed.
      </p>
      <p style="font-size:13px;line-height:1.6;color:#6a6a80;">
        If you made this change, no further action is needed. If you did <strong>not</strong>
        change your password, reset it immediately and secure your account:
      </p>
      <p style="text-align:center;margin:20px 0;">
        <a href="{reset_link}" style="background:{ACCENT};color:#fff;text-decoration:none;
           padding:10px 20px;border-radius:8px;font-size:14px;display:inline-block;">Reset password</a>
      </p>
    """
    text = (
        f"{greeting}\n\nThe password for your {BRAND} account was just changed. "
        f"If this wasn't you, reset your password immediately: {reset_link}\n"
    )
    return subject, _shell("Password changed", body), text


def welcome_email(full_name):
    subject = f"Welcome to {BRAND}!"
    greeting = f"Hi {_html.escape(full_name or 'there')},"
    start_link = f"{config.FRONTEND_URL}/"
    body = f"""
      <p style="font-size:14px;line-height:1.6;">{greeting}</p>
      <p style="font-size:14px;line-height:1.6;">
        Your email is verified and your {BRAND} account is ready. Here's how to start:
      </p>
      <ul style="font-size:14px;line-height:1.8;color:#2a2a40;">
        <li>Pick a question from the practice question bank</li>
        <li>Record a webcam answer</li>
        <li>Get instant multimodal feedback — voice, content, and body language</li>
        <li>Track your progress over time on the dashboard</li>
      </ul>
      <p style="text-align:center;margin:22px 0;">
        <a href="{start_link}" style="background:{ACCENT};color:#fff;text-decoration:none;
           padding:11px 22px;border-radius:8px;font-size:14px;display:inline-block;">Start practicing</a>
      </p>
    """
    text = (
        f"{greeting}\n\nYour {BRAND} account is ready! Pick a question, record a "
        f"webcam answer, and get instant feedback on your delivery, content, and "
        f"body language.\n\nStart here: {start_link}\n"
    )
    return subject, _shell(f"Welcome to {BRAND}", body), text
