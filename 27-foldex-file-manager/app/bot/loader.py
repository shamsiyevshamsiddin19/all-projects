# -*- coding: utf-8 -*-
"""
Foldex Telegram Bot Loader moduli.
aiogram 3.x Bot va Dispatcher nusxalarini sozlaydi va ishga tushiradi.
"""

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.core.config import settings

# 1. Telegram Bot nusxasi
# Barcha xabarlarda sukut bo'yicha HTML formatlash ishlatiladi
# Agar BOT_TOKEN bo'sh bo'lsa, mahalliy testlar xatosiz o'tishi uchun formatli placeholder ishlatiladi
token_to_use = settings.BOT_TOKEN if settings.BOT_TOKEN and ":" in settings.BOT_TOKEN else "1234567890:AAH_mock_token_for_foldex_local_test_12345"
bot = Bot(
    token=token_to_use,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

# 2. Asinxron Dispatcher nusxasi (FSM holatlari xotirada saqlanadi)
dp = Dispatcher(storage=MemoryStorage())
