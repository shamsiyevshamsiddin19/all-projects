"""Quiz bot — kirish nuqtasi. Telegram bot (polling) + web admin panelni birga yuritadi."""
from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand
from aiohttp import web

import bot as bot_handlers
import db
from config import settings
from web import admin_web

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("main")


async def _set_commands(bot: Bot) -> None:
    await bot.set_my_commands([
        BotCommand(command="start", description="Bosh menyu"),
        BotCommand(command="testlar", description="Testlar ro'yxati"),
        BotCommand(command="reyting", description="Eng yaxshi natijalar"),
        BotCommand(command="profil", description="Profilim: daraja, streak, nishonlar"),
        BotCommand(command="natijalarim", description="Natijalarim tarixi"),
        BotCommand(command="sevimli", description="Sevimli testlar"),
        BotCommand(command="yaratish", description="Test yaratish"),
        BotCommand(command="stop", description="Joriy testni to'xtatish"),
    ])


async def _start_web(bot: Bot) -> web.AppRunner:
    app = web.Application()
    admin_web.setup_admin_routes(app, bot)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, settings.WEB_HOST, settings.WEB_PORT)
    await site.start()
    log.info("Web admin panel: http://%s:%s/admin", settings.WEB_HOST, settings.WEB_PORT)
    return runner


async def main() -> None:
    await db.init()
    log.info("PostgreSQL ulandi.")

    bot = Bot(token=settings.BOT_TOKEN,
              default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    bot_handlers.register(dp, bot)

    await _set_commands(bot)
    runner = await _start_web(bot)
    log.info("Bot ishga tushdi (@%s).", settings.BOT_USERNAME)
    try:
        await dp.start_polling(bot)
    finally:
        await runner.cleanup()
        await db.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        log.info("To'xtatildi.")
