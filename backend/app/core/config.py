from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import json


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # --- Core ---
    PROJECT_NAME: str = "Email Credential Harvesting & Monitoring System"
    API_V1_STR: str = "/api/v1"
    LOG_LEVEL: str = "INFO"

    # --- Database (async driver) ---
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/otp_system"

    # --- Redis ---
    REDIS_URL: str = "redis://localhost:6379/0"

    # --- Security ---
    SECRET_KEY: str = "CHANGE_ME_generate_a_real_secret_key"
    ENCRYPTION_KEY: str = "CHANGE_ME_generate_a_real_fernet_key"

    # --- CORS ---
    CORS_ORIGINS: str = '["http://localhost:3000"]'

    @property
    def cors_origins_list(self) -> List[str]:
        return json.loads(self.CORS_ORIGINS)

    # --- Gmail OAuth 2.0 ---
    GMAIL_CLIENT_ID: str = ""
    GMAIL_CLIENT_SECRET: str = ""
    GMAIL_REDIRECT_URI: str = "http://localhost:8000/api/v1/oauth/gmail/callback"
    GMAIL_SCOPES: List[str] = [
        "https://www.googleapis.com/auth/gmail.readonly",
    ]

    # --- Monitoring ---
    POLLING_INTERVAL_SECONDS: int = 30
    MAX_CONSECUTIVE_FAILURES: int = 5


settings = Settings()
