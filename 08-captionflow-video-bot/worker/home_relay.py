"""Uy kompyuteri orqali video yuklab olish (YouTube/Instagram datacenter IP bloki uchun).

Muammo: Hetzner (datacenter) IP'dan YouTube/Instagram ko'p hollarda "Sign in to
confirm you're not a bot" yoki 403 bilan bloklaydi. Uy/mobil IP odatda bloklanmaydi.

Yechim: belgilangan admin(lar) yuborgan YouTube/Instagram havolalari uchun bot
serverda o'zi yuklamaydi — o'rniga "ish" (job) yaratadi va uy kompyuteridagi
`tools/home_relay_client.py` skripti (foydalanuvchi ishga tushiradi, doim ishlab
turadi) uni pull qilib, o'zi (uy IP'da) yt-dlp bilan yuklab, natijani serverga
yuklaydi (upload). Bu modul — shu ishlarning oddiy xotira-navbat (queue) qatlami
(bitta server jarayoni ichida, Redis shart emas — kam sonli, tez ishlar).
"""
from __future__ import annotations

import asyncio
import logging
import os
import threading
import time
import uuid
from typing import Awaitable, Callable

from config import settings

logger = logging.getLogger(__name__)

ProgressFn = Callable[[str], Awaitable[None]]

_LOCK = threading.Lock()
_JOBS: dict[str, dict] = {}
_MAX_JOBS = 200
_JOB_TTL = 3 * 3600  # 3 soat — eskirgan ishlarni tozalash


def _cleanup_locked() -> None:
    if len(_JOBS) <= _MAX_JOBS:
        return
    now = time.time()
    for jid in list(_JOBS):
        if now - _JOBS[jid]["created"] > _JOB_TTL:
            _JOBS.pop(jid, None)


def create_job(url: str) -> str:
    """Yangi yuklab olish ishi yaratadi. Qaytaradi: job_id."""
    job_id = uuid.uuid4().hex[:16]
    with _LOCK:
        _cleanup_locked()
        _JOBS[job_id] = {
            "url": url,
            "status": "pending",  # pending -> claimed -> done | error
            "path": None,
            "error": None,
            "created": time.time(),
        }
    return job_id


def claim_next() -> tuple[str, str] | None:
    """Klient (uy skripti) navbatdagi eng eski PENDING ishni oladi.

    Topilsa "claimed" deb belgilaydi (boshqa so'rov qayta olmasin) va
    (job_id, url) qaytaradi; bo'lmasa None."""
    with _LOCK:
        pending = [
            (jid, j) for jid, j in _JOBS.items() if j["status"] == "pending"
        ]
        if not pending:
            return None
        jid, j = min(pending, key=lambda kv: kv[1]["created"])
        j["status"] = "claimed"
        j["claimed_at"] = time.time()
        return jid, j["url"]


def complete_job(job_id: str, path: str) -> bool:
    with _LOCK:
        job = _JOBS.get(job_id)
        if not job:
            return False
        job["status"] = "done"
        job["path"] = path
        return True


def fail_job(job_id: str, error: str) -> bool:
    with _LOCK:
        job = _JOBS.get(job_id)
        if not job:
            return False
        job["status"] = "error"
        job["error"] = (error or "")[:500]
        return True


def get_status(job_id: str) -> dict | None:
    with _LOCK:
        job = _JOBS.get(job_id)
        return dict(job) if job else None


def discard(job_id: str) -> None:
    with _LOCK:
        _JOBS.pop(job_id, None)


def enabled() -> bool:
    return bool(settings.home_relay_secret) and bool(settings.home_relay_admin_id_set)


def is_relay_user(user_tg_id: int) -> bool:
    return enabled() and user_tg_id in settings.home_relay_admin_id_set


async def request_download(
    url: str, dest_path: str, progress: ProgressFn | None = None
) -> None:
    """Videoni uy kompyuteri orqali yuklab, dest_path ga qo'yadi.

    Ish yaratiladi va klient skript (tools/home_relay_client.py) uni pull
    qilishini kutamiz. HOME_RELAY_GRACE_SECONDS ichida hech kim olmasa
    (skript o'chiq) — xato tashlaymiz, chaqiruvchi (video.py) oddiy
    server-tomon yuklashga qaytadi. Olingandan keyin HOME_RELAY_TIMEOUT_SECONDS
    gacha natijani kutamiz (katta video uchun uzoqroq)."""
    job_id = create_job(url)
    if progress:
        await progress(
            "🖥 Havola kompyuteringiz orqali yuklanmoqda...\n"
            "(Kompyuteringiz yoqiq va dastur ishlab turgani kerak)"
        )

    grace = settings.home_relay_grace_seconds
    timeout = settings.home_relay_timeout_seconds
    start = time.monotonic()
    claimed = False
    downloading_notified = False

    try:
        while True:
            elapsed = time.monotonic() - start
            if elapsed > timeout:
                raise RuntimeError(
                    "Kompyuteringiz orqali yuklash vaqti tugadi (juda uzoq davom etdi)"
                )
            job = get_status(job_id)
            if job is None:
                raise RuntimeError("Yuklab olish ishi topilmadi (ichki xato)")

            status = job["status"]
            if status == "pending" and elapsed > grace:
                raise RuntimeError(
                    "Kompyuteringizdagi dastur javob bermayapti — ishga tushirilganini tekshiring"
                )
            if status == "claimed" and not claimed:
                claimed = True
                if progress and not downloading_notified:
                    downloading_notified = True
                    await progress("📥 Kompyuteringiz videoni yuklab olmoqda...")
            if status == "done":
                path = job["path"]
                if not path or not os.path.isfile(path):
                    raise RuntimeError("Yuklangan fayl topilmadi")
                os.makedirs(os.path.dirname(os.path.abspath(dest_path)), exist_ok=True)
                os.replace(path, dest_path)
                return
            if status == "error":
                raise RuntimeError(
                    f"Kompyuteringiz videoni yuklay olmadi: {job.get('error') or 'noma\'lum xato'}"
                )

            await asyncio.sleep(2.0)
    finally:
        discard(job_id)
