"""Pexels stok-fotolar — slayd muqova/illyustrativ fon uchun.

Kalit bo'lmasa yoki so'rov muvaffaqiyatsiz bo'lsa, jim None qaytaradi —
taqdimot baribir tayyor bo'ladi, faqat fotosiz (gradient fon bilan)."""
from __future__ import annotations
import logging
import httpx
from config import settings

logger = logging.getLogger(__name__)

_SEARCH_URL = "https://api.pexels.com/v1/search"


async def fetch_image(query: str, orientation: str = "landscape") -> bytes | None:
    """Mavzuga mos fotoni yuklab, xom baytlarni qaytaradi. Xatoda None."""
    key = settings.pexels_api_key
    query = (query or "").strip()
    if not key or not query:
        return None
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(
                _SEARCH_URL,
                headers={"Authorization": key},
                params={"query": query, "per_page": 1, "orientation": orientation},
            )
            resp.raise_for_status()
            photos = resp.json().get("photos") or []
            if not photos:
                return None
            url = photos[0]["src"]["large2x"]
            img_resp = await client.get(url)
            img_resp.raise_for_status()
            return img_resp.content
    except Exception as e:
        logger.debug("Pexels so'rovi muvaffaqiyatsiz (%r): %s", query, e)
        return None
