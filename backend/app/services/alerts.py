from datetime import datetime, timezone
from email.message import EmailMessage
import smtplib

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import AlertDelivery, Notice, utc_now


def log_alert(session: Session, notice: Notice, reason: str) -> None:
    """Create one local demo log or one configured email attempt per revision."""
    if settings.alert_mode.lower() == "email":
        recipients = [value.strip() for value in settings.alert_recipients.split(",") if value.strip()]
        channel = "email"
        if not settings.smtp_ready or not recipients:
            recipients = ["configuration-required"]
    else:
        recipients = ["local-demo"]
        channel = "demo"

    subject = "TransitNotice: " + notice.summary[:250]
    for recipient in recipients:
        exists = session.scalar(
            select(AlertDelivery.id).where(
                AlertDelivery.notice_id == notice.id,
                AlertDelivery.revision_number == notice.revision_number,
                AlertDelivery.channel == channel,
                AlertDelivery.recipient == recipient,
            )
        )
        if exists:
            continue
        delivery = AlertDelivery(
            notice_id=notice.id,
            revision_number=notice.revision_number,
            channel=channel,
            recipient=recipient,
            status="logged" if channel == "demo" else "queued",
            subject=subject,
            created_at=utc_now(),
            subscriber_filter={},
        )
        session.add(delivery)
        session.flush()
        if channel == "demo" or recipient == "configuration-required":
            if recipient == "configuration-required":
                delivery.status = "blocked"
                delivery.error_message = "Email mode needs SMTP settings and at least one recipient"
            continue
        _send_email(delivery, notice, reason)


def _send_email(delivery: AlertDelivery, notice: Notice, reason: str) -> None:
    message = EmailMessage()
    message["Subject"] = delivery.subject
    message["From"] = settings.smtp_sender
    message["To"] = delivery.recipient
    message.set_content(
        "TransitNotice advisory update\n\n"
        + notice.summary
        + "\n\n"
        + reason
        + "\n\nAgency: "
        + notice.agency.name
        + "\nRoutes: "
        + ", ".join(notice.route_ids or [])
        + "\nValid to: "
        + (notice.valid_to.isoformat() if notice.valid_to else "Not stated by source")
        + "\nSource: "
        + (notice.source_url or "No source detail link provided")
    )
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as smtp:
            if settings.smtp_use_tls:
                smtp.starttls()
            smtp.login(settings.smtp_username, settings.smtp_password)
            smtp.send_message(message)
        delivery.status = "sent"
        delivery.delivered_at = datetime.now(timezone.utc)
    except Exception as exc:
        delivery.status = "failed"
        delivery.error_message = (type(exc).__name__ + ": " + str(exc))[:1000]
