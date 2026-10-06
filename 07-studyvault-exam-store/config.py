"""Sozlamalar — .env dan o'qiladi (maxfiy qiymatlar kodda emas)."""
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _ids(raw: str) -> tuple[int, ...]:
    out = []
    for part in (raw or "").replace(";", ",").split(","):
        part = part.strip()
        if part.lstrip("-").isdigit():
            out.append(int(part))
    return tuple(out)


@dataclass(frozen=True)
class Settings:
    # Telegram
    bot_token: str = os.getenv("BOT_TOKEN", "")
    bot_username: str = os.getenv("BOT_USERNAME", "sessiyatayyorgarlikbot")
    admin_ids: tuple[int, ...] = _ids(os.getenv("ADMIN_IDS", "7524804094"))

    # Biznes
    secret_salt: str = os.getenv("SECRET_SALT", "talaba-xizmatlari-secret")
    base_price: int = int(os.getenv("BASE_PRICE", "10000"))
    referrals_for_free: int = int(os.getenv("REFERRALS_FOR_FREE", "5"))

    # Click to'lov (URL eski serverda — bot faqat to'lov havolasini yasaydi)
    click_service_id: str = os.getenv("CLICK_SERVICE_ID", "99657")
    click_merchant_id: str = os.getenv("CLICK_MERCHANT_ID", "59136")
    click_merchant_user_id: str = os.getenv("CLICK_MERCHANT_USER_ID", "81435")
    click_base_url: str = os.getenv("CLICK_BASE_URL", "https://my.click.uz/services/pay")
    click_tx_prefix: str = os.getenv("CLICK_TX_PREFIX", "BAZA_")

    # Ko'prik: eski PHP Click endpointlari shu maxfiy sir bilan murojaat qiladi
    internal_secret: str = os.getenv("INTERNAL_SECRET", "")
    web_host: str = os.getenv("WEB_HOST", "127.0.0.1")
    web_port: int = int(os.getenv("WEB_PORT", "8090"))

    # Web admin panel (Basic Auth)
    admin_user: str = os.getenv("ADMIN_USER", "admin")
    admin_password: str = os.getenv("ADMIN_PASSWORD", "")

    # PostgreSQL
    database_url: str = os.getenv(
        "DATABASE_URL", "postgresql://sessiya:sessiya@127.0.0.1:5432/sessiyabot"
    )

    def validate(self) -> None:
        missing = [k for k in ("bot_token", "internal_secret") if not getattr(self, k)]
        if missing:
            raise RuntimeError(f".env da yo'q: {', '.join(missing)}")


settings = Settings()
