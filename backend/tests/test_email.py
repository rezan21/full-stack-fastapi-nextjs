import socket
from unittest.mock import patch

import pytest

from app.core.config import settings
from app.utils import send_email


def smtp_options(monkeypatch: pytest.MonkeyPatch, **overrides: object) -> dict:
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
    with patch("app.utils.emails.message.Message") as message_class:
        send_email(email_to="to@example.com", subject="Hi", html_content="<p>Hi</p>")
    return message_class.return_value.send.call_args.kwargs["smtp"]


def test_a_plain_connection_has_no_tls_ssl_or_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert smtp_options(monkeypatch) == {
        "host": "smtp.example.com",
        "port": 587,
        "fail_silently": False,
    }


def test_tls_is_used_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    assert smtp_options(monkeypatch, SMTP_TLS=True)["tls"] is True


def test_ssl_is_used_when_tls_is_off(monkeypatch: pytest.MonkeyPatch) -> None:
    options = smtp_options(monkeypatch, SMTP_SSL=True)

    assert options["ssl"] is True
    assert "tls" not in options


def test_credentials_are_sent_when_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    options = smtp_options(monkeypatch, SMTP_USER="user", SMTP_PASSWORD="secret")

    assert options["user"] == "user"
    assert options["password"] == "secret"


def test_a_refused_connection_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        closed_port = probe.getsockname()[1]
    for name, value in {
        "SMTP_HOST": "127.0.0.1",
        "EMAILS_FROM_EMAIL": "from@example.com",
        "SMTP_PORT": closed_port,
        "SMTP_TLS": False,
        "SMTP_SSL": False,
    }.items():
        monkeypatch.setattr(settings, name, value)

    with pytest.raises(OSError):
        send_email(email_to="to@example.com", subject="Hi", html_content="<p>Hi</p>")
