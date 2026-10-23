"""Redis asosidagi oddiy rate limiter va parallel oqim hisoblagichi."""

import logging
import ipaddress
from typing import Optional

from fastapi import Request

logger = logging.getLogger(__name__)


def client_ip(request: Request) -> str:
    """Haqiqiy mijoz IP'si.

    Sayt nginx/Caddy orqasida turgani uchun `request.client.host` har doim
    reverse proxy IP'si bo'ladi. Shuning uchun X-Forwarded-For ning BIRINCHI
    qiymati olinadi (uni bizning reverse proxy qo'yadi).
    """
    direct_peer = request.client.host if request.client else "unknown"

    # Forwarded headerlarni faqat ishonchli lokal reverse-proxy orqali kelgan
    # so'rovda qabul qilamiz. Aks holda mijoz X-Forwarded-For ni o'zi yozib,
    # rate limitni har so'rovda boshqa IP bilan chetlab o'tishi mumkin.
    try:
        peer_ip = ipaddress.ip_address(direct_peer)
        trusted_proxy = peer_ip.is_loopback
    except ValueError:
        trusted_proxy = False

    if trusted_proxy:
        candidate = request.headers.get("x-real-ip")
        if not candidate:
            xff = request.headers.get("x-forwarded-for", "")
            candidate = xff.split(",")[0].strip() if xff else ""
        if candidate:
            try:
                return str(ipaddress.ip_address(candidate.strip()))
            except ValueError:
                logger.warning("Noto'g'ri forwarded IP rad etildi: %r", candidate)

    return direct_peer


async def check_rate_limit(
    redis,
    key: str,
    limit: int,
    window_seconds: int = 60,
) -> bool:
    """Oyna ichida `limit` dan oshmaganini tekshiradi. True = ruxsat."""
    if redis is None:
        return True
    try:
        redis_key = f"rl:{key}"
        current = await redis.incr(redis_key)
        if current == 1:
            await redis.expire(redis_key, window_seconds)
        return current <= limit
    except Exception as exc:  # Redis yiqilsa — xizmatni to'xtatmaymiz
        logger.warning("Rate limit tekshirib bo'lmadi (%s): %s", key, exc)
        return True


class ConcurrencySlot:
    """Bir IP uchun parallel oqimlar sonini cheklaydi.

    `async with` bilan ishlatiladi: kirishda hisoblagich oshadi, chiqishda
    (mijoz uzilganda ham) albatta kamayadi.
    """

    def __init__(self, redis, ip: str, limit: int, ttl: int = 3600):
        self.redis = redis
        self.key = f"stream:conc:{ip}"
        self.limit = limit
        self.ttl = ttl
        self.acquired = False

    async def acquire(self) -> bool:
        if self.redis is None:
            self.acquired = True
            return True
        try:
            current = await self.redis.incr(self.key)
            # Osilib qolgan hisoblagich abadiy qolmasligi uchun TTL
            await self.redis.expire(self.key, self.ttl)
            if current > self.limit:
                await self.redis.decr(self.key)
                return False
            self.acquired = True
            return True
        except Exception as exc:
            logger.warning("Parallellik cheklovi ishlamadi (%s): %s", self.key, exc)
            self.acquired = True
            return True

    async def release(self) -> None:
        if not self.acquired or self.redis is None:
            return
        try:
            remaining = await self.redis.decr(self.key)
            if remaining < 0:
                await self.redis.delete(self.key)
        except Exception:
            pass
        finally:
            self.acquired = False
