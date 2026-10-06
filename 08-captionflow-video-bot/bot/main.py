"""Botni ishga tushirish nuqtasi.

Ishga tushirish (loyiha ildizidan):
    python -m bot.main
"""
from __future__ import annotations

import asyncio
import logging

from aiogram import Dispatcher, F
from aiogram.types import (
    BotCommand,
    BotCommandScopeAllGroupChats,
    BotCommandScopeAllPrivateChats,
)

from config import settings
from tg_session import make_bot
from bot.handlers import admin, donate, feedback, inline, start, subscribe, tts, video
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

    # Uzunroq timeout — katta tayyor videolarni Telegramga yuklash uchun.
    # local_bot_api sozlangan bo'lsa — o'z serverimizdagi telegram-bot-api (2GB).
    bot = make_bot()
    if settings.local_bot_api:
        logger.info("Local Bot API server ishlatilmoqda: %s", settings.local_bot_api)
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
        # Inline rejim ulashish kartasi uchun bot username
        if username:
            inline.BOT_USERNAME = username
    except Exception:
        logger.warning("Bot username olinmadi")

    # Marketing tavsiflari — havola yuborilganda/bot ochilganda ko'rinadi
    try:
        await bot.set_my_short_description(
            short_description=(
                "🎬 Videoga AI subtitr: tarjima, SRT, matn, lug'at. "
                "O'zbek · rus · ingliz. YouTube, Instagram, Telegram. Har oy bepul!"
            )
        )
        await bot.set_my_description(
            description=(
                "🎬 Subtitr Bot — istalgan videoga aqlli AI subtitr yozadi.\n\n"
                "✅ Original subtitr (o'zbek · rus · ingliz)\n"
                "🌐 Boshqa tilga tarjima\n"
                "📑 Ikki qatlam (asl + tarjima)\n"
                "📄 SRT fayl\n"
                "📜 Videodagi barcha matn (PDF/txt)\n"
                "📚 Lug'at — so'zlar + tarjima\n\n"
                "⚡ YouTube, Instagram, Telegram videolari\n"
                "🎁 Har oy bepul!\n\n"
                "Video yoki havola yuboring — darrov subtitr olasiz."
            )
        )
        logger.info("Bot marketing tavsiflari o'rnatildi")
    except Exception:
        logger.warning("Bot tavsiflarini o'rnatib bo'lmadi")

    # Buyruqlar menyusi FAQAT shaxsiy chatda; guruhlarda buyruq ko'rinmaydi
    try:
        await bot.set_my_commands(
            [
                BotCommand(command="start", description="🎬 Boshlash"),
                BotCommand(command="app", description="📲 Mini App (katta video)"),
                BotCommand(command="subscribe", description="💎 Obuna olish"),
                BotCommand(command="profile", description="👤 Mening profilim"),
                BotCommand(command="invite", description="🎁 Do'st taklif qilish (bepul video)"),
                BotCommand(command="donate", description="☕ Homiylik"),
                BotCommand(command="donors", description="🏆 Homiylar ro'yxati"),
                BotCommand(command="feedback", description="💬 Fikr bildirish"),
                BotCommand(command="tts", description="🔊 Matnni ovozga aylantirish"),
                BotCommand(command="help", description="❓ Yordam"),
            ],
            scope=BotCommandScopeAllPrivateChats(),
        )
        # Guruhlarda hech qanday buyruq ko'rinmasin
        await bot.delete_my_commands(scope=BotCommandScopeAllGroupChats())
        logger.info("Buyruqlar menyusi (faqat shaxsiy chat) o'rnatildi")
    except Exception:
        logger.warning("Buyruqlar menyusini o'rnatib bo'lmadi")

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
    # Bot guruhlarda JIM tursin — barcha xabar handlerlari faqat shaxsiy chatda
    # ishlaydi (inline rejim hamma joyda ishlayveradi — u xabar emas).
    dp.message.filter(F.chat.type == "private")
    dp.include_router(start.router)
    dp.include_router(admin.router)
    dp.include_router(subscribe.router)
    dp.include_router(donate.router)
    dp.include_router(feedback.router)
    # tts.router video.router'dan OLDIN: video.py'ning on_other_text handleri
    # holatsiz (har qanday matnni) ushlaydi — tts FSM holatidagi matn shu
    # yerga yetib bormasdan oldin ushlanishi kerak.
    dp.include_router(tts.router)
    dp.include_router(inline.router)
    dp.include_router(video.router)

    # Avtomatik holat kuzatuvi (ogohlantirish + kunlik hisobot)
    from bot.monitor import monitor_loop

    asyncio.create_task(monitor_loop(bot))

    logger.info("Bot ishga tushdi. To'xtatish: Ctrl+C")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.getLogger(__name__).info("Bot to'xtatildi")
