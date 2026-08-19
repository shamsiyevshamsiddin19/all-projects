"""Minimal yuklab olish serveri — MASOFAVIY worker uchun.

Masofaviy worker katta (>49MB) natija videoni Telegramga yubora olmaydi,
shuning uchun o'z diskidan havola orqali beradi. Bu server faqat /dl/ ni
ochadi (DB, bot, miniapp kerak emas — yengil).

Ishga tushirish:  python -m web.dlserver
PUBLIC_BASE_URL=http://<worker_public_ip>:8080 bo'lishi kerak (.env da).
"""
from __future__ import annotations

import asyncio
import logging
import os

from aiohttp import web

from config import settings
from web.server import _cleanup_loop, _handle_download

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


async def main() -> None:
    os.makedirs(settings.download_dir, exist_ok=True)
    app = web.Application()
    app.router.add_get("/dl/{name}", _handle_download)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=settings.web_port)
    await site.start()
    asyncio.create_task(_cleanup_loop())
    logger.info("Worker dl-server tayyor: 0.0.0.0:%s", settings.web_port)
    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("dl-server to'xtatildi")
