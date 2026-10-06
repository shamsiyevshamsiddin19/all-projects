"""Barcha InlineKeyboard va ReplyKeyboard."""
from __future__ import annotations
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from config import settings, DOC_TYPES, LANGS


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Buyurtma berish"), KeyboardButton(text="🎁 Bepul namuna")],
            [KeyboardButton(text="📂 Mening buyurtmalarim"), KeyboardButton(text="👤 Profilim")],
            [KeyboardButton(text="🤝 Referal dastur"), KeyboardButton(text="💳 Hisobni to'ldirish")],
            [KeyboardButton(text="ℹ️ Yordam")],
        ],
        resize_keyboard=True,
    )


def samples_kb() -> InlineKeyboardMarkup:
    """Bepul namuna tanlash — to'lashдан oldin sifatni ko'rish."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📄 Referat namunasi", callback_data="sample:referat")],
        [InlineKeyboardButton(text="📝 Mustaqil ish namunasi", callback_data="sample:mustaqil")],
        [InlineKeyboardButton(text="📊 Slayd namunasi", callback_data="sample:slayd")],
        [InlineKeyboardButton(text="📝 Buyurtma berish", callback_data="new_order")],
    ])


def doc_types_kb() -> InlineKeyboardMarkup:
    buttons = []
    row = []
    for key, info in DOC_TYPES.items():
        price = settings.min_price(key)
        row.append(InlineKeyboardButton(
            text=f"{info['emoji']} {info['label']} — {price:,} so'm dan",
            callback_data=f"doctype:{key}",
        ))
        if len(row) == 1:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def language_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇺🇿 O'zbek", callback_data="lang:uz"),
            InlineKeyboardButton(text="🇷🇺 Rus", callback_data="lang:ru"),
            InlineKeyboardButton(text="🇬🇧 Ingliz", callback_data="lang:en"),
        ],
        [InlineKeyboardButton(text="◀️ Orqaga", callback_data="back:topic")],
    ])


def pages_kb(doc_type: str) -> InlineKeyboardMarkup:
    presets = {
        "tezis":    [(1, "Qisqa (1 bet)"), (2, "O'rta (2 bet)"), (3, "To'liq (3 bet)")],
        "mustaqil": [(5, "Minimal (5 bet)"), (7, "O'rtacha (7 bet)"), (10, "To'liq (10 bet)")],
        "referat":  [(8, "Qisqa (8 bet)"), (12, "O'rtacha (12 bet)"), (15, "To'liq (15 bet)")],
        "krasword": [(20, "20 so'z"), (30, "30 so'z"), (40, "40 so'z")],
        "maqola":   [(5, "Qisqa (5 bet)"), (10, "O'rtacha (10 bet)"), (15, "To'liq (15 bet)")],
        "slayd":    [(10, "10 slayd"), (15, "15 slayd"), (20, "20 slayd")],
        "kurs":     [(25, "Minimal (25 bet)"), (35, "O'rtacha (35 bet)"), (40, "To'liq (40 bet)")],
        "diplom":   [(50, "Minimal (50 bet)"), (65, "O'rtacha (65 bet)"), (80, "To'liq (80 bet)")],
    }
    opts = presets.get(doc_type, [(10, "O'rtacha"), (15, "Ko'p")])
    row = [InlineKeyboardButton(text=label, callback_data=f"pages:{val}")
           for val, label in opts]
    return InlineKeyboardMarkup(inline_keyboard=[row,
        [InlineKeyboardButton(text="◀️ Orqaga", callback_data="back:lang")],
    ])


def format_kb(doc_type: str) -> InlineKeyboardMarkup:
    if doc_type == "slayd":
        buttons = [[InlineKeyboardButton(text="📊 PPTX (Slayd)", callback_data="format:pptx")]]
    elif doc_type == "krasword":
        buttons = [[InlineKeyboardButton(text="🖼 PNG + 📄 DOCX", callback_data="format:png")]]
    else:
        buttons = [
            [
                InlineKeyboardButton(text="📄 DOCX (Word)", callback_data="format:docx"),
                InlineKeyboardButton(text="📋 PDF", callback_data="format:pdf"),
            ]
        ]
    buttons.append([InlineKeyboardButton(text="◀️ Orqaga", callback_data="back:count")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def payment_kb(balance: int, price: int, order_id: int, click_url: str) -> InlineKeyboardMarkup:
    buttons = []
    if balance >= price:
        buttons.append([InlineKeyboardButton(
            text=f"💰 Hisobdan to'lash ({balance:,} so'm dan)",
            callback_data=f"pay:balance:{order_id}",
        )])
    buttons.append([InlineKeyboardButton(
        text="💳 Click orqali to'lash",
        url=click_url,
    )])
    buttons.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"pay:cancel:{order_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def confirm_kb(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"confirm:{order_id}")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel")],
    ])


def order_done_kb(order_id: int, revisable: bool = True) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text="📥 Qayta yuklash", callback_data=f"redownload:{order_id}")]]
    if revisable:
        rows.append([InlineKeyboardButton(
            text="✏️ Qayta ishlash (bepul)", callback_data=f"revise:{order_id}")])
    rows.append([InlineKeyboardButton(text="🆕 Yangi buyurtma", callback_data="new_order")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def tier_kb(price: int, premium_price: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"⚡ Standart — {price:,} so'm", callback_data="tier:standard")],
        [InlineKeyboardButton(
            text=f"👑 Premium — {premium_price:,} so'm (kuchliroq AI)",
            callback_data="tier:premium")],
    ])


def otm_kb(prev_otm: str | None = None) -> InlineKeyboardMarkup:
    rows = []
    if prev_otm:
        rows.append([InlineKeyboardButton(
            text=f"🏛 {prev_otm[:40]}", callback_data="otm:prev")])
    rows.append([InlineKeyboardButton(text="⏭ O'tkazib yuborish", callback_data="otm:skip")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def rating_kb(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=f"{'⭐' * n}", callback_data=f"rate:{order_id}:{n}")
        for n in range(1, 6)
    ]])


def share_kb(bot_username: str, ref_code: str) -> InlineKeyboardMarkup:
    import urllib.parse
    link = f"https://t.me/{bot_username}?start=ref_{ref_code}"
    text = ("🎓 Referat, mustaqil ish, kurs ishi — jadval, grafik va formulalari "
            "bilan AI tayyorlab beradi. Men sinab ko'rdim, zo'r chiqdi! 👇")
    share_url = ("https://t.me/share/url?url=" + urllib.parse.quote(link)
                 + "&text=" + urllib.parse.quote(text))
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 Do'stlarga ulashish", url=share_url)],
    ])


def retry_kb(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Qayta urinish", callback_data=f"retry:{order_id}")],
    ])


def back_to_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="main_menu")],
    ])


def referral_kb(bot_username: str, ref_code: str) -> InlineKeyboardMarkup:
    link = f"https://t.me/{bot_username}?start=ref_{ref_code}"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 Ulashish", switch_inline_query=f"ref_{ref_code}")],
        [InlineKeyboardButton(text="🔗 Havolani nusxalash", callback_data=f"copy_ref:{ref_code}")],
    ])


def topup_amounts_kb() -> InlineKeyboardMarkup:
    amounts = [10_000, 20_000, 50_000, 100_000]
    row1 = [InlineKeyboardButton(text=f"{a:,} so'm", callback_data=f"topup:{a}") for a in amounts[:2]]
    row2 = [InlineKeyboardButton(text=f"{a:,} so'm", callback_data=f"topup:{a}") for a in amounts[2:]]
    return InlineKeyboardMarkup(inline_keyboard=[row1, row2,
        [InlineKeyboardButton(text="✏️ Boshqa miqdor", callback_data="topup_custom")],
        [InlineKeyboardButton(text="❌ Bekor", callback_data="cancel")],
    ])
