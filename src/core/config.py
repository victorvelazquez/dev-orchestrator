"""Application configuration."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """Application configuration loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # Version
    version: str = "0.1.0"
    
    # Telegram
    telegram_bot_token: str = Field(alias="TELEGRAM_BOT_TOKEN")
    telegram_allowed_users: list[int] = Field(
        default_factory=list,
        alias="TELEGRAM_ALLOWED_USERS",
    )
    
    # AI Providers
    anthropic_api_key: str = Field(alias="ANTHROPIC_API_KEY")
    google_ai_api_key: str = Field(alias="GOOGLE_AI_API_KEY")
    
    # GitHub
    github_token: str = Field(alias="GITHUB_TOKEN")
    
    # Application
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_dir: str = Field(default="/app/logs", alias="LOG_DIR")
    database_url: str = Field(
        default="sqlite:///data/orchestrator.db",
        alias="DATABASE_URL",
    )
    workspace_path: str = Field(default="/app/workspace", alias="WORKSPACE_PATH")
    
    # Optional settings
    checkpoint_interval: int = Field(default=300, alias="CHECKPOINT_INTERVAL")
    max_clarification_rounds: int = Field(default=10, alias="MAX_CLARIFICATION_ROUNDS")
    task_timeout: int = Field(default=1800, alias="TASK_TIMEOUT")
    sandbox_image: str = Field(default="python:3.11-slim", alias="SANDBOX_IMAGE")
    
    # Protected branches
    protected_branches: list[str] = Field(
        default=["main", "master", "develop", "development"],
    )
    
    @property
    def telegram_token(self) -> str:
        """Alias for telegram_bot_token."""
        return self.telegram_bot_token
    
    @property
    def workspace_dir(self) -> Path:
        """Get workspace directory as Path."""
        return Path(self.workspace_path)


@lru_cache
def get_config() -> Config:
    """Get cached configuration instance."""
    return Config()
