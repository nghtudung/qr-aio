from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "QR AIO"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    max_upload_bytes: int = 8 * 1024 * 1024
    max_url_download_bytes: int = 8 * 1024 * 1024
    request_timeout_seconds: float = 5.0
    rate_limit: str = "120/minute"

    model_config = SettingsConfigDict(env_file=".env", env_prefix="QR_AIO_")


@lru_cache
def get_settings() -> Settings:
    return Settings()
