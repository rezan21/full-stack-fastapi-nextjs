from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ChatConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )
    CHAT_RUNS_PER_HOUR: int = Field(default=30, gt=0)


chat_settings = ChatConfig()
