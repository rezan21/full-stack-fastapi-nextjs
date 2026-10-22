from typing import Self

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.config import settings
from src.models import Email


class UsersConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )
    FIRST_SUPERUSER: Email
    FIRST_SUPERUSER_PASSWORD: str
    EMAIL_CHANGE_TOKEN_EXPIRE_MINUTES: int = 60
    SIGNUP_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    @model_validator(mode="after")
    def _enforce_non_default_secrets(self) -> Self:
        settings.check_default_secret(
            "FIRST_SUPERUSER_PASSWORD", self.FIRST_SUPERUSER_PASSWORD
        )
        return self


users_settings = UsersConfig()  # type: ignore[call-arg]
