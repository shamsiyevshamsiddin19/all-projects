"""Matnni ovozga aylantirish (TTS) — yordamchi saytidagi usul (Google Translate TTS).

Nega Gemini emas: `gemini-2.5-flash-preview-tts` bepul tarifda BUTUN loyihaga
kuniga ~10 ta so'rov beradi — bot amalda "Bugungi limit tugadi" deyaverardi.
Yordamchi sayti (`backend_py/app/handlers/tts.py`) allaqachon Google Translate
TTS ishlatadi: kalit talab qilmaydi, kunlik limiti yo'q va tayyor.

Usul (yordamchi bilan bir xil):
  matn -> gaplarga bo'linadi -> har gap <=150 belgilik bo'laklarga bo'linadi
  -> har bo'lak uchun MP3 olinadi (diskda keshlanadi) -> hammasi ketma-ket
  ulanadi -> ffmpeg OGG/Opus qiladi (Telegram ovozli xabar formati).

Gap chegarasi saqlanadi — bo'laklar gaplar orasida aralashmaydi, shuning uchun
o'qish ohangi tabiiy bo'lib, har gapdan keyin qisqa pauza qoladi.
"""
from __future__ import annotations

import hashlib
import logging
import os
import random
import re
import subprocess
import time
import urllib.parse
import uuid
import threading
from concurrent.futures import ThreadPoolExecutor

from config import settings

logger = logging.getLogger(__name__)

# Google Translate TTS limitsiz — matn uzunligini faqat o'zimiz cheklaymiz.
MAX_CHARS = 20000

# Google TTS bitta so'rovda ~200 belgidan kam matn qabul qiladi.
_CHUNK_CHARS = 150
_PARALLEL = 4
_TIMEOUT = 20

_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)

# Kesh: bir xil gap qayta o'qilganda so'rov yubormaymiz.
_CACHE_MAX_BYTES = 200 * 1024 * 1024   # ~200 MB
_CACHE_MAX_AGE_DAYS = 30
_CLEAN_CHANCE = 0.02                    # ~50 so'rovda bir marta


class QuotaExceeded(RuntimeError):
    """Endi ishlatilmaydi (Google TTS da kunlik limit yo'q).

    Sinf saqlanadi, chunki `bot/handlers/tts.py` uni import qiladi va
    tutadi — kelajakda limitli provayder qaytsa qayta ishlatiladi.
    """


_LANG_CONF = {
    "ru": {"tl": "ru", "name": "rus"},
    "en": {"tl": "en", "name": "ingliz"},
}


def _cache_dir() -> str:
    path = os.path.join(settings.work_dir, "tts_cache")
    os.makedirs(path, exist_ok=True)
    return path


def _prune_cache(cache_dir: str) -> None:
    """Eskirgan va ortiqcha kesh fayllarini o'chiradi (yosh -> hajm tartibida).

    Xatolar yutiladi: kesh tozalash asosiy ishni to'xtatmasligi kerak.
    """
    try:
        files = []
        for name in os.listdir(cache_dir):
            if not name.endswith(".mp3"):
                continue
            full = os.path.join(cache_dir, name)
            try:
                st = os.stat(full)
            except OSError:
                continue
            files.append((st.st_mtime, st.st_size, full))

        cutoff = time.time() - _CACHE_MAX_AGE_DAYS * 86400
        keep = []
        for mtime, size, full in files:
            if mtime < cutoff:
                try:
                    os.remove(full)
                except OSError:
                    pass
            else:
                keep.append((mtime, size, full))

        total = sum(s for _, s, _ in keep)
        if total > _CACHE_MAX_BYTES:
            keep.sort(key=lambda x: x[0])       # eng eskisi birinchi
            for _mtime, size, full in keep:
                if total <= _CACHE_MAX_BYTES:
                    break
                try:
                    os.remove(full)
                    total -= size
                except OSError:
                    pass
    except Exception:
        logger.exception("TTS keshini tozalab bo'lmadi")


def _split_sentences(text: str) -> list[str]:
    """Matnni gaplarga bo'ladi (. ! ? va yangi qator chegaralari bo'yicha)."""
    text = (text or "").replace("\r\n", "\n").strip()
    if not text:
        return []
    out: list[str] = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        for part in re.split(r"(?<=[.!?…])\s+", line):
            part = re.sub(r"\s+", " ", part).strip()
            if part:
                out.append(part)
    return out


def _split_into_chunks(text: str, max_chars: int = _CHUNK_CHARS) -> list[str]:
    """Bitta gapni so'z chegarasi bo'yicha <=max_chars bo'laklarga bo'ladi."""
    text = re.sub(r"\s+", " ", str(text or "").strip())
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]

    chunks: list[str] = []
    cur: list[str] = []
    cur_len = 0
    for word in text.split(" "):
        if not word:
            continue
        # Bitta so'zning o'zi juda uzun bo'lsa — majburan kesamiz.
        while len(word) > max_chars:
            if cur:
                chunks.append(" ".join(cur))
                cur, cur_len = [], 0
            chunks.append(word[:max_chars])
            word = word[max_chars:]
        if cur_len + len(word) + 1 > max_chars and cur:
            chunks.append(" ".join(cur))
            cur, cur_len = [word], len(word)
        else:
            cur.append(word)
            cur_len += len(word) + 1
    if cur:
        chunks.append(" ".join(cur))
    return chunks


