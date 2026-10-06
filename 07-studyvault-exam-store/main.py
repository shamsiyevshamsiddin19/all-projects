"""Sessiya tayyorgarlik bot — ishga tushirish.

Bot polling bilan ishlaydi (webhook shart emas). Yon tomonda Click ko'prik
API (aiohttp) ishlaydi — eski server PHP shu yerga BAZA_ to'lovlarni uzatadi.
"""
from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiohttp import web

import db
from bot import router
from click_api import setup_click_routes
from config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    settings.validate()
    await db.init()

    bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    # Web-server: Click ko'prik + admin panel (nginx 127.0.0.1:web_port ga proxy qiladi)
    app = web.Application()
    setup_click_routes(app, bot)
    from admin_web import setup_admin_routes
    setup_admin_routes(app, bot)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host=settings.web_host, port=settings.web_port)
    await site.start()
    logger.info("Click ko'prik API tayyor: %s:%s", settings.web_host, settings.web_port)

    dp = Dispatcher()
    dp.include_router(router)

    me = await bot.get_me()
    logger.info("Bot ishga tushdi: @%s", me.username)
    await bot.delete_webhook(drop_pending_updates=False)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi")
