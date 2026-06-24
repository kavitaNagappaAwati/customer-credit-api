"""
config.py
─────────
Centralised application configuration loaded from environment variables / .env file.
All other modules import `settings` from here — never read os.environ directly.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-level settings validated by Pydantic."""

    # ── App ──────────────────────────────────────────────────────────────────
    APP_NAME: str = "Customer Credit Profile & Loan Offer Management API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # ── Database ──────────────────────────────────────────────────────────────
    DATABASE_URL: str

    # ── Logging ───────────────────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


# Singleton instance — import this everywhere
settings = Settings()
