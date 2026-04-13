from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_ENV_FILE = _PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "dev"
    database_url: str = (
        "postgresql://postgres:123456@localhost:5432/academic_warning_db"
    )
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 43200
    refresh_token_expire_days: int = 30
    support_phone: str = "0362629326"

    cors_allow_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    cors_allow_headers: list[str] = ["Authorization", "Content-Type"]
    trusted_hosts: list[str] = ["localhost", "127.0.0.1"]
    max_upload_mb: int = 15
    ml_predict_rate_limit_per_minute: int = 60
    auth_login_ip_rate_limit_per_minute: int = 30
    auth_login_user_rate_limit_per_minute: int = 10

    ml_artifacts_dir: str = str(_PROJECT_ROOT / "ml_artifacts")

    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_use_tls: bool = False
    smtp_from_email: str = "no-reply@academic-warning-system.local"


@lru_cache
def get_settings() -> Settings:
    return Settings()
