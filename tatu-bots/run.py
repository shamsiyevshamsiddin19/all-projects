"""tatulmsbot kirish nuqtasi.
   Ishga tushirish:  python run.py
"""
from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand
from aiohttp import web

from core import db
from core.config import settings
from bots import inline, lms_bot
from bots.admin_web import make_admin_app
from bots.scheduler import start_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("run")

COMMANDS = [
    BotCommand(command="start", description="Boshlash"),
    BotCommand(command="menu", description="Asosiy menyu"),
    BotCommand(command="login", description="LMS hisobiga kirish"),
    BotCommand(command="logout", description="Hisobdan chiqish"),
    BotCommand(command="help", description="Yordam"),
]


async def main():
    if not settings.lms_bot_token:
        raise SystemExit("LMS_BOT_TOKEN o'rnatilmagan (.env)")
    if not settings.fernet_key:
        raise SystemExit("FERNET_KEY o'rnatilmagan (.env)")

    await db.init()

    bot = Bot(settings.lms_bot_token,
              default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(lms_bot.router)
    dp.include_router(inline.router)

    start_scheduler(bot)

    # Admin web (master sayt /tatulms/ ostida proxy qiladi)
    runner = web.AppRunner(make_admin_app(bot))
    await runner.setup()
    site = web.TCPSite(runner, settings.web_host, settings.web_port)
    await site.start()
    log.info("Admin web: http://%s:%d%s/admin", settings.web_host, settings.web_port, "/tatulms")

    me = await bot.get_me()
    log.info("Bot ishga tushdi: @%s", me.username)
    await bot.set_my_commands(COMMANDS)
    await bot.delete_webhook(drop_pending_updates=True)
    try:
        await dp.start_polling(bot)
    finally:
        await runner.cleanup()
        await db.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
