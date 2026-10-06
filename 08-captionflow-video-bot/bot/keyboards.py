"""Inline klaviaturalar."""
from __future__ import annotations
import os
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Barcha rejimlar (tartib bilan). Qulflanganlariga 🔒 qo'shiladi.
_ALL_MODES = (
    "original", "translate", "dual", "dual_vocab", "srt",
    "transcript", "vocabulary", "audio",
)
# Boshqa modullar uchun ochiq nom (video.py rejimlar ro'yxatini shu orqali oladi)
ALL_MODES = _ALL_MODES

_MODE_LABELS = {
    "original": "📝 Original — asl tilda subtitr",
    "translate": "🌐 Tarjima — boshqa tilga o'giradi",
    "dual": "📑 Ikki qatlam — asl + tarjima",
    "dual_vocab": "🎓 Ikki qatlam + lug'at — til o'rganish",
    "srt": "📄 .SRT fayl — o'zingiz tahrirlang",
    "transcript": "📜 Matn — barcha gaplar (txt/PDF)",
    "vocabulary": "📚 Lug'at — so'zlar + tarjima (txt/PDF)",
    "audio": "🎵 Audio — videodan ovoz (MP3)",
}


def mode_keyboard(allowed_modes: tuple[str, ...]) -> InlineKeyboardMarkup:
    """Barcha rejim tugmalari (bittasini tanlash). Tarifda yo'q rejimlar 🔒
    bilan ko'rsatiladi (bosilsa obuna taklif qilinadi)."""
    rows = []
    for m in _ALL_MODES:
        label = _MODE_LABELS[m]
        if m not in allowed_modes:
            label = "🔒 " + label
        rows.append([InlineKeyboardButton(text=label, callback_data=f"mode:{m}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# Rejim kartasi — rasm+tavsif orqali batafsil ko'rsatish uchun (mode_card_keyboard).
_ASSETS_MODES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "modes"
)

_MODE_INFO = {
    "original": (
        "📝 Original subtitr",
        "Video aynan gapirilgan tilda — asl matn subtitr sifatida ekranga "
        "chiqadi. Tarjima yo'q, faqat aniq matn.",
    ),
    "translate": (
        "🌐 Tarjima",
        "Video butunlay boshqa tilga tarjima qilinib, subtitr sifatida "
        "videoga kuydiriladi (o'zbek, rus yoki ingliz).",
    ),
    "dual": (
        "📑 Ikki qatlam",
        "Ekranda ikkita qator birga: yuqorida asl matn, pastda tarjima. "
        "Ikkala tilni bir vaqtda ko'rish uchun qulay.",
    ),
    "dual_vocab": (
        "🎓 Ikki qatlam + lug'at",
        "Ikki qatlam subtitr + gapirilayotgan so'zlarning tarjimasi ekran "
        "chetida suzib chiqadi. Til o'rganish uchun eng zo'r rejim!",
    ),
    "srt": (
        "📄 .SRT fayl",
        "Video kuydirilmaydi — alohida subtitr fayli (.srt) beriladi, "
        "istalgan pleyer yoki muharrirga qo'yasiz.",
    ),
    "transcript": (
        "📜 Matn (PDF/TXT)",
        "Videodagi barcha gaplar toza matn holida — PDF va TXT formatda, "
        "tarjima bilan yoki tarjimasiz.",
    ),
    "vocabulary": (
        "📚 Lug'at",
        "Videodagi so'zlar ro'yxati tarjimasi va chastotasi bilan — "
        "PDF/TXT fayl, til o'rganish uchun.",
    ),
    "audio": (
        "🎵 Audio (MP3)",
        "Videodan faqat sifatli ovoz (MP3) ajratib beradi — subtitr yo'q, "
        "eng tez va eng arzon.",
    ),
}


def mode_photo_path(mode: str) -> str:
    """Rejim uchun preview rasm yo'li (assets/modes/<mode>.png)."""
    return os.path.join(_ASSETS_MODES_DIR, f"{mode}.png")


def mode_caption(mode: str, index: int, total: int) -> str:
    """Rejim kartasi ostidagi matn (nom + tavsif + N/jami)."""
    title, desc = _MODE_INFO.get(mode, (mode, ""))
    return f"<b>{title}</b>\n\n{desc}\n\n<i>Rejim {index + 1}/{total}</i>"


def mode_card_keyboard(modes: tuple[str, ...], index: int) -> InlineKeyboardMarkup:
    """Rejim kartasi klaviaturasi: navigatsiya (oldingi/keyingi rejim) bitta
    qatorda yonma-yon, tanlash tugmasi alohida qatorda (pastroqda)."""
    n = len(modes)
    prev_i = (index - 1) % n
    next_i = (index + 1) % n
    mode = modes[index]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="◀️ Oldingi rejim", callback_data=f"modenav:{prev_i}"),
                InlineKeyboardButton(text="Keyingi rejim ▶️", callback_data=f"modenav:{next_i}"),
            ],
            [InlineKeyboardButton(text="✅ Shu rejimni tanlash", callback_data=f"mode:{mode}")],
        ]
    )


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


def transcript_lang_keyboard() -> InlineKeyboardMarkup:
    """Matn rejimi — asl tilda yoki tarjima tilini tanlash."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📄 Asl tilda (tarjimasiz)", callback_data="lang:none")],
            [
                InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang:uz"),
                InlineKeyboardButton(text="🇷🇺 Ruscha", callback_data="lang:ru"),
            ],
            [
                InlineKeyboardButton(text="🇬🇧 Inglizcha", callback_data="lang:en"),
            ],
        ]
    )
