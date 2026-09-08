"""TTS Audio yuklab olish moduli.

Google Translate TTS orqali gaplarni yuqori sifatli MP3 formatiga aylantiradi,
takrorlash (repeat: 1x, 2x, 3x) rejimini qo'llab-quvvatlaydi va yagona audio fayl
sifatida foydalanuvchiga taqdim etadi.
"""

from __future__ import annotations

import hashlib
import logging
import re
import urllib.parse
from pathlib import Path

from fastapi import Request
from starlette.responses import Response

from ..errors import ApiError

logger = logging.getLogger("yordamchi")

CACHE_DIR = Path("/tmp/yordamchi_tts_cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"


def _clean_filename(title: str, default: str = "audio") -> str:
    cleaned = re.sub(r'[\\/*?:"<>|]', "", str(title or "").strip())
    cleaned = re.sub(r"\s+", "_", cleaned)
    return cleaned[:80] or default


def _split_into_chunks(text: str, max_chars: int = 150) -> list[str]:
    """Google TTS bir so'rovda 200 belgidan kam matn qabul qiladi.
    Matnni gap yoki so'z chegaralari bo'yicha kichik bo'laklarga ajratamiz."""
    text = re.sub(r"\s+", " ", str(text or "").strip())
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]

    chunks: list[str] = []
    # Tinish belgilari yoki bo'sh joy bo'yicha bo'lamiz
    words = text.split(" ")
    cur: list[str] = []
    cur_len = 0
    for w in words:
        if not w:
            continue
        if cur_len + len(w) + 1 > max_chars and cur:
            chunks.append(" ".join(cur))
            cur = [w]
            cur_len = len(w)
        else:
            cur.append(w)
            cur_len += len(w) + 1
    if cur:
        chunks.append(" ".join(cur))
    return chunks


async def _fetch_chunk_mp3(client, chunk: str, tl: str) -> bytes:
    """Keshdan yoki Google TTS dan bitta bo'lak MP3 baytlarini oladi."""
    cache_key = hashlib.md5(f"{tl}:{chunk}".encode("utf-8")).hexdigest()
    cache_file = CACHE_DIR / f"{cache_key}.mp3"
    if cache_file.is_file():
        try:
            return cache_file.read_bytes()
        except Exception:
            pass

    encoded = urllib.parse.quote(chunk)
    url = f"https://translate.google.com/translate_tts?ie=UTF-8&tl={tl}&client=tw-ob&q={encoded}"
    try:
        r = await client.get(url, headers={"User-Agent": USER_AGENT})
        if r.status_code == 200 and len(r.content) > 100:
            try:
                cache_file.write_bytes(r.content)
            except Exception:
                pass
            return r.content
        logger.warning("TTS fetch muvaffaqiyatsiz bo'ldi: status=%s len=%d", r.status_code, len(r.content))
    except Exception as e:
        logger.warning("TTS request xatosi: %s", e)
    return b""


async def handle_tts_download(request: Request, body: dict, q: dict) -> Response:
    """Matn yoki gaplar ro'yxatini MP3 formatida yuklab beradi.

    Parametrlar (body yoki query):
      - text: bitta matn
      - sentences: gaplar ro'yxati (array)
      - lang: 'ru' / 'ru-RU' yoki 'en' / 'en-US'
      - repeat: har bir gapni takrorlash soni (1, 2, 3). Standart: 1
      - title: yuklanadigan fayl nomi
    """
    import httpx

    # Parametrlarni yig'amiz
    raw_sentences = body.get("sentences") or q.get("sentences")
    raw_text = body.get("text") or q.get("text") or ""
    raw_lang = (body.get("lang") or q.get("lang") or "en").lower()
    raw_repeat = body.get("repeat") or q.get("repeat") or 1
    raw_title = body.get("title") or q.get("title") or "reading_audio"

    # Tilni aniqlaymiz: ru yoki en
    tl = "ru" if raw_lang.startswith("ru") else "en"

    # Takrorlash soni 1..3 oralig'ida
    try:
        repeat_count = max(1, min(3, int(raw_repeat)))
    except (ValueError, TypeError):
        repeat_count = 1

    # Gaplar ro'yxatini shakllantiramiz
    sentences: list[str] = []
    if isinstance(raw_sentences, list):
        for s in raw_sentences:
            cleaned = str(s or "").strip()
            if cleaned:
                sentences.append(cleaned)
    elif raw_text:
        # Bitta matn berilgan bo'lsa
        sentences = [raw_text.strip()]

    if not sentences:
        raise ApiError("Yuklab olish uchun matn yoki gaplar topilmadi.", 400)

    # 1 daqiqadan ortiq davom etmasligi uchun xavfsizlik cheklovi: ko'pi bilan 300 gap
    sentences = sentences[:300]

    filename = _clean_filename(raw_title)
    if repeat_count > 1:
        filename += f"_{repeat_count}x"

    # MP3 fayllarni yig'amiz
    audio_parts: list[bytes] = []

    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
        for s in sentences:
            chunks = _split_into_chunks(s)
            sentence_audio: list[bytes] = []
            for ch in chunks:
                chunk_bytes = await _fetch_chunk_mp3(client, ch, tl)
                if chunk_bytes:
                    sentence_audio.append(chunk_bytes)

            if not sentence_audio:
                continue

            full_sent_bytes = b"".join(sentence_audio)

            # Har bir gapni repeat_count marta takrorlaymiz
            for _ in range(repeat_count):
                audio_parts.append(full_sent_bytes)

    if not audio_parts:
        raise ApiError("Audio yaratib bo'lmadi. Keyinroq qayta urinib ko'ring.", 502)

    final_audio = b"".join(audio_parts)

    headers = {
        "Content-Disposition": f'attachment; filename="{filename}.mp3"',
        "Content-Length": str(len(final_audio)),
        "Cache-Control": "public, max-age=86400",
        "Accept-Ranges": "bytes",
    }

    return Response(content=final_audio, media_type="audio/mpeg", headers=headers)


async def handle_tts_audio(request: Request, q: dict) -> Response:
    """Bitta gap yoki matn uchun MP3 audio qaytaradi (fondagi / lockscreen pleyer uchun)."""
    import httpx
    text = str(q.get("text") or "").strip()
    if not text:
        raise ApiError("Matn ko'rsatilmadi", 400)
    lang = str(q.get("lang") or "en").lower().strip()
    tl = "ru" if lang.startswith("ru") else "en"

    chunks = _split_into_chunks(text)
    if not chunks:
        raise ApiError("Matn bo'sh", 400)

    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        parts: list[bytes] = []
        for ch in chunks:
            data = await _fetch_chunk_mp3(client, ch, tl)
            if data:
                parts.append(data)
        if not parts:
            raise ApiError("TTS audio olib bo'lmadi", 502)
        full_mp3 = b"".join(parts)

    return Response(
        content=full_mp3,
        media_type="audio/mpeg",
        headers={
            "Cache-Control": "public, max-age=604800, immutable",
            "Accept-Ranges": "bytes",
            "Content-Length": str(len(full_mp3)),
        },
    )

