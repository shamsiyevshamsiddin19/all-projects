import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from django.conf import settings

from .handlers import register_all_handlers
from .middlewares.auth import AuthMiddleware
from .middlewares.block_check import BlockCheckMiddleware
from .middlewares.logging_mw import LoggingMiddleware
from .middlewares.throttling import ThrottlingMiddleware

logger = logging.getLogger("bot")


def create_bot() -> Bot:
    return Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))


def create_dispatcher() -> Dispatcher:
    storage = RedisStorage.from_url(settings.REDIS_URL)
    dp = Dispatcher(storage=storage)

    dp.update.outer_middleware(ThrottlingMiddleware())
    dp.update.outer_middleware(AuthMiddleware())
    dp.update.outer_middleware(BlockCheckMiddleware())
    dp.update.outer_middleware(LoggingMiddleware())

    register_all_handlers(dp)
    return dp


async def run_polling():
    bot = create_bot()
    dp = create_dispatcher()
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Bot polling rejimida ishga tushdi")
    await dp.start_polling(bot)


async def setup_webhook():
    bot = create_bot()
    dp = create_dispatcher()
    webhook_url = f"{settings.BOT_WEBHOOK_BASE_URL.rstrip('/')}/bot/webhook/"
    await bot.set_webhook(webhook_url, secret_token=settings.BOT_WEBHOOK_SECRET, drop_pending_updates=True)
    logger.info("Webhook o'rnatildi: %s", webhook_url)
    return bot, dp
