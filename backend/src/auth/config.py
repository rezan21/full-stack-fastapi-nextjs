from typing import Self

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.config import settings


class AuthConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 60
    AUTH_MAX_FAILURES: int = 5
    AUTH_LOCK_MINUTES: int = 15

    @model_validator(mode="after")
    def _enforce_non_default_secrets(self) -> Self:
        settings.check_default_secret("SECRET_KEY", self.SECRET_KEY)
        settings.check_secret_length("SECRET_KEY", self.SECRET_KEY)
        return self


auth_settings = AuthConfig()  # type: ignore[call-arg]
