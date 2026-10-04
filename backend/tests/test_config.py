import pytest
from pydantic import ValidationError

from app.core.config import Settings

VALID = {
    "PROJECT_NAME": "Test",
    "SECRET_KEY": "a-secret-that-is-not-the-placeholder",
    "FIRST_SUPERUSER": "admin@example.com",
    "FIRST_SUPERUSER_PASSWORD": "a-password-that-is-not-the-placeholder",
    "DATABASE_URL": "postgresql://postgres:a-db-password@localhost:5432/app",
    "FASTAPI_ENV": None,
}


def settings_with(**overrides: str | None) -> Settings:
    return Settings(_env_file=None, **{**VALID, **overrides})  # type: ignore[arg-type]


def test_a_placeholder_secret_only_warns_in_development() -> None:
    with pytest.warns(UserWarning, match="SECRET_KEY"):
        settings_with(SECRET_KEY="changethis", FASTAPI_ENV="development")


@pytest.mark.parametrize(
    "overrides",
    [
        {"SECRET_KEY": "changethis"},
        {"FIRST_SUPERUSER_PASSWORD": "changethis"},
        {"DATABASE_URL": "postgresql://postgres:changethis@localhost:5432/app"},
    ],
)
def test_a_placeholder_secret_is_rejected_outside_development(
    overrides: dict[str, str],
) -> None:
    with pytest.raises(ValidationError, match="changethis"):
        settings_with(**overrides)


@pytest.mark.parametrize(
    "scheme", ["postgres://", "postgresql://", "postgresql+psycopg://"]
)
def test_the_database_url_always_uses_the_psycopg_driver(scheme: str) -> None:
    settings = settings_with(DATABASE_URL=f"{scheme}user:pw@localhost:5432/app")

    assert str(settings.DATABASE_URL).startswith("postgresql+psycopg://")