def _fetch_chunk_mp3(session, chunk: str, tl: str, cache_dir: str) -> bytes:
    """Keshdan yoki Google TTS dan bitta bo'lak MP3 baytlarini oladi."""
    key = hashlib.md5(f"{tl}:{chunk}".encode("utf-8")).hexdigest()
    cache_file = os.path.join(cache_dir, f"{key}.mp3")
    if os.path.isfile(cache_file):
        try:
            with open(cache_file, "rb") as f:
                data = f.read()
            if len(data) > 100:
                return data
        except OSError:
            pass

    url = (
        "https://translate.google.com/translate_tts"
        f"?ie=UTF-8&tl={tl}&client=tw-ob&q={urllib.parse.quote(chunk)}"
    )
    for attempt in (1, 2):
        try:
            r = session.get(url, headers={"User-Agent": _USER_AGENT}, timeout=_TIMEOUT)
            if r.status_code == 200 and len(r.content) > 100:
                try:
                    with open(cache_file, "wb") as f:
                        f.write(r.content)
                    if random.random() < _CLEAN_CHANCE:
                        _prune_cache(cache_dir)
                except OSError:
                    pass
                return r.content
            logger.warning(
                "TTS bo'lak olinmadi (urinish %s): status=%s len=%s",
                attempt, r.status_code, len(r.content),
            )
        except Exception as exc:
            logger.warning("TTS so'rov xatosi (urinish %s): %s", attempt, exc)
        time.sleep(0.5 * attempt)
    return b""


def _synthesize_mp3(text: str, tl: str) -> bytes:
    """Butun matn uchun ulangan MP3 baytlarini qaytaradi."""
    import requests

    cache_dir = _cache_dir()
    chunks: list[str] = []
    for sentence in _split_sentences(text):
        chunks.extend(_split_into_chunks(sentence))
    if not chunks:
        raise ValueError("Matn bo'sh")

    # requests.Session ko'p oqimli ishlash uchun xavfsiz emas: bir nechta
    # oqim bitta ulanishlar pulidan foydalanganda ma'lumot aralashib,
    # ConnectionReset / buzilgan audio bo'laklarga olib keladi. Shuning uchun
    # har bir oqimga alohida sessiya beramiz.
    local = threading.local()
    _sessions: list = []

    def fetch(chunk: str) -> bytes:
        session = getattr(local, "session", None)
        if session is None:
            session = requests.Session()
            local.session = session
            _sessions.append(session)
        return _fetch_chunk_mp3(session, chunk, tl, cache_dir)

    try:
        with ThreadPoolExecutor(max_workers=_PARALLEL) as pool:
            # map -> tartib saqlanadi (gaplar aralashib ketmaydi)
            parts = list(pool.map(fetch, chunks))
    finally:
        for session in _sessions:
            try:
                session.close()
            except Exception:
                pass

    ok = [p for p in parts if p]
    if not ok:
        raise RuntimeError("Google TTS audio qaytarmadi")
    if len(ok) < len(parts):
        logger.warning("TTS: %s bo'lakdan %s tasi olindi", len(parts), len(ok))
    return b"".join(ok)


def _mp3_to_ogg(mp3_path: str, ogg_path: str) -> None:
    """MP3 -> OGG/Opus (Telegram ovozli xabar formati).

    Sozlamalar nutq uchun tanlangan va 2 yadroli serverga moslangan:
    `voip` + `compression_level 5` xuddi shu 23 daqiqalik audioni standart
    `compression_level 10` ga qaraganda 79s o'rniga 46s da kodlaydi va fayl
    ham kichikroq chiqadi (5.2 MB -> 3.8 MB). Kodlash butun jarayondagi eng
    sekin bosqich — matn yuklab olish keshdan 0.4s da tugaydi.
    """
    cmd = [
        "ffmpeg", "-y",
        "-i", mp3_path,
        "-c:a", "libopus",
        "-b:a", "24k",
        "-vbr", "on",
        "-application", "voip",
        "-compression_level", "5",
        ogg_path,
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        err = proc.stderr.decode("utf-8", "ignore").strip()[-500:]
        raise RuntimeError(f"ffmpeg (tts) xato: {err}")
    if not os.path.exists(ogg_path):
        raise RuntimeError("OGG fayl yaratilmadi")


def text_to_voice(text: str, lang: str, work_dir: str | None = None) -> str:
    """Matnni ovozli xabar (.ogg/Opus) qiladi, fayl yo'lini qaytaradi.

    lang: "ru" yoki "en" (boshqasi ValueError). Chaqiruvchi asyncio.to_thread
    ichida ishlatishi kerak (sinxron: tarmoq + ffmpeg subprocess).
    """
    if lang not in _LANG_CONF:
        raise ValueError(f"TTS faqat ru/en uchun ishlaydi, berilgan: {lang}")
    text = (text or "").strip()
    if not text:
        raise ValueError("Matn bo'sh")
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS]

    work_dir = work_dir or settings.work_dir
    os.makedirs(work_dir, exist_ok=True)
    job_id = uuid.uuid4().hex[:12]
    mp3_path = os.path.join(work_dir, f"tts_{job_id}.mp3")
    ogg_path = os.path.join(work_dir, f"tts_{job_id}.ogg")

    try:
        mp3 = _synthesize_mp3(text, _LANG_CONF[lang]["tl"])
        with open(mp3_path, "wb") as f:
            f.write(mp3)
        _mp3_to_ogg(mp3_path, ogg_path)
        return ogg_path
    finally:
        try:
            if os.path.exists(mp3_path):
                os.remove(mp3_path)
        except OSError:
            pass
