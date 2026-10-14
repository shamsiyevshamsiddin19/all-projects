"""Audio oqim proxysi.

Vazifasi: HTTP oqimni HTTPS orqali uzatish va CORS header qo'shish.
Bu xizmat GEO-BLOKNI AYLANIB O'TISH uchun emas — faqat brauzerning
mixed-content va CORS cheklovlarini hal qiladi.
"""

import logging
from urllib.parse import urljoin

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db, get_redis
from app.models.stream import Stream
from app.services.rate_limit import ConcurrencySlot, client_ip
from app.services.token_service import verify_stream_token
from app.utils.ssrf_guard import is_safe_url

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Stream Proxy"])

# Oqimga uzatilmaydigan upstream header'lari
_HOP_BY_HOP = {
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailers", "transfer-encoding", "upgrade", "content-length",
    "content-encoding", "set-cookie",
}


def _allowed_origin(request: Request) -> str | None:
    """So'rov ruxsat etilgan manzildan kelganmi? CORS header qiymatini qaytaradi."""
    origin = request.headers.get("origin")
    if origin and origin in settings.ALLOWED_ORIGINS:
        return origin
    return None


def _referer_allowed(request: Request) -> bool:
    """Hotlink himoyasi: Origin yoki Referer bizning saytdan bo'lishi kerak."""
    if not settings.ENFORCE_STREAM_REFERER:
        return True

    origin = request.headers.get("origin")
    if origin:
        return origin in settings.ALLOWED_ORIGINS

    referer = request.headers.get("referer")
    if referer:
        return any(referer.startswith(o) for o in settings.ALLOWED_ORIGINS)

    # <audio src="..."> ba'zi brauzerlarda Origin ham, Referer ham yubormaydi.
    # Token baribir tekshirilgani uchun bunday so'rovga ruxsat beramiz.
    return True


async def _open_upstream(url: str) -> tuple[httpx.AsyncClient, httpx.Response]:
    """Redirect zanjirini QO'LDA kuzatadi va har qadamni SSRF uchun tekshiradi.

    `follow_redirects=True` ishlatib bo'lmaydi: u holda faqat birinchi URL
    tekshiriladi, redirect esa ichki manzilga (masalan bulut metadata
    endpointiga) olib borishi mumkin.
    """
    client = httpx.AsyncClient(
        timeout=httpx.Timeout(
            settings.UPSTREAM_CONNECT_TIMEOUT,
            read=settings.UPSTREAM_READ_TIMEOUT,
        ),
        follow_redirects=False,
        limits=httpx.Limits(max_connections=None, max_keepalive_connections=0),
    )

    current_url = url
    try:
        for _ in range(settings.UPSTREAM_MAX_REDIRECTS + 1):
            if not await is_safe_url(current_url):
                raise HTTPException(status_code=400, detail="Ruxsat etilmagan upstream manzil")

            req = client.build_request(
                "GET",
                current_url,
                headers={"User-Agent": settings.USER_AGENT, "Icy-MetaData": "1"},
            )
            res = await client.send(req, stream=True)

            if res.status_code in (301, 302, 303, 307, 308):
                location = res.headers.get("location")
                await res.aclose()
                if not location:
                    raise HTTPException(status_code=502, detail="Redirect manzili ko'rsatilmagan")
                current_url = urljoin(current_url, location)
                continue

            return client, res

        raise HTTPException(status_code=502, detail="Redirectlar soni chegaradan oshdi")
    except HTTPException:
        await client.aclose()
        raise
    except Exception as exc:
        await client.aclose()
        logger.warning("Upstream ulanish xatosi (%s): %s", url, exc)
        raise HTTPException(status_code=502, detail="Stansiyaga ulanib bo'lmadi") from exc


@router.get("/stream/{stream_id}")
async def proxy_audio_stream(
    stream_id: int,
    request: Request,
    t: str = Query(..., description="Imzolangan HMAC token"),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    if not verify_stream_token(stream_id, t):
        raise HTTPException(status_code=403, detail="Token yaroqsiz yoki muddati tugagan")

    if not _referer_allowed(request):
        raise HTTPException(status_code=403, detail="Bu manzildan so'rovga ruxsat yo'q")

    stream = (
        await db.execute(select(Stream).where(Stream.id == stream_id))
    ).scalar_one_or_none()
    if not stream:
        raise HTTPException(status_code=404, detail="Oqim topilmadi")

    ip = client_ip(request)
    slot = ConcurrencySlot(redis, ip, settings.RATE_LIMIT_STREAM_CONCURRENT)
    if not await slot.acquire():
        raise HTTPException(
            status_code=429,
            detail=f"Bir vaqtda {settings.RATE_LIMIT_STREAM_CONCURRENT} tadan ko'p oqim tinglab bo'lmaydi",
        )

    try:
        client, upstream = await _open_upstream(stream.url_resolved or stream.url)
    except Exception:
        await slot.release()
        raise

    if upstream.status_code >= 400:
        status = upstream.status_code
        await upstream.aclose()
        await client.aclose()
        await slot.release()
        detail = "Stansiya hududiy cheklangan" if status == 403 else "Stansiya javob bermadi"
        raise HTTPException(status_code=502, detail=detail)

    async def body():
        try:
            async for chunk in upstream.aiter_bytes(chunk_size=16384):
                yield chunk
        except Exception as exc:
            logger.info("Oqim uzildi (stream=%s): %s", stream_id, exc)
        finally:
            # Mijoz uzilsa ham upstream ulanish va parallellik sloti bo'shatiladi
            await upstream.aclose()
            await client.aclose()
            await slot.release()

    headers = {
        "Cache-Control": "no-store",
        "X-Content-Type-Options": "nosniff",
        "Vary": "Origin",
    }
    origin = _allowed_origin(request)
    if origin:
        headers["Access-Control-Allow-Origin"] = origin

    # Stansiyaning ICY metadatasi (hozir ijroda) — frontend o'qishi uchun ochiladi
    icy_name = upstream.headers.get("icy-name")
    if icy_name:
        headers["X-Icy-Name"] = icy_name
        headers["Access-Control-Expose-Headers"] = "X-Icy-Name"

    return StreamingResponse(
        body(),
        media_type=upstream.headers.get("content-type", "audio/mpeg"),
        headers=headers,
    )
