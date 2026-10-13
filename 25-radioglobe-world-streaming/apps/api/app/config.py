import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    PROJECT_NAME: str = "RadioGlobe API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql+asyncpg://shamsiddin:postgres@localhost:5432/radioglobe"
    )
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Proxy / Security
    PROXY_SECRET_KEY: str = os.getenv("PROXY_SECRET_KEY", "radioglobe-super-secure-token-signing-secret-2026")
    PROXY_BASE_URL: str = os.getenv("PROXY_BASE_URL", "http://localhost:8000/api/v1/stream")
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://radio.shamsiyev.uz",
        "*"
    ]
    
    # Radio-Browser settings
    RADIO_BROWSER_MIRRORS: List[str] = [
        "de1.api.radio-browser.info",
        "nl1.api.radio-browser.info",
        "at1.api.radio-browser.info"
    ]
    USER_AGENT: str = "RadioGlobe/1.0 (+https://radio.shamsiyev.uz)"
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
