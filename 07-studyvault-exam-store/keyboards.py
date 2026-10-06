"""Telegram klaviaturalar (reply + inline)."""
from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from services import telegram_bot_url


def reply_kb(items: list[str], back: bool = True, cols: int = 2) -> ReplyKeyboardMarkup:
    rows, row = [], []
    for it in items:
        row.append(KeyboardButton(text=it))
        if len(row) == cols:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    if back:
        rows.append([KeyboardButton(text="🔙 ORQAGA")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def user_menu() -> ReplyKeyboardMarkup:
    return reply_kb([
        "📚 FAN BAZALAR",
        "🔑 AKTIVLASHTIRISH KODINI OLISH",
        "📝 BUYURTMA BERISH",
        "🎁 TEKIN BAZA (REFERAL)",
    ], back=False, cols=1)


def admin_menu() -> ReplyKeyboardMarkup:
    return reply_kb([
        "BAZA QO'SHISH", "BAZA O'CHIRISH", "HAVOLALAR", "TAG SOZLAMALARI",
        "📢 OBUNA SOZLAMALARI", "👥 REFERALLAR", "REKLAMA", "STATISTIKA",
    ], back=False, cols=2)


def courses_kb() -> ReplyKeyboardMarkup:
    return reply_kb(["1-kurs", "2-kurs", "3-kurs", "4-kurs"], back=True, cols=2)


def click_invoice_kb(payment_url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💠 Click orqali to'lash", url=payment_url)],
        [InlineKeyboardButton(text="🎁 Referal orqali", callback_data="open_referral_section")],
    ])


def referral_kb(enough: bool) -> InlineKeyboardMarkup | None:
    if not enough:
        return None
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 5 BALL = 1 KOD (AVTO)", callback_data="get_free_code_auto")],
    ])


def subscription_kb(channels: list[dict]) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text="➕ " + ch["title"], url=ch["link"])] for ch in channels]
    rows.append([InlineKeyboardButton(text="✅ OBUNANI TASDIQLASH", callback_data="check_subs_btn")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def back_to_bot_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 Botga o'tish", url=telegram_bot_url())],
    ])
