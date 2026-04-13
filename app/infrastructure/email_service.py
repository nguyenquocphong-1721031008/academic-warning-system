import smtplib
from email.message import EmailMessage

from app.infrastructure.config.settings import get_settings


class EmailConfigError(ValueError):
    pass


class EmailDeliveryError(RuntimeError):
    pass


def send_email(to_email: str, subject: str, body: str) -> None:
    settings = get_settings()
    if not settings.smtp_host or not settings.smtp_from_email:
        raise EmailConfigError("SMTP chưa được cấu hình đầy đủ")

    msg = EmailMessage()
    msg["From"] = settings.smtp_from_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        if settings.smtp_use_tls:
            with smtplib.SMTP(
                settings.smtp_host, settings.smtp_port, timeout=10
            ) as server:
                server.starttls()
                if settings.smtp_user and settings.smtp_password:
                    server.login(settings.smtp_user, settings.smtp_password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(
                settings.smtp_host, settings.smtp_port, timeout=10
            ) as server:
                if settings.smtp_user and settings.smtp_password:
                    server.login(settings.smtp_user, settings.smtp_password)
                server.send_message(msg)
    except Exception as exc:
        raise EmailDeliveryError(
            "Gửi email thất bại: "
            f"{exc} (smtp={settings.smtp_host}:{settings.smtp_port}, tls={settings.smtp_use_tls})"
        ) from exc
