import pytest
from pydantic import ValidationError

from src.auth.config import AuthConfig
from src.chat.config import ChatConfig
from src.config import Config, settings
from src.notifications.config import NotificationsConfig
from src.users.config import UsersConfig

VALID = {
    "PROJECT_NAME": "Test",
    "DATABASE_URL": "postgresql://postgres:a-db-password@localhost:5432/app",
    "FASTAPI_ENV": None,
}
SECRET_KEY = "a-secret-that-is-not-the-placeholder"


def config_with(**overrides: str | None) -> Config:
    return Config(_env_file=None, **{**VALID, **overrides})  # type: ignore[arg-type]


def auth_with(**overrides: str) -> AuthConfig:
    return AuthConfig(_env_file=None, **{"SECRET_KEY": SECRET_KEY, **overrides})  # type: ignore[call-arg]


def users_with(**overrides: str) -> UsersConfig:
    values = {
        "FIRST_SUPERUSER": "admin@example.com",
        "FIRST_SUPERUSER_PASSWORD": "a-password-that-is-not-the-placeholder",
    }
    return UsersConfig(_env_file=None, **{**values, **overrides})  # type: ignore[call-arg]


@pytest.fixture
def production(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "FASTAPI_ENV", None)


@pytest.fixture
def development(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "FASTAPI_ENV", "development")


@pytest.mark.usefixtures("development")
def test_a_placeholder_secret_only_warns_in_development() -> None:
    with pytest.warns(UserWarning, match="SECRET_KEY"):
        auth_with(SECRET_KEY="changethis")


@pytest.mark.usefixtures("production")
@pytest.mark.parametrize(
    "build",
    [
        lambda: auth_with(SECRET_KEY="changethis"),
        lambda: users_with(FIRST_SUPERUSER_PASSWORD="changethis"),
        lambda: config_with(
            DATABASE_URL="postgresql://postgres:changethis@localhost:5432/app"
        ),
    ],
)
def test_a_placeholder_secret_is_rejected_outside_development(build: object) -> None:
    with pytest.raises(ValidationError, match="changethis"):
        build()  # type: ignore[operator]


@pytest.mark.parametrize(
    "scheme", ["postgres://", "postgresql://", "postgresql+psycopg://"]
)
def test_the_database_url_always_uses_the_psycopg_driver(scheme: str) -> None:
    config = config_with(DATABASE_URL=f"{scheme}user:pw@localhost:5432/app")

    assert str(config.DATABASE_URL).startswith("postgresql+psycopg://")


@pytest.mark.usefixtures("development")
def test_a_short_secret_key_only_warns_in_development() -> None:
    with pytest.warns(UserWarning, match="at least 32 characters"):
        auth_with(SECRET_KEY="too-short")


@pytest.mark.usefixtures("production")
def test_a_short_secret_key_is_rejected_outside_development() -> None:
    with pytest.raises(ValidationError, match="at least 32 characters"):
        auth_with(SECRET_KEY="too-short")


@pytest.mark.usefixtures("production")
def test_a_long_secret_key_is_accepted_outside_development() -> None:
    assert auth_with(SECRET_KEY="a" * 32).SECRET_KEY == "a" * 32


def test_the_openai_key_is_optional(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    assert ChatConfig(_env_file=None).OPENAI_API_KEY is None


def test_an_empty_openai_key_counts_as_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "")

    assert ChatConfig(_env_file=None).OPENAI_API_KEY is None


def test_the_openai_key_is_kept_out_of_reprs() -> None:
    chat = ChatConfig(_env_file=None, OPENAI_API_KEY="sk-a-key-nobody-should-see")  # type: ignore[arg-type]

    assert chat.OPENAI_API_KEY is not None
    assert chat.OPENAI_API_KEY.get_secret_value() == "sk-a-key-nobody-should-see"
    assert "sk-a-key-nobody-should-see" not in repr(chat)


def test_the_chat_run_quota_must_be_positive() -> None:
    with pytest.raises(ValidationError, match="CHAT_RUNS_PER_HOUR"):
        ChatConfig(_env_file=None, CHAT_RUNS_PER_HOUR=0)


def test_emails_are_sent_from_the_project_name_by_default() -> None:
    notifications = NotificationsConfig(_env_file=None, EMAILS_FROM_NAME=None)

    assert notifications.EMAILS_FROM_NAME == settings.PROJECT_NAME


def test_emails_are_enabled_once_a_host_and_a_sender_are_set() -> None:
    unset = NotificationsConfig(_env_file=None, SMTP_HOST=None, EMAILS_FROM_EMAIL=None)
    configured = NotificationsConfig(
        _env_file=None, SMTP_HOST="smtp.example.com", EMAILS_FROM_EMAIL="a@example.com"
    )

    assert not unset.emails_enabled
    assert configured.emails_enabled
