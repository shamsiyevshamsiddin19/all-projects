"""RapidAPI orqali YouTube video yuklab olish — yt-dlp bot-blok bo'lganda fallback.

youtube-media-downloader (DataFanatic): videoId -> formatlar (to'g'ridan-to'g'ri
googlevideo havolalari). YouTube datacenter IP bloki API tomonda hal qilinadi;
qaytgan havola IP'ga bog'lanmagan — server to'g'ridan-to'g'ri yuklaydi.

Faqat YouTube. Instagram uchun ishlatilmaydi.
"""
from __future__ import annotations

import logging
import os
import re
import subprocess
import time

import requests

from config import settings

logger = logging.getLogger(__name__)

_VIDEO_ID_RE = re.compile(
    r"(?:v=|/shorts/|/embed/|/live/|/v/|youtu\.be/)([A-Za-z0-9_-]{11})"
)
_TIMEOUT = 40
_CACHE: dict[str, tuple[float, dict]] = {}
_CACHE_TTL = 120  # soniya — probe va download bitta so'rovni baham ko'radi


def available() -> bool:
    return bool(settings.rapidapi_key)


def video_id(url: str) -> str | None:
    m = _VIDEO_ID_RE.search(url or "")
    return m.group(1) if m else None


def _details(vid: str) -> dict:
    cached = _CACHE.get(vid)
    if cached and time.time() - cached[0] < _CACHE_TTL:
        return cached[1]
    host = settings.rapidapi_host
    r = requests.get(
        f"https://{host}/v2/video/details",
        params={"videoId": vid},
        headers={"x-rapidapi-key": settings.rapidapi_key, "x-rapidapi-host": host},
        timeout=_TIMEOUT,
    )
    r.raise_for_status()
    data = r.json()
    if str(data.get("errorId") or "Success") != "Success":
        raise RuntimeError(f"RapidAPI xato: {data.get('errorId')}")
    _CACHE[vid] = (time.time(), data)
    return data


def _height(fmt: dict) -> int:
    m = re.search(r"\d+", str(fmt.get("quality") or ""))
    return int(m.group()) if m else 0


def probe(url: str) -> dict:
    """Metama'lumot (davomiylik, sarlavha) — yt-dlp probe ishlamaganда."""
    vid = video_id(url)
    if not vid:
        raise RuntimeError("YouTube video ID topilmadi")
    d = _details(vid)
    dur = d.get("lengthSeconds") or d.get("duration") or 0
    try:
        dur = int(float(dur))
    except (ValueError, TypeError):
        dur = 0
    return {"duration": dur, "title": str(d.get("title") or "").strip(), "filesize": 0}


def _stream_to(dl_url: str, path: str) -> None:
    with requests.get(dl_url, stream=True, timeout=_TIMEOUT) as r:
        r.raise_for_status()
        with open(path, "wb") as f:
            for chunk in r.iter_content(1 << 16):
                if chunk:
                    f.write(chunk)


def _ok(path: str) -> bool:
    return os.path.exists(path) and os.path.getsize(path) > 0


def download(url: str, out_path: str, max_h: int) -> None:
    """Videoni yuklaydi. Imkon bo'lsa HD (video-only + audio merge), aks holda
    progressive (audio bilan bitta fayl)."""
    vid = video_id(url)
    if not vid:
        raise RuntimeError("YouTube video ID topilmadi")
    d = _details(vid)
    vids = (d.get("videos") or {}).get("items") or []
    auds = (d.get("audios") or {}).get("items") or []

    def is_mp4(f):
        return str(f.get("extension") or "").lower() == "mp4"

    prog = sorted(
        [f for f in vids if f.get("hasAudio") and is_mp4(f) and _height(f) <= max_h],
        key=_height, reverse=True,
    )
    vonly = sorted(
        [f for f in vids if not f.get("hasAudio") and is_mp4(f) and _height(f) <= max_h],
        key=_height, reverse=True,
    )
    best_prog = prog[0] if prog else None
    best_vonly = vonly[0] if vonly else None
    best_aud = None
    if auds:
        best_aud = sorted(
            auds,
            key=lambda a: (str(a.get("extension")) == "m4a", a.get("bitrate") or 0),
            reverse=True,
        )[0]

    # HD: video-only + audio'ni birlashtirish (progressivedan yuqori bo'lsa)
    if best_vonly and best_aud and (not best_prog or _height(best_vonly) > _height(best_prog)):
        vpath, apath = out_path + ".v", out_path + ".a"
        try:
            _stream_to(best_vonly["url"], vpath)
            _stream_to(best_aud["url"], apath)
            proc = subprocess.run(
                ["ffmpeg", "-y", "-i", vpath, "-i", apath, "-c", "copy",
                 "-movflags", "+faststart", out_path],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            if proc.returncode == 0 and _ok(out_path):
                logger.info("RapidAPI: HD %dp + audio birlashtirildi", _height(best_vonly))
                return
            logger.warning("RapidAPI merge xato (kod %s) — progressive'ga o'tamiz", proc.returncode)
        except Exception as exc:
            logger.warning("RapidAPI HD xato (%s) — progressive'ga o'tamiz", str(exc)[:100])
        finally:
            for p in (vpath, apath):
                try:
                    os.remove(p)
                except OSError:
                    pass

    # Progressive (bitta fayl, audio bilan)
    if best_prog:
        _stream_to(best_prog["url"], out_path)
        if _ok(out_path):
            logger.info("RapidAPI: progressive %dp yuklandi", _height(best_prog))
            return

    raise RuntimeError("RapidAPI: yuklab olinadigan format topilmadi")
