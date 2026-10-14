import os
import secrets
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, model_validator


class Settings(BaseSettings):
    PROJECT_NAME: str = "RadioGlobe API"
    VERSION: str = "1.1.0"
    API_V1_STR: str = "/api/v1"

    # Muhit: "development" | "production"
    ENVIRONMENT: str = "development"

    # Ma'lumotlar bazasi
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/radioglobe"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Proxy / xavfsizlik
    # DIQQAT: bu yerda zaxira (default) qiymat YO'Q. Productionda .env dan kelishi SHART.
    PROXY_SECRET_KEY: str = ""
    PROXY_BASE_URL: str = "http://localhost:8000/api/v1/stream"
    STREAM_TOKEN_TTL: int = 7200

    # CORS — faqat shu manzillar. "*" hech qachon ishlatilmaydi.
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://radio.shamsiyev.uz",
    ]

    # Rate limit (bir IP uchun)
    RATE_LIMIT_PLAY_PER_MIN: int = 30
    RATE_LIMIT_STREAM_CONCURRENT: int = 3

    # Hotlink himoyasi: oqim so'rovida Origin/Referer shu ro'yxatdan bo'lishi kerak
    ENFORCE_STREAM_REFERER: bool = True

    # Radio-Browser
    RADIO_BROWSER_MIRRORS: List[str] = [
        "de1.api.radio-browser.info",
        "nl1.api.radio-browser.info",
        "at1.api.radio-browser.info",
    ]
    USER_AGENT: str = "RadioGlobe/1.1 (+https://radio.shamsiyev.uz)"

    # Upstream ulanish cheklovlari
    UPSTREAM_CONNECT_TIMEOUT: float = 10.0
    UPSTREAM_READ_TIMEOUT: float = 30.0
    UPSTREAM_MAX_REDIRECTS: int = 3

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("ALLOWED_ORIGINS", mode="after")
    @classmethod
    def _no_wildcard_origin(cls, v: List[str]) -> List[str]:
        if "*" in v:
            raise ValueError(
                "ALLOWED_ORIGINS ichida '*' bo'lishi mumkin emas — "
                "aniq manzillarni ro'yxat qiling."
            )
        return v

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() in ("production", "prod")

    @model_validator(mode="after")
    def _validate_secret(self) -> "Settings":
        if not self.PROXY_SECRET_KEY:
            if self.is_production:
                # fail-closed: productionda kalitsiz ishga tushmaydi
                raise RuntimeError(
                    "PROXY_SECRET_KEY o'rnatilmagan. Productionda bu MAJBURIY. "
                    "Yaratish: python3 -c \"import secrets; print(secrets.token_urlsafe(48))\""
                )
            # developmentda har ishga tushishda yangi tasodifiy kalit
            object.__setattr__(self, "PROXY_SECRET_KEY", secrets.token_urlsafe(48))
        elif len(self.PROXY_SECRET_KEY) < 32 and self.is_production:
            raise RuntimeError("PROXY_SECRET_KEY juda qisqa (kamida 32 belgi bo'lsin).")
        return self


settings = Settings()
