from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Muhitdan o'qiladigan, xavfsiz standartli ilova sozlamalari."""

    app_env: str = "development"
    app_host: str = "train.shamsiyev.uz"
    app_name: str = "train.shamsiyev.uz"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    """Sozlamalar obyektini har so'rovda qayta yaratmaslik uchun keshlaydi."""

    return Settings()

