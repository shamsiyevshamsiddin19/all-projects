"""Kichik web-server: katta videolarni yuklab olish havolasi orqali beradi.

Telegram bot orqali 50MB dan katta fayl yuborib bo'lmaydi. Shu hollarda
tayyor video shu serverga qo'yiladi va foydalanuvchiga havola beriladi
(arxitektura: katta video / Mini App yo'nalishi).

Eslatma: havola foydalanuvchi qurilmasidan ochilishi uchun manzil
o'sha qurilmadan ko'rinishi kerak:
  - bir xil Wi-Fi: LAN IP avtomatik ishlatiladi
  - har joydan: serverga deploy + PUBLIC_BASE_URL=https://domen
"""
from __future__ import annotations

import asyncio
import logging
import os
import shutil
import socket
import time
import uuid

from aiohttp import web

from config import settings

logger = logging.getLogger(__name__)


def get_lan_ip() -> str:
    """Mahalliy tarmoq (LAN) IP manzilini aniqlaydi."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        sock.close()


def base_url() -> str:
    """Yuklab olish havolalari uchun asos manzil."""
    if settings.public_base_url:
        return settings.public_base_url.rstrip("/")
    return f"http://{get_lan_ip()}:{settings.web_port}"


def publish_file(src_path: str, suffix: str = ".mp4") -> str:
    """Faylni downloads papkasiga ko'chirib, yuklab olish havolasini qaytaradi."""
    os.makedirs(settings.download_dir, exist_ok=True)
    token = uuid.uuid4().hex
    dest = os.path.join(settings.download_dir, token + suffix)
    shutil.move(src_path, dest)
    return f"{base_url()}/dl/{token}{suffix}"


def internal_base_url() -> str:
    """Worker'lar kirish videoni oladigan to'g'ridan-to'g'ri manzil (tunnel emas)."""
    if settings.internal_base_url:
        return settings.internal_base_url.rstrip("/")
    return base_url()


def publish_input(src_path: str, suffix: str = ".mp4") -> str:
    """Kirish videoni NUSXALAB (asl fayl master worker uchun qoladi) ulashadi.

    Masofaviy worker shu havoladan videoni yuklab oladi. Master'ning o'z
    worker'i lokal asl fayldan foydalanadi (havola ishlatilmaydi).
    """
    if not src_path or not os.path.exists(src_path):
        return ""
    os.makedirs(settings.download_dir, exist_ok=True)
    token = uuid.uuid4().hex
    dest = os.path.join(settings.download_dir, token + suffix)
    shutil.copy(src_path, dest)
    return f"{internal_base_url()}/dl/{token}{suffix}"


async def _handle_internal_finish(request: web.Request) -> web.Response:
    """Masofaviy worker video statusini master DB'ga yozadi (umumiy sir bilan)."""
    if not settings.internal_secret:
        return web.Response(status=403, text="internal API o'chiq")
    try:
        data = await request.json()
    except Exception:
        return web.Response(status=400, text="bad json")
    if data.get("secret") != settings.internal_secret:
        return web.Response(status=403, text="forbidden")
    try:
        from db.crud import finish_video

        await finish_video(
            int(data["video_id"]),
            str(data.get("status") or "done"),
            error_message=(data.get("error") or None),
        )
    except Exception:
        logger.exception("internal finish xatosi")
        return web.Response(status=500, text="db xato")
    return web.json_response({"ok": True})


# ---------------------------------------------------------------------------
# Uy kompyuteri orqali yuklash (home relay) — worker/home_relay.py.
# YouTube/Instagram datacenter IP blokini chetlab o'tish uchun: belgilangan
# admin yuborgan havolalar uy kompyuteridagi skript (tools/home_relay_client.py)
# orqali yuklanadi. Bu 3 endpoint o'sha skript bilan gaplashadi.


def _home_relay_check(secret: str) -> web.Response | None:
    if not settings.home_relay_secret:
        return web.Response(status=403, text="home relay o'chiq")
    if secret != settings.home_relay_secret:
        return web.Response(status=403, text="forbidden")
    return None


async def _handle_home_pull(request: web.Request) -> web.Response:
    """Klient skript navbatdagi ishni so'raydi (bo'sh bo'lsa job_id=null)."""
    err = _home_relay_check(request.query.get("secret", ""))
    if err:
        return err
    from worker import home_relay

    job = home_relay.claim_next()
    if not job:
        return web.json_response({"job_id": None})
    job_id, url = job
    return web.json_response({"job_id": job_id, "url": url})


