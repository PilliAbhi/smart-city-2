"""Minimal Flask app for the Smart City Complaint Portal

Run with: python app.py  (or use the Debug configuration "Python: Flask")
"""

import os
import uuid
import secrets
import time
import smtplib
import ssl

from dotenv import load_dotenv
load_dotenv()

from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret")

# Simple in-memory store for demo purposes. Use a DB for production.
COMPLAINTS = {}
TOKEN_TTL_SECONDS = int(
    os.environ.get("TOKEN_TTL_SECONDS", 60 * 60 * 24)
)  # default 24 hours

# Development email backend (optional): 'console' | 'file'
DEV_EMAIL_BACKEND = os.environ.get("DEV_EMAIL_BACKEND", "").lower()
EMAIL_OUTPUT_DIR = os.environ.get("EMAIL_OUTPUT_DIR", "sent_emails")


def send_verification_email(
    to_email: str, reference_id: str, token: str, cc=None
) -> bool:
    """Send a verification email with a token and verification link using SMTP.

    Configure SMTP credentials via environment variables:
    - SMTP_HOST
    - SMTP_PORT
    - SMTP_USERNAME
    - SMTP_PASSWORD
    - SMTP_USE_TLS (true/false)
    - SENDER_EMAIL (optional; falls back to SMTP_USERNAME)
    """
    smtp_host = os.environ.get("SMTP_HOST")
    smtp_port = int(os.environ.get("SMTP_PORT", "0"))
    smtp_user = os.environ.get("SMTP_USERNAME")
    smtp_pass = os.environ.get("SMTP_PASSWORD")
    use_tls = os.environ.get("SMTP_USE_TLS", "true").lower() in ("1", "true", "yes")
    sender = os.environ.get("SENDER_EMAIL") or smtp_user

    # Build message (plain text)
    link = url_for(
        "verify_link", reference_id=reference_id, token=token, _external=True
    )
    subject = f"Confirm your complaint: {reference_id}"
    body = render_template(
        "verification_email.txt", reference_id=reference_id, token=token, link=link
    )

    # Check required SMTP configuration
    missing = [
        name
        for name, val in (
            ("SMTP_HOST", smtp_host),
            ("SMTP_PORT", smtp_port),
            ("SMTP_USERNAME", smtp_user),
            ("SMTP_PASSWORD", smtp_pass),
            ("SENDER_EMAIL", sender),
        )
        if not val
    ]

    if missing:
        # Development backends: print to console or write to a file so you can test without a real SMTP server
        if DEV_EMAIL_BACKEND == "console":
            app.logger.info(
                "DEV EMAIL (console) for %s: subject=%s\n%s", to_email, subject, body
            )
            print("=== DEV EMAIL (console) ===")
            print(f"To: {to_email}")
            print(f"Subject: {subject}")
            print(body)
            print("=== END DEV EMAIL ===")
            return True
        if DEV_EMAIL_BACKEND == "file":
            os.makedirs(EMAIL_OUTPUT_DIR, exist_ok=True)
            out_path = os.path.join(EMAIL_OUTPUT_DIR, f"{reference_id}.txt")
            with open(out_path, "w", encoding="utf-8") as fh:
                fh.write(f"To: {to_email}\nSubject: {subject}\n\n{body}\n")
            app.logger.info("DEV EMAIL saved to %s", out_path)
            return True

        app.logger.warning(
            "SMTP not configured (missing: %s), skipping email send",
            ",".join(missing),
        )
        return False

    message = MIMEMultipart()
    message["From"] = sender

    # If CCs are provided, set To header to include them for readability
    recipients = [to_email] + (cc or [])
    message["To"] = ", ".join(recipients)
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    try:
        if smtp_port == 465:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as server:
                server.login(smtp_user, smtp_pass)
                server.sendmail(sender, recipients, message.as_string())
        else:
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                if use_tls:
                    server.starttls(context=ssl.create_default_context())
                server.login(smtp_user, smtp_pass)
                server.sendmail(sender, recipients, message.as_string())
        app.logger.info("Sent verification email to %s", to_email)
        return True
    except Exception as exc:
        app.logger.exception("Failed to send verification email: %s", exc)
        # If DEV backend is enabled, write the email so developer can inspect it
        if DEV_EMAIL_BACKEND == "file":
            os.makedirs(EMAIL_OUTPUT_DIR, exist_ok=True)
            out_path = os.path.join(EMAIL_OUTPUT_DIR, f"{reference_id}_error.txt")
            with open(out_path, "w", encoding="utf-8") as fh:
                fh.write(
                    f"TO: {to_email}\nSUBJECT: {subject}\n\n{body}\n\nERROR: {exc}"
                )
            app.logger.info("Saved failed email to %s", out_path)
            return True
        return False


