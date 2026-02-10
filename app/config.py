"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # API Keys
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    serpapi_key: str = ""

    # LLM Configuration
    llm_provider: Literal["openai", "anthropic"] = "openai"
    openai_model: str = "gpt-4-turbo-preview"
    anthropic_model: str = "claude-3-sonnet-20240229"

    # Database
    database_url: str = "sqlite+aiosqlite:///./seo_agent.db"

    # Application
    debug: bool = False
    log_level: str = "INFO"
    host: str = "0.0.0.0"
    port: int = 8000

    # Content Generation Defaults
    default_word_count: int = 1500
    default_language: str = "en"

    @property
    def use_mock_serp(self) -> bool:
        """Return True if SERP API key is not configured."""
        return not self.serpapi_key


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


