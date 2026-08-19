"""Kino bot — kirish nuqtasi. aiogram polling + web-admin bitta loopda."""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

import config
import db
import handlers


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    log = logging.getLogger("kino")

    await db.init()
    log.info("PostgreSQL ulandi va sxema tayyor.")

    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Routerlar tartibi: callback, inline, user (start/menyu), admin (oxirida catch)
    dp.include_router(handlers.callbacks.router)
    dp.include_router(handlers.inline.router)
    dp.include_router(handlers.user.router)
    dp.include_router(handlers.admin.router)

    # Web-admin panel (ixtiyoriy)
    web_runner = None
    if config.WEB_ENABLED:
        from web.server import start_web
        web_runner = await start_web(bot)

    me = await bot.get_me()
    log.info("Bot ishga tushdi: @%s", me.username)

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        if web_runner:
            await web_runner.cleanup()
        await db.close()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
