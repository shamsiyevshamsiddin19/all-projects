"""Inline rejim — @bot_username yozilganda chiroyli, rasmli ulashish kartasi.

Foydalanuvchi istalgan chatda @subtitle_srtbot deb yozsa — marketing kartasi
chiqadi; bossa rasm + matn + "Botni ochish" tugmasi bilan yuboriladi (viral).
Rasm: admin /setpromo bilan yuklaydi -> file_id DB'da saqlanadi (doimiy).
"""
from __future__ import annotations

import logging
import time

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQuery,
    InlineQueryResultArticle,
    InlineQueryResultCachedPhoto,
    InputTextMessageContent,
    Message,
)

from config import settings
from db.crud import get_settings_map, set_setting

logger = logging.getLogger(__name__)
router = Router()

BOT_USERNAME = "subtitle_srtbot"  # main.py haqiqiysiga yangilaydi
_PROMO_KEY = "promo_photo_id"


def _bot_link() -> str:
    return f"https://t.me/{BOT_USERNAME}"


def _caption() -> str:
    return (
        "🎬 <b>Subtitr Bot</b>\n"
        "<i>Istalgan videoga AI subtitr — bir necha soniyada!</i>\n\n"
        "<b>Rejimlar:</b>\n"
        "<blockquote>"
        "📝 <b>Original</b> — videoni asl tilida subtitr qiladi\n"
        "🌐 <b>Tarjima</b> — boshqa tilga o'girib subtitr yozadi\n"
        "📑 <b>Ikki qatlam</b> — asl + tarjima birga ko'rinadi\n"
        "📄 <b>SRT fayl</b> — o'zingiz tahrirlaysiz\n"
        "📜 <b>Matn</b> — videodagi barcha gaplar (PDF/txt)\n"
        "📚 <b>Lug'at</b> — so'zlar va tarjimasi (PDF/txt)"
        "</blockquote>\n"
        "🗣 <b>Tillar:</b> o'zbek · rus · ingliz\n"
        "⚡ <b>Manba:</b> YouTube · Instagram · Telegram\n\n"
        "🎁 <b>Har oy BEPUL</b> — hoziroq sinab ko'ring!\n"
        f"👉 @{BOT_USERNAME}"
    )


def _keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🚀 Botni ochish", url=_bot_link()),
    ]])


# Promo rasm file_id keshи (DB'ni har so'rovда o'qimaslik uchun, 60s)
_promo = {"id": None, "ts": 0.0}


async def _promo_photo_id() -> str | None:
    now = time.time()
    if now - _promo["ts"] > 60:
        try:
            m = await get_settings_map()
            _promo["id"] = m.get(_PROMO_KEY) or None
        except Exception:
            pass
        _promo["ts"] = now
    return _promo["id"]


@router.inline_query()
async def inline_share(query: InlineQuery) -> None:
    """@bot yozilganda ulashish kartasi (rasm bo'lsa rasmli, bo'lmasa matnli)."""
    results: list = []
    photo_id = await _promo_photo_id()
    if photo_id:
        # Rasm bor — FAQAT rasmli karta (rasm + matn + tugma)
        results.append(InlineQueryResultCachedPhoto(
            id="promo_photo",
            photo_file_id=photo_id,
            title="Subtitr Bot — do'stlarga ulashing",
            caption=_caption(),
            parse_mode="HTML",
            reply_markup=_keyboard(),
        ))
    else:
        # Rasm hali yo'q — matnli zaxira karta
        results.append(InlineQueryResultArticle(
            id="promo_text",
            title="🎬 Subtitr Bot — do'stlarga ulashing",
            description="Videoga AI subtitr: tarjima · SRT · matn · lug'at. Bepul!",
            input_message_content=InputTextMessageContent(
                message_text=_caption(),
                parse_mode="HTML",
                disable_web_page_preview=False,
            ),
            reply_markup=_keyboard(),
        ))
    try:
        await query.answer(results, cache_time=30, is_personal=False)
    except Exception:
        logger.warning("inline javob xatosi", exc_info=True)


@router.message(Command("setpromo"))
async def cmd_setpromo(message: Message) -> None:
    """Admin: promo rasmni o'rnatadi. Rasmni caption '/setpromo' bilan yuboring
    yoki rasmga reply qilib /setpromo yozing."""
    if message.from_user.id not in settings.admin_id_set:
        return
    photo = message.photo or (message.reply_to_message.photo if message.reply_to_message else None)
    if not photo:
        await message.answer(
            "🖼 Promo rasmni <b>caption</b>ига <code>/setpromo</code> yozib yuboring "
            "(yoki rasmga reply qilib).", parse_mode="HTML",
        )
        return
    file_id = photo[-1].file_id  # eng katta o'lcham
    await set_setting(_PROMO_KEY, file_id)
    _promo["ts"] = 0.0  # keshни yangilatamiz
    await message.answer(
        "✅ Promo rasm o'rnatildi! Endi istalgan chatда "
        f"<code>@{BOT_USERNAME}</code> yozib sinab ko'ring.", parse_mode="HTML",
    )
