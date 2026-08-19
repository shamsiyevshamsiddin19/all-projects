import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web
from web.admin import setup_admin_app

from core.config import BOT_TOKEN
from core.database import db
from handlers import user_handlers, file_handlers

async def main():
    logging.basicConfig(level=logging.INFO)

    # Initialize Bot and Dispatcher
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    # Connect Database
    await db.connect()

    # Include routers
    dp.include_router(user_handlers.router)
    dp.include_router(file_handlers.router)

    # Start web server (admin panel lives on the site, not in the bot)
    admin_app = setup_admin_app(bot)
    runner = web.AppRunner(admin_app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8085)
    await site.start()
    print("Admin panel started on port 8085")

    # Start polling
    print("Bot is starting...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
