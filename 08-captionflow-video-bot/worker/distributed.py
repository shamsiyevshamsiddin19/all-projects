"""Taqsimlangan worker yordamchilari.

Masofaviy worker (boshqa serverda) master bilan ikki nuqtada ishlaydi:
  1) Kirish video master diskida — worker uni HTTP orqali yuklab oladi.
  2) DB master'da (SQLite) — worker statusni master'ga HTTP orqali yuboradi.

Master'ning o'z worker'ida (REMOTE_WORKER=0) bu modul ishlatilmaydi —
kirish fayl lokalda, DB ham lokalda.
"""
from __future__ import annotations

import logging
import os

import requests

from config import settings

logger = logging.getLogger(__name__)


def _master_base() -> str:
    """Worker -> master ichki API asos manzili."""
    if settings.master_url:
        return settings.master_url.rstrip("/")
    return f"http://127.0.0.1:{settings.web_port}"


def fetch_input(in_path: str, in_url: str) -> str:
    """Kirish video lokalda bo'lsa o'shani qaytaradi; aks holda in_url'dan yuklaydi.

    Master'ning o'z worker'ida fayl lokalda bo'ladi (tez yo'l). Masofaviy
    worker'da lokal fayl yo'q — master'dan to'g'ridan-to'g'ri yuklab olamiz.
    """
    if in_path and os.path.exists(in_path) and os.path.getsize(in_path) > 0:
        return in_path
    if not in_url:
        raise RuntimeError("Kirish video topilmadi (lokal fayl ham, URL ham yo'q)")
    os.makedirs(settings.work_dir, exist_ok=True)
    dest = in_path or os.path.join(
        settings.work_dir, os.path.basename(in_url.split("?")[0]) or "input.mp4"
    )
    logger.info("Masofaviy worker: kirish video yuklanmoqda %s", in_url)
    with requests.get(in_url, stream=True, timeout=180) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(1 << 16):
                if chunk:
                    f.write(chunk)
    if not os.path.exists(dest) or os.path.getsize(dest) == 0:
        raise RuntimeError("Kirish videoni master'dan yuklab bo'lmadi")
    return dest


def report_finish(video_db_id: int, status: str, error: str = "") -> bool:
    """Master'ga video yakuniy statusini yuboradi (DB master'da). True=ok."""
    url = _master_base() + "/internal/finish"
    try:
        resp = requests.post(
            url,
            json={
                "secret": settings.internal_secret,
                "video_id": video_db_id,
                "status": status,
                "error": (error or "")[:500],
            },
            timeout=20,
        )
        if resp.status_code != 200:
            logger.warning("Master status javobi %s: %s", resp.status_code, resp.text[:120])
        return resp.status_code == 200
    except Exception as exc:
        logger.warning("Master'ga status yuborilmadi (%s): %s", url, exc)
        return False
