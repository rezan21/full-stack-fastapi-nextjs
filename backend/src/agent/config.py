from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class AgentConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )
    OPENAI_API_KEY: SecretStr | None = None
    CHAT_MODEL: str = "gpt-5.4-mini"


agent_settings = AgentConfig()
