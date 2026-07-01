from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Agent SSH"
    app_secret: str = Field(default="change-me", validation_alias="APP_SECRET")
    credential_secret: str = Field(default="change-me", validation_alias="CREDENTIAL_SECRET")
    database_url: str = Field(default="sqlite:///./data/ai_agent_ssh.db", validation_alias="DATABASE_URL")
    ai_base_url: str | None = Field(default=None, validation_alias="AI_BASE_URL")
    ai_api_key: str | None = Field(default=None, validation_alias="AI_API_KEY")
    ai_model: str | None = Field(default=None, validation_alias="AI_MODEL")
    data_dir: Path = Field(default=Path("./data"), validation_alias="DATA_DIR")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
