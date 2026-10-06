"""Mustaqil Ish Bot — kirish nuqtasi."""
from __future__ import annotations
import asyncio
import logging
import os

try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    pass

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import settings, apply_overrides
from db.crud import create_tables, load_settings, recover_stuck_orders
from bot.router import build_router
from bot.middlewares.user import UserMiddleware
from bot.middlewares.throttle import ThrottleMiddleware
from web.app import run_web

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    os.makedirs(settings.tmp_dir, exist_ok=True)

    await create_tables()
    logger.info("✅ DB jadvallar tayyor")

    # Admin paneldan o'rnatilgan narx/bonus sozlamalarini yuklash
    apply_overrides(await load_settings())
    logger.info("✅ Sozlamalar yuklandi")

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())
    # Throttle (spam) — UserMiddleware'dan oldin (ban'lanmaganlar uchun ham)
    dp.message.middleware(ThrottleMiddleware())
    dp.callback_query.middleware(ThrottleMiddleware())
    dp.message.middleware(UserMiddleware())
    dp.callback_query.middleware(UserMiddleware())

    router = build_router()
    dp.include_router(router)

    web_runner = await run_web(bot)
    logger.info("✅ Web server port %d da ishga tushdi", settings.web_port)

    # Restartda osilib qolgan buyurtmalarni qaytarish va foydalanuvchini ogohlantirish
    try:
        stuck = await recover_stuck_orders()
        for o in stuck:
            logger.warning("Osilgan buyurtma #%s qaytarildi (%s so'm)", o["order_id"], o["price"])
            try:
                await bot.send_message(
                    o["user_id"],
                    f"♻️ <b>Uzr — texnik uzilish yuz berdi.</b>\n"
                    f"«{o['topic'][:60]}» buyurtmangiz yakunlanmadi.\n"
                    f"💰 <b>{o['price']:,} so'm</b> balansingizga qaytarildi.\n"
                    "Iltimos, qaytadan buyurtma bering — endi ishlaydi.",
                    parse_mode="HTML",
                )
            except Exception:
                pass
        if stuck and settings.admin_ids:
            for aid in settings.admin_ids:
                try:
                    await bot.send_message(
                        aid, f"♻️ Restartda {len(stuck)} ta osilgan buyurtma qaytarildi.")
                except Exception:
                    pass
    except Exception as e:
        logger.error("Osilgan buyurtmalarni tiklashda xato: %s", e)

    try:
        logger.info("🤖 Bot ishga tushdi: @%s", settings.bot_username)
        await dp.start_polling(bot, drop_pending_updates=True)
    finally:
        await web_runner.cleanup()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
