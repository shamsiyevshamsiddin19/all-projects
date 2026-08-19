"""YouTube / Instagram videolarini yt-dlp orqali yuklab olish.

Arxitektura 3.2 (kirish manbalari) va 5.1 (link pipeline). Avval havola
metama'lumoti olinadi (yuklamasdan) — davomiylik/limit tekshiriladi, so'ng
video yuklab olinadi va mavjud pipeline (worker/pipeline.py) ishlaydi.

Faqat YouTube va Instagram qabul qilinadi (arxitektura 15 — xavfsizlik).
Funksiyalar sinxron — pipeline ularni asyncio.to_thread ichida chaqiradi.
"""
from __future__ import annotations

import glob
import logging
import os
import re

import yt_dlp

from config import settings
from worker import rapidapi

logger = logging.getLogger(__name__)

# Qo'llab-quvvatlanadigan manbalar (link aniqlash)
_YOUTUBE_RE = re.compile(
    r"https?://(?:www\.|m\.)?(?:youtube\.com/(?:watch\?|shorts/|embed/|live/|v/)"
    r"|youtu\.be/)",
    re.IGNORECASE,
)
_INSTAGRAM_RE = re.compile(
    r"https?://(?:www\.)?instagram\.com/(?:p/|reel/|reels/|tv/)",
    re.IGNORECASE,
)
_URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)


def detect_source(text: str | None) -> str | None:
    """Matndan link manbasini aniqlaydi: 'youtube' / 'instagram' / None."""
    if not text:
        return None
    if _YOUTUBE_RE.search(text):
        return "youtube"
    if _INSTAGRAM_RE.search(text):
        return "instagram"
    return None


def extract_url(text: str | None) -> str | None:
    """Matndan birinchi http(s) havolani ajratib oladi."""
    if not text:
        return None
    match = _URL_RE.search(text)
    return match.group(0) if match else None


# Brauzerga o'xshash User-Agent — datacenter IP'da bot-tekshiruvini kamaytiradi
_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

# YouTube player-client'lar tartibi. tv/android/ios datacenter IP'da
# ishlaydi; web/mweb EJS solver (Node.js) bilan ishlaydigan formatlarni beradi.
_YT_CLIENTS = ["tv", "android", "mweb", "web"]


def _common_opts() -> dict:
    """Har bir yt-dlp chaqiruviga qo'shiladigan umumiy sozlamalar.

    YouTube datacenter IP'larni bloklaydi. Node.js 22+ EJS solver (yt-dlp-ejs)
    orqali signature va n-challenge hal qilinadi — barcha sifatlar ochiladi.
    js_runtimes={'node': {}} — default deno o'rniga node'ni yoqadi.
    """
    return {
        "http_headers": {"User-Agent": _UA},
        "extractor_args": {
            "youtube": {
                "player_client": _YT_CLIENTS,
            }
        },
        "geo_bypass": True,
        "extractor_retries": 4,
        "js_runtimes": {"node": {}},
    }


def _cookie_opts() -> dict:
    """yt-dlp cookie sozlamalari (YouTube bot-tekshiruvi uchun). Bo'lmasa bo'sh."""
    if settings.ytdlp_cookies_file and os.path.isfile(settings.ytdlp_cookies_file):
        return {"cookiefile": settings.ytdlp_cookies_file}
    if settings.ytdlp_cookies_browser:
        return {"cookiesfrombrowser": (settings.ytdlp_cookies_browser,)}
    return {}


_COOKIE_RETRY_SIGNALS = ("cookie", "sign in", "not a bot", "no longer valid")


def _ydl_run(opts_base: dict, run_fn):
    """yt-dlp ni cookie bilan ishlatadi; cookie ishlamasa cookiesiz qayta urinadi.

    Eskirgan yoki blokdan o'tgan cookie sign-in/bot xatolarini chiqarishi mumkin —
    shunda cookiesiz davom etamiz (EJS node solver formatlarni ochib beradi).
    """
    opts_base = {**_common_opts(), **opts_base}
    cookie = _cookie_opts()
    if cookie:
        try:
            with yt_dlp.YoutubeDL({**opts_base, **cookie}) as ydl:
                return run_fn(ydl)
        except yt_dlp.utils.DownloadError as exc:
            exc_lower = str(exc).lower()
            if not any(sig in exc_lower for sig in _COOKIE_RETRY_SIGNALS):
                raise
            logger.warning("Cookie bilan xato, cookiesiz urinaman: %s", str(exc)[:140])
    with yt_dlp.YoutubeDL(opts_base) as ydl:
        return run_fn(ydl)


