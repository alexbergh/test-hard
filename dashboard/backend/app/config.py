"""Application configuration."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "Test-Hard Dashboard"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: Literal["development", "staging", "production"] = "development"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Security
    secret_key: str = Field(default="change-me-in-production-use-openssl-rand-hex-32")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/dashboard.db"

    # Docker
    docker_host: str = "unix:///var/run/docker.sock"

    # Prometheus
    prometheus_url: str = "http://localhost:9090"

    # Grafana
    grafana_url: str = "http://localhost:3000"
    grafana_api_key: str = ""

    # Loki
    loki_url: str = "http://localhost:3100"

    # Tempo (Tracing)
    tempo_url: str = "http://localhost:3200"
    otlp_endpoint: str = "http://localhost:4317"
    tracing_enabled: bool = True

    # SMTP / Email notifications
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    notification_email: str = ""

    # Scanning
    reports_dir: str = "./reports"
    scan_timeout: int = 600  # 10 minutes

    # Scheduler
    scheduler_enabled: bool = True
    scheduler_timezone: str = "UTC"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
