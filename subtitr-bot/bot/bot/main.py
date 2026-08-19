"""Botni ishga tushirish nuqtasi.

Ishga tushirish (loyiha ildizidan):
    python -m bot.main
"""
from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession

from config import settings
from bot.handlers import admin, donate, start, subscribe, video
from web.server import start_web
from db.base import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    settings.validate()
    await init_db()

    # Uzunroq timeout — katta tayyor videolarni Telegramga yuklash uchun
    session = AiohttpSession(timeout=settings.bot_request_timeout)
    bot = Bot(token=settings.bot_token, session=session)
    await start_web(bot)  # Click webhooklari uchun bot kerak

    # Bot username — Mini App Profil bo'limidagi obuna/donat tugmalari uchun
    # va bot instansi — Mini App "Chatga yuborish" tugmasi uchun
    try:
        import web.miniapp as _miniapp
        import worker.pipeline as _pipeline

        _miniapp.BOT = bot
        username = (await bot.get_me()).username or ""
        _miniapp.BOT_USERNAME = username
        # PDF suvbelgisi uchun bot brendi (@username)
        _pipeline.BOT_BRAND = f"@{username}" if username else ""
    except Exception:
        logger.warning("Bot username olinmadi")

    # Mini App'ni chat menyu tugmasiga qo'yamiz (Telegram web_app HTTPS talab qiladi)
    if settings.public_base_url.startswith("https"):
        from aiogram.types import MenuButtonWebApp, WebAppInfo

        try:
            await bot.set_chat_menu_button(
                menu_button=MenuButtonWebApp(
                    text="Mini App",
                    web_app=WebAppInfo(url=f"{settings.public_base_url.rstrip('/')}/app"),
                )
            )
            logger.info("Mini App chat menyu tugmasi o'rnatildi")
        except Exception:
            logger.warning("Chat menyu tugmasini o'rnatib bo'lmadi")

    dp = Dispatcher()
    dp.include_router(start.router)
    dp.include_router(admin.router)
    dp.include_router(subscribe.router)
    dp.include_router(donate.router)
    dp.include_router(video.router)

    logger.info("Bot ishga tushdi. To'xtatish: Ctrl+C")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.getLogger(__name__).info("Bot to'xtatildi")
