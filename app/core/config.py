"""
Application configuration using pydantic-settings.
All settings are loaded from environment variables or .env file.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────────────────────────
    APP_NAME: str = "AuraGrowth"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    ALLOWED_ORIGINS: str = "https://aura-growth.onrender.com,http://localhost:5173"

    # ── Database ─────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://linkshare_h09n_user:qJ73O9KqtxClUjBji3prbzXzkjGyQRIJ@dpg-d7mebq9j2pic73caljng-a/linkshare_h09n"

    # ── JWT ──────────────────────────────────────────────────────────────
    SECRET_KEY: str = "change-me-to-a-very-long-random-secret-key-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Google OAuth ─────────────────────────────────────────────────────
    GOOGLE_CLIENT_ID: str = "281050352510-h4pgsv9vba7p87g864kbbh9kfarp838s.apps.googleusercontent.com"
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "https://aura-growth-backend.onrender.com/api/v1/auth/google/callback"

    # ── Meta / Instagram ─────────────────────────────────────────────────
    META_APP_ID: str = ""
    META_APP_SECRET: str = ""
    META_WEBHOOK_VERIFY_TOKEN: str = "auragrowth_webhook_verify_token"
    INSTAGRAM_REDIRECT_URI: str = "http://localhost:8000/api/v1/instagram/callback"

    # ── SMTP / Email ─────────────────────────────────────────────────────
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_NAME: str = "AuraGrowth"
    SMTP_FROM_EMAIL: str = ""
    SMTP_USE_TLS: bool = True

    # ── AI / Gemini ──────────────────────────────────────────────────────
    GEMINI_API_KEY: str = ""

    # ── Rate Limiting ────────────────────────────────────────────────────
    IG_DM_RATE_LIMIT_PER_DAY: int = 200

    # ── Pagination ───────────────────────────────────────────────────────
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    # ── Request Logging ──────────────────────────────────────────────────
    ENABLE_REQUEST_LOGGING: bool = True

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]


settings = Settings()
