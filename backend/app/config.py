from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        extra="ignore",
        case_sensitive=False,
    )

    database_url: str = "postgresql+psycopg://transitnotice:transitnotice_dev_only@localhost:5432/transitnotice"
    demo_mode: bool = True
    scheduler_enabled: bool = True
    refresh_interval_minutes: int = 10
    stale_after_minutes: int = 30
    request_timeout_seconds: int = 15
    max_retries: int = 3
    mtc_enabled: bool = True
    cmrl_enabled: bool = True
    alert_mode: str = "demo"
    alert_recipients: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_sender: str = ""
    smtp_use_tls: bool = True
    app_timezone: str = "UTC"
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def cta_ready(self) -> bool:
        return self.cta_terms_accepted

    @property
    def smtp_ready(self) -> bool:
        return all((self.smtp_host, self.smtp_username, self.smtp_password, self.smtp_sender))


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
