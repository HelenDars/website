"""Настройки из переменных окружения (см. .env.example)."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://nordis:nordis@localhost:5432/nordis"
    redis_url: str = "redis://localhost:6379/0"
    nordis_timezone: str = "Asia/Almaty"
    nordis_encryption_key: str = ""
    anthropic_api_key: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