# Admin emails (optional) — set via environment variable `ADMIN_EMAILS`
ADMIN_EMAILS = [
    e.strip() for e in os.environ.get("ADMIN_EMAILS", "").split(",") if e.strip()
]

# Quick local hardcoded example (UNCOMMENT for quick local testing only)
# SENDER_EMAIL = 'abhiprincee121@gmail.com'
# ADMIN_EMAILS = ['admin@example.com']
# NOTE: prefer using environment variables for security and portability


def _get_missing_smtp_config():
    smtp_host = os.environ.get("SMTP_HOST")
    smtp_port = os.environ.get("SMTP_PORT")
    smtp_user = os.environ.get("SMTP_USERNAME")
    smtp_pass = os.environ.get("SMTP_PASSWORD")
    sender = os.environ.get("SENDER_EMAIL") or smtp_user
    missing = [
        name
        for name, val in (
            ("SMTP_HOST", smtp_host),
            ("SMTP_PORT", smtp_port),
            ("SMTP_USERNAME", smtp_user),
            ("SMTP_PASSWORD", smtp_pass),
            ("SENDER_EMAIL", sender),
        )
        if not val
    ]
    return missing


def send_admin_notification(reference_id: str, record: dict) -> bool:
    """Send a simple notification email to admins with complaint details."""
    if not ADMIN_EMAILS:
        return False

    smtp_host = os.environ.get("SMTP_HOST")
    smtp_port = int(os.environ.get("SMTP_PORT", "0"))
    smtp_user = os.environ.get("SMTP_USERNAME")
    smtp_pass = os.environ.get("SMTP_PASSWORD")
    use_tls = os.environ.get("SMTP_USE_TLS", "true").lower() in ("1", "true", "yes")
    sender = os.environ.get("SENDER_EMAIL") or smtp_user

    # Check required SMTP configuration
    missing = [
        name
        for name, val in (
            ("SMTP_HOST", smtp_host),
            ("SMTP_PORT", smtp_port),
            ("SMTP_USERNAME", smtp_user),
            ("SMTP_PASSWORD", smtp_pass),
            ("SENDER_EMAIL", sender),
        )
        if not val
    ]

    if missing:
        if DEV_EMAIL_BACKEND == "console":
            app.logger.info(
                "DEV ADMIN EMAIL (console) for %s: subject=%s\n%s",
                ADMIN_EMAILS,
                subject,
                body,
            )
            print("=== DEV ADMIN EMAIL (console) ===")
            print(f"To: {ADMIN_EMAILS}")
            print(f"Subject: {subject}")
            print(body)
            print("=== END DEV ADMIN EMAIL ===")
            return True
        if DEV_EMAIL_BACKEND == "file":
            os.makedirs(EMAIL_OUTPUT_DIR, exist_ok=True)
            out_path = os.path.join(EMAIL_OUTPUT_DIR, f"admin_{reference_id}.txt")
            with open(out_path, "w", encoding="utf-8") as fh:
                fh.write(f"To: {ADMIN_EMAILS}\nSubject: {subject}\n\n{body}\n")
            app.logger.info("Saved admin email to %s", out_path)
            return True

        app.logger.warning(
            "SMTP not configured (missing: %s), skipping admin notification",
            ",".join(missing),
        )
        return False

    subject = f"New complaint submitted: {reference_id}"
    submitted_at = datetime.fromtimestamp(
        record.get("created_at", time.time())
    ).isoformat()
    body = render_template(
        "admin_notification.txt",
        reference_id=reference_id,
        record=record,
        submitted_at=submitted_at,
    )

    message = MIMEMultipart()
    message["From"] = sender
    message["To"] = ", ".join(ADMIN_EMAILS)
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    try:
        if smtp_port == 465:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as server:
                server.login(smtp_user, smtp_pass)
                server.sendmail(sender, ADMIN_EMAILS, message.as_string())
        else:
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                if use_tls:
                    server.starttls(context=ssl.create_default_context())
                server.login(smtp_user, smtp_pass)
                server.sendmail(sender, ADMIN_EMAILS, message.as_string())
        app.logger.info(
            "Sent admin notification for %s to %s", reference_id, ADMIN_EMAILS
        )
        return True
    except Exception as exc:
        app.logger.exception(
            "Failed to send admin notification for %s: %s", reference_id, exc
        )
        return False


