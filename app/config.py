from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    line_channel_secret: str = Field(..., alias="LINE_CHANNEL_SECRET")
    line_channel_access_token: str = Field(..., alias="LINE_CHANNEL_ACCESS_TOKEN")
    anthropic_api_key: str = Field(..., alias="ANTHROPIC_API_KEY")
    claude_model: str = Field(default="claude-opus-4-7", alias="CLAUDE_MODEL")
    claude_max_tokens: int = Field(default=1024, alias="CLAUDE_MAX_TOKENS")
    port: int = Field(default=8000, alias="PORT")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
