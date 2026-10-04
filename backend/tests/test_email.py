import ssl
from unittest.mock import MagicMock, patch

import pytest

from app.core.config import settings
from app.utils import send_email


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
        monkeypatch.setattr(settings, name, value)
    with (
        patch("app.utils.smtplib.SMTP") as plain,
        patch("app.utils.smtplib.SMTP_SSL") as implicit,
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
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr(settings, "EMAILS_FROM_EMAIL", "from@example.com")
    with (
        patch("app.utils.smtplib.SMTP", side_effect=ConnectionRefusedError),
        pytest.raises(ConnectionRefusedError),
    ):
        send_email(email_to="to@example.com", subject="Hi", html_content="<p>Hi</p>")