@app.route("/", methods=("GET", "POST"))
def index():
    if request.method == "POST":
        # Accept form data (demo-only, no DB)
        name = request.form.get("name")
        email = request.form.get("email")
        issue = request.form.get("issue")
        location = request.form.get("location")

        # Create a short reference id and 6-digit numeric token for friendly verification
        reference_id = f"REF-{uuid.uuid4().hex[:8].upper()}"
        token = f"{secrets.randbelow(10**6):06d}"
        created_at = time.time()

        COMPLAINTS[reference_id] = {
            "name": name,
            "email": email,
            "issue": issue,
            "location": location,
            "token": token,
            "created_at": created_at,
            "verified": False,
        }

        sent = send_verification_email(email, reference_id, token)
        # Notify admins (best-effort)
        admin_notified = send_admin_notification(reference_id, COMPLAINTS[reference_id])

        if sent:
            flash(
                f"Complaint submitted. A confirmation email (ref {reference_id}) has been sent to {email}.",
                "success",
            )
        else:
            # Provide helpful debugging info in debug mode
            missing = _get_missing_smtp_config()
            if missing and app.debug:
                flash(
                    f"Complaint submitted (ref {reference_id}). Email NOT sent. Missing SMTP config: {', '.join(missing)}",
                    "warning",
                )
            else:
                flash(
                    f"Complaint submitted (ref {reference_id}). We could not send an email—please contact support or keep this reference id.",
                    "warning",
                )

        if admin_notified:
            app.logger.info("Admin notified for %s", reference_id)

        return redirect(url_for("index"))

    return render_template("index.html")


@app.route("/verify", methods=("GET", "POST"))
def verify():
    """Allow user to verify by entering Reference ID and Token"""
    if request.method == "POST":
        reference_id = request.form.get("reference_id")
        token = request.form.get("token")

        if not reference_id or reference_id not in COMPLAINTS:
            flash("Invalid reference id.", "danger")
            return redirect(url_for("verify"))

        record = COMPLAINTS[reference_id]

        # Check token and TTL
        if time.time() - record["created_at"] > TOKEN_TTL_SECONDS:
            flash("Token expired. Please resubmit your complaint.", "warning")
            return redirect(url_for("verify"))

        if secrets.compare_digest(record["token"], token):
            record["verified"] = True
            flash(
                f"Reference {reference_id} successfully verified. Thank you!", "success"
            )
            return redirect(url_for("index"))

        flash("Invalid token for this reference.", "danger")
        return redirect(url_for("verify"))

    return render_template("verify.html")


@app.route("/verify/<reference_id>/<token>")
def verify_link(reference_id, token):
    """Verify directly from the link in the email"""
    record = COMPLAINTS.get(reference_id)

    if not record:
        flash("Invalid reference id.", "danger")
        return redirect(url_for("index"))

    if time.time() - record["created_at"] > TOKEN_TTL_SECONDS:
        flash("Token expired. Please resubmit your complaint.", "warning")
        return redirect(url_for("index"))

    if secrets.compare_digest(record["token"], token):
        record["verified"] = True
        flash(
            f"Reference {reference_id} successfully verified via email. Thank you!",
            "success",
        )
        return redirect(url_for("index"))

    flash("Invalid token.", "danger")
    return redirect(url_for("index"))


@app.route("/status/<reference_id>")
def status(reference_id):
    record = COMPLAINTS.get(reference_id)
    if not record:
        return "Reference not found", 404
    return {
        "reference_id": reference_id,
        "verified": record["verified"],
        "created_at": datetime.fromtimestamp(record["created_at"]).isoformat(),
    }


if __name__ == "__main__":
    # Use debug=True locally to see errors in the browser
    app.run(host="127.0.0.1", port=5000, debug=True)
