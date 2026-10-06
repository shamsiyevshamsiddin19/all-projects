"""Barcha klaviaturalar (reply va inline)."""
import math

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

import config


def _rows(items, per_row=2):
    row, out = [], []
    for it in items:
        row.append(KeyboardButton(text=str(it)))
        if len(row) == per_row:
            out.append(row)
            row = []
    if row:
        out.append(row)
    return out


def reply_kb(items, back=True, per_row=2) -> ReplyKeyboardMarkup:
    kb = _rows(items, per_row)
    if back:
        kb.append([KeyboardButton(text="ORQAGA")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="KOD BILAN QIDIRISH")],
            [KeyboardButton(text="KINOLAR"), KeyboardButton(text="SERIALLAR")],
            [KeyboardButton(text="QIDIRISH"), KeyboardButton(text="REYTING VA KODLAR")],
            [KeyboardButton(text="🎲 TASODIFIY KINO")],
        ],
        resize_keyboard=True,
    )


def admin_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="KINO QO'SHISH"), KeyboardButton(text="SERIAL QO'SHISH")],
            [KeyboardButton(text="KINO NOMINI O'ZGARTIRISH"), KeyboardButton(text="SERIAL NOMINI O'ZGARTIRISH")],
            [KeyboardButton(text="O'CHIRISH"), KeyboardButton(text="REKLAMA")],
            [KeyboardButton(text="OBUNA SOZLAMALARI"), KeyboardButton(text="MANBA SOZLAMALARI")],
            [KeyboardButton(text="IJTIMOIY TARMOQLAR"), KeyboardButton(text="STATISTIKA")],
            [KeyboardButton(text="CHIQISH")],
        ],
        resize_keyboard=True,
    )


def series_episodes_kb(episodes) -> ReplyKeyboardMarkup:
    kb = [[KeyboardButton(text="ORQAGA"), KeyboardButton(text="BARCHA QISMLAR")]]
    row = []
    for ep in episodes:
        row.append(KeyboardButton(text=f"{ep}-qism"))
        if len(row) == 4:
            kb.append(row)
            row = []
    if row:
        kb.append(row)
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def web_buttons(name: str) -> InlineKeyboardMarkup:
    from urllib.parse import quote
    google = "https://www.google.com/search?q=" + quote(f"{name} o'zbek tilida skachat")
    rows = [[InlineKeyboardButton(text="🔎 Google (O'zbekcha)", url=google)]]
    if config.SUPPORT_GROUP:
        rows.append([InlineKeyboardButton(text="🗣 Guruhdan so'rash", callback_data="ask_group")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def sub_message_kb(missing) -> InlineKeyboardMarkup:
    import db
    rows = [[InlineKeyboardButton(text=m["text"], url=m["url"])] for m in missing]

    socials = await db.fetch("SELECT platform, url FROM social_links")
    social_row = []
    for s in socials:
        social_row.append(InlineKeyboardButton(text=s["platform"], url=s["url"]))
        if len(social_row) == 2:
            rows.append(social_row)
            social_row = []
    if social_row:
        rows.append(social_row)

    rows.append([InlineKeyboardButton(text="✅ TASDIQLASH", callback_data="check_sub")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ---- Admin ro'yxat (pagination) klaviaturasi ----
def list_keyboard(items, page: int, per_page: int = 20):
    total = len(items)
    total_pages = max(1, math.ceil(total / per_page))
    page = max(0, min(page, total_pages - 1))
    current = items[page * per_page: page * per_page + per_page]

    kb, row = [], []
    for it in current:
        row.append(KeyboardButton(text=str(it)))
        if len(row) == 2:
            kb.append(row)
            row = []
    if row:
        kb.append(row)

    nav = []
    if page > 0:
        nav.append(KeyboardButton(text="⬅️ ORQAGA"))
    nav.append(KeyboardButton(text="🔎 QIDIRISH"))
    if page < total_pages - 1:
        nav.append(KeyboardButton(text="➡️ KEYINGI"))
    kb.append(nav)
    kb.append([KeyboardButton(text="🏠 MENYU")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True), page, total_pages