def probe_url(url: str) -> dict:
    """Yuklamasdan video metama'lumotini oladi (davomiylik, sarlavha, hajm)."""
    opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "skip_download": True,
        "socket_timeout": 30,
    }
    try:
        info = _ydl_run(opts, lambda ydl: ydl.extract_info(url, download=False))
    except Exception as exc:
        # YouTube bot-blok — RapidAPI fallback (sozlangan bo'lsa)
        if detect_source(url) == "youtube" and rapidapi.available():
            logger.warning("probe yt-dlp xato — RapidAPI: %s", str(exc)[:120])
            return rapidapi.probe(url)
        raise
    # Pleylist/ko'p video kelsa — birinchisini olamiz
    entries = info.get("entries") if isinstance(info, dict) else None
    if entries:
        info = entries[0]
    return {
        "duration": int(info.get("duration") or 0),
        "title": (info.get("title") or "").strip(),
        "filesize": int(info.get("filesize") or info.get("filesize_approx") or 0),
    }


def download_video(url: str, out_path: str) -> None:
    """Videoni out_path ga yuklab oladi (mp4, balandligi <= YTDLP_MAX_HEIGHT).

    yt-dlp kengaytmani o'zi tanlaydi; yakuniy faylni topib out_path ga
    keltiramiz va ortiqcha bo'laklarni tozalaymiz.
    """
    work_dir = os.path.dirname(os.path.abspath(out_path)) or "."
    base = os.path.splitext(os.path.basename(out_path))[0]
    max_h = settings.ytdlp_max_height

    opts = {
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "noplaylist": True,
        "outtmpl": os.path.join(work_dir, f"{base}.%(ext)s"),
        "format": (
            f"bestvideo[height<={max_h}][ext=mp4]+bestaudio[ext=m4a]/"
            f"best[height<={max_h}][ext=mp4]/"
            f"best[height<={max_h}]/best"
        ),
        "merge_output_format": "mp4",
        "retries": 3,
        "fragment_retries": 3,
        "socket_timeout": 30,
    }

    try:
        _ydl_run(opts, lambda ydl: ydl.download([url]))
    except yt_dlp.utils.DownloadError as exc:
        # YouTube bot-blok — RapidAPI fallback (sozlangan bo'lsa)
        if detect_source(url) == "youtube" and rapidapi.available():
            logger.warning("download yt-dlp xato — RapidAPI fallback: %s", str(exc)[:120])
            try:
                rapidapi.download(url, out_path, max_h)
            except Exception as rexc:
                raise RuntimeError(f"Video yuklab olinmadi (yt-dlp+API): {rexc}") from rexc
            if not os.path.exists(out_path) or os.path.getsize(out_path) == 0:
                raise RuntimeError("Video yuklab olinmadi (API bo'sh)")
            return  # RapidAPI muvaffaqiyatli — quyidagi yt-dlp fayl-qidiruvi shart emas
        raise RuntimeError(f"Video yuklab olinmadi: {exc}") from exc

    # Yakuniy faylni topamiz (.mp4 ni afzal ko'ramiz) va out_path ga ko'chiramiz
    produced = sorted(glob.glob(os.path.join(work_dir, f"{base}.*")))
    chosen: str | None = None
    for path in produced:
        if path.endswith(".part"):
            continue
        if path.endswith(".mp4"):
            chosen = path
            break
        if chosen is None:
            chosen = path
    if chosen and os.path.abspath(chosen) != os.path.abspath(out_path):
        os.replace(chosen, out_path)

    # Ortiqcha bo'laklarni (alohida audio/video, .part) tozalaymiz
    for path in glob.glob(os.path.join(work_dir, f"{base}.*")):
        if os.path.abspath(path) != os.path.abspath(out_path):
            try:
                os.remove(path)
            except OSError:
                pass

    if not os.path.exists(out_path) or os.path.getsize(out_path) == 0:
        raise RuntimeError("Video yuklab olinmadi (fayl bo'sh)")
