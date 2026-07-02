"""Application configuration."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "ugra"
    app_env: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    log_level: str = "INFO"

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    database_url: PostgresDsn = Field(
        default="postgresql+asyncpg://ugra:ugra@localhost:5432/ugra"
    )

    openai_api_key: str = ""
    anthropic_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"
    default_llm_provider: Literal["openai", "anthropic", "ollama"] = "openai"
    default_llm_model: str = "gpt-4o-mini"

    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    telegram_bot_token: str = ""
    telegram_webhook_url: str = ""

    hh_api_token: str = ""
    geekjob_api_token: str = ""

    mcp_servers: str = "[]"

    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    prometheus_port: int = 9090

    autonomous_enabled: bool = True
    autonomous_interval_seconds: int = 300
    use_postgres_memory: bool = True
    default_user_id: str = ""

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
