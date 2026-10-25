from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

ReasoningEffort = Literal["minimal", "low", "medium", "high"]


class AgentConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )
    OPENAI_API_KEY: SecretStr | None = None
    CHAT_MODEL: str = "gpt-5.4-mini"
    CHAT_REASONING_EFFORT: ReasoningEffort | None = None


agent_settings = AgentConfig()
