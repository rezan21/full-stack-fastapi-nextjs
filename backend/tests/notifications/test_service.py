import ssl
from unittest.mock import MagicMock, patch

import pytest

from src.notifications.config import notifications_settings
from src.notifications.service import logger, send_email, send_notice_email


def send_with(monkeypatch: pytest.MonkeyPatch, **overrides: object) -> MagicMock:
    defaults = {
        "SMTP_HOST": "smtp.example.com",
        "EMAILS_FROM_EMAIL": "from@example.com",
        "SMTP_PORT": 587,
        "SMTP_TLS": False,
        "SMTP_SSL": False,
        "SMTP_USER": None,
        "SMTP_PASSWORD": None,
    }
    for name, value in {**defaults, **overrides}.items():
        monkeypatch.setattr(notifications_settings, name, value)
    with (
        patch("src.notifications.service.smtplib.SMTP") as plain,
        patch("src.notifications.service.smtplib.SMTP_SSL") as implicit,
    ):
        send_email(email_to="to@example.com", subject="Hi", html_content="<p>Hi</p>")
    return implicit if overrides.get("SMTP_SSL") else plain


def verifies_certificates(context: ssl.SSLContext) -> bool:
    return context.verify_mode == ssl.CERT_REQUIRED and context.check_hostname


def test_a_plain_connection_uses_no_tls_and_no_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = send_with(monkeypatch)

    connection.assert_called_once_with("smtp.example.com", 587, timeout=10)
    server = connection.return_value
    server.starttls.assert_not_called()
    server.login.assert_not_called()
    server.sendmail.assert_called_once()


def test_tls_is_started_with_a_context_that_verifies_certificates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = send_with(monkeypatch, SMTP_TLS=True)

    server = connection.return_value
    server.starttls.assert_called_once()
    assert verifies_certificates(server.starttls.call_args.kwargs["context"])


def test_ssl_connects_with_a_context_that_verifies_certificates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = send_with(monkeypatch, SMTP_SSL=True)

    assert verifies_certificates(connection.call_args.kwargs["context"])
    server = connection.return_value
    server.starttls.assert_not_called()


def test_credentials_are_sent_when_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    connection = send_with(monkeypatch, SMTP_USER="user", SMTP_PASSWORD="secret")

    server = connection.return_value
    server.login.assert_called_once_with("user", "secret")


def test_the_message_goes_to_the_recipient_from_the_sender(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = send_with(monkeypatch)

    server = connection.return_value
    sender, recipients, raw = server.sendmail.call_args.args
    assert (sender, recipients) == ("from@example.com", ["to@example.com"])
    assert "To: to@example.com" in raw
    assert "Subject: Hi" in raw


def test_a_refused_connection_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(notifications_settings, "SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr(notifications_settings, "EMAILS_FROM_EMAIL", "from@example.com")
    with (
        patch(
            "src.notifications.service.smtplib.SMTP", side_effect=ConnectionRefusedError
        ),
        pytest.raises(ConnectionRefusedError),
    ):
        send_email(email_to="to@example.com", subject="Hi", html_content="<p>Hi</p>")


def test_a_notice_that_cannot_be_sent_is_logged_not_raised() -> None:
    with (
        patch("src.notifications.service.send_email", side_effect=RuntimeError("down")),
        patch.object(logger, "exception") as log_exception,
    ):
        send_notice_email(email_to="to@example.com", subject="Hi", message="Hello")

    log_exception.assert_called_once()