async def _handle_home_upload(request: web.Request) -> web.Response:
    """Klient skript yuklab olgan faylni shu yerga yuklaydi (multipart)."""
    err = _home_relay_check(request.query.get("secret", ""))
    if err:
        return err
    from worker import home_relay

    reader = await request.multipart()
    job_id = None
    dest_path = None
    field = await reader.next()
    while field is not None:
        if field.name == "job_id":
            job_id = (await field.read()).decode("utf-8").strip()
        elif field.name == "file":
            if not job_id:
                return web.Response(status=400, text="job_id avval kelishi kerak")
            os.makedirs(settings.work_dir, exist_ok=True)
            dest_path = os.path.join(settings.work_dir, f"home_{job_id}.mp4")
            with open(dest_path, "wb") as f:
                while True:
                    chunk = await field.read_chunk(1 << 20)
                    if not chunk:
                        break
                    f.write(chunk)
        field = await reader.next()

    if not job_id or not dest_path or not os.path.isfile(dest_path):
        return web.Response(status=400, text="fayl kelmadi")
    home_relay.complete_job(job_id, dest_path)
    logger.info("Home relay: job %s yuklandi (%s)", job_id, dest_path)
    return web.json_response({"ok": True})


async def _handle_home_fail(request: web.Request) -> web.Response:
    """Klient skript xato haqida xabar beradi (masalan yt-dlp muvaffaqiyatsiz)."""
    err = _home_relay_check(request.query.get("secret", ""))
    if err:
        return err
    from worker import home_relay

    try:
        data = await request.json()
    except Exception:
        return web.Response(status=400, text="bad json")
    job_id = str(data.get("job_id") or "")
    if not job_id:
        return web.Response(status=400, text="job_id yo'q")
    home_relay.fail_job(job_id, str(data.get("error") or "noma'lum xato"))
    return web.json_response({"ok": True})


async def _handle_download(request: web.Request) -> web.StreamResponse:
    name = os.path.basename(request.match_info["name"])  # path traversal himoyasi
    path = os.path.join(settings.download_dir, name)
    if not os.path.isfile(path):
        return web.Response(status=404, text="Fayl topilmadi yoki muddati o'tgan.")
    lower = name.lower()
    if lower.endswith(".srt"):
        fname = "subtitle.srt"
    elif lower.endswith(".txt"):
        fname = "subtitr-matn.txt"
    elif lower.endswith(".pdf"):
        fname = "subtitr.pdf"
    else:
        fname = "subtitled.mp4"
    # ?dl=1 -> majburiy yuklab olish; aks holda inline (Mini App video preview)
    disposition = "attachment" if request.query.get("dl") else "inline"
    return web.FileResponse(
        path,
        headers={"Content-Disposition": f'{disposition}; filename="{fname}"'},
    )


async def _cleanup_loop() -> None:
    """Eski yuklab olish fayllarini vaqti-vaqti bilan o'chiradi (TTL)."""
    ttl_seconds = settings.download_ttl_hours * 3600
    while True:
        try:
            now = time.time()
            folder = settings.download_dir
            if os.path.isdir(folder):
                for name in os.listdir(folder):
                    path = os.path.join(folder, name)
                    if os.path.isfile(path) and now - os.path.getmtime(path) > ttl_seconds:
                        try:
                            os.remove(path)
                        except OSError:
                            pass
        except Exception:
            logger.exception("Download cleanup xatosi")
        await asyncio.sleep(3600)


async def start_web(bot=None) -> None:
    """Web-serverni bot bilan bir loopda ishga tushiradi.

    bot berilsa, Click to'lov webhooklari ham ulanadi (to'lov tugaganda
    foydalanuvchiga xabar yuborish uchun bot kerak).
    """
    os.makedirs(settings.download_dir, exist_ok=True)
    # client_max_size — aiohttp standarti atigi 1MB. Mini App katta video
    # yuklashi uchun limitni oshiramiz (miniapp_max_mb + zaxira).
    max_body = (settings.miniapp_max_mb + 32) * 1024 * 1024
    app = web.Application(client_max_size=max_body)
    app.router.add_get("/dl/{name}", _handle_download)
    app.router.add_post("/internal/finish", _handle_internal_finish)
    app.router.add_get("/internal/home/pull", _handle_home_pull)
    app.router.add_post("/internal/home/upload", _handle_home_upload)
    app.router.add_post("/internal/home/fail", _handle_home_fail)

    if bot is not None:
        from web.click import setup_click_routes

        setup_click_routes(app, bot)

    from web.admin import setup_admin_routes
    from web.miniapp import cleanup_jobs_loop, setup_miniapp_routes

    setup_admin_routes(app, bot)
    setup_miniapp_routes(app)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=settings.web_port)
    await site.start()

    asyncio.create_task(_cleanup_loop())
    asyncio.create_task(cleanup_jobs_loop())
    logger.info("Web-server tayyor: %s (yuklab olish havolalari shu manzilda)", base_url())
    logger.info("Admin panel: %s/admin", base_url())
    logger.info("Mini App: %s/app", base_url())
