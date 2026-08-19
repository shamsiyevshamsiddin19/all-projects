"""Inline klaviaturalar."""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Barcha rejimlar (tartib bilan). Qulflanganlariga 🔒 qo'shiladi.
_ALL_MODES = ("original", "translate", "dual", "srt", "transcript", "vocabulary")

_MODE_LABELS = {
    "original": "📝 Original — asl tilda subtitr",
    "translate": "🌐 Tarjima — boshqa tilga o'giradi",
    "dual": "📑 Ikki qatlam — asl + tarjima",
    "srt": "📄 .SRT fayl — o'zingiz tahrirlang",
    "transcript": "📜 Matn — barcha gaplar (txt/docx)",
    "vocabulary": "📚 Lug'at — so'zlar + tarjima (txt/docx)",
}


def mode_keyboard(allowed_modes: tuple[str, ...]) -> InlineKeyboardMarkup:
    """Barcha rejim tugmalari (bittasini tanlash). Tarifda yo'q rejimlar 🔒
from __future__ import annotations

    bilan ko'rsatiladi (bosilsa obuna taklif qilinadi)."""
    rows = []
    for m in _ALL_MODES:
        label = _MODE_LABELS[m]
        if m not in allowed_modes:
            label = "🔒 " + label
        rows.append([InlineKeyboardButton(text=label, callback_data=f"mode:{m}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def language_keyboard() -> InlineKeyboardMarkup:
    """Manba (asl) tilni tanlash — original/.srt uchun."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇷🇺 Ruscha", callback_data="lang:ru"),
                InlineKeyboardButton(text="🇬🇧 Inglizcha", callback_data="lang:en"),
            ],
            [
                InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang:uz"),
            ],
            [
                InlineKeyboardButton(
                    text="🔄 Avtomatik (AI aniqlaydi)", callback_data="lang:auto"
                ),
            ],
        ]
    )


def target_lang_keyboard() -> InlineKeyboardMarkup:
    """Tarjima tilini tanlash — translate/dual uchun (auto yo'q)."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang:uz"),
                InlineKeyboardButton(text="🇷🇺 Ruscha", callback_data="lang:ru"),
            ],
            [
                InlineKeyboardButton(text="🇬🇧 Inglizcha", callback_data="lang:en"),
            ],
        ]
    )
