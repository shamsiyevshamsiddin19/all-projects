"""Inline rejim:
  @bot ref_<kod>  → referal ulashish xabari (batafsil + "Botni ochish" tugmasi)
  @bot <mavzu>    → hujjat turlari ro'yxati (buyurtma uchun)
"""
from __future__ import annotations
from aiogram import Router
from aiogram.types import (
    InlineQuery, InlineQueryResultArticle, InputTextMessageContent,
    InlineKeyboardMarkup, InlineKeyboardButton,
)
from config import settings, DOC_TYPES

router = Router()


def _ref_share_text(ref_link: str) -> str:
    """Do'stga yuboriladigan to'laqonli reklama xabari."""
    return (
        "🎓 <b>Talaba xizmatlari boti</b>\n\n"
        "Referat, mustaqil ish, kurs ishi, diplom, taqdimot (slayd), ilmiy "
        "maqola, tezis va krossvord — hammasi <b>AI yordamida</b>, daqiqalar "
        "ichida, o'z qoidalari bo'yicha tayyor bo'ladi! 🚀\n\n"
        "✅ Mavzu va sahifa sonini o'zingiz tanlaysiz\n"
        "✅ Word / PDF / PowerPoint formatda\n"
        "✅ Click orqali qulay to'lov\n\n"
        "👇 Quyidagi tugma orqali botga kiring va birinchi buyurtmangizni bering:\n"
        f"{ref_link}"
    )


@router.inline_query()
async def inline_handler(query: InlineQuery):
    q = query.query.strip()

    # ── Referal ulashish: @bot ref_<kod> ──
    if q.startswith("ref_"):
        code = q[4:]
        ref_link = f"https://t.me/{settings.bot_username}?start=ref_{code}"
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🚀 Botni ochish", url=ref_link)
        ]])
        result = InlineQueryResultArticle(
            id="ref_share",
            title="📤 Do'stlarni taklif qilish",
            description="Tayyor reklama xabari + botga kirish tugmasi",
            input_message_content=InputTextMessageContent(
                message_text=_ref_share_text(ref_link),
                parse_mode="HTML",
                disable_web_page_preview=False,
            ),
            reply_markup=kb,
        )
        await query.answer([result], cache_time=0, is_personal=True)
        return

    # ── Oddiy rejim: hujjat turlari ──
    topic = q or "Yangi buyurtma"
    results = []
    for i, (key, info) in enumerate(DOC_TYPES.items()):
        price = settings.min_price(key)
        deep_link = f"https://t.me/{settings.bot_username}?start=order_{key}"
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🔗 Botda buyurtma bering", url=deep_link)
        ]])
        content = InputTextMessageContent(
            message_text=(
                f"{info['emoji']} <b>{info['label']}</b>\n"
                f"📌 Mavzu: <b>{topic}</b>\n"
                f"💰 Narx: <b>{price:,} so'm dan</b> (har {info['unit']} "
                f"{settings.per_unit(key):,} so'm)\n\n"
                f"👇 Buyurtma berish uchun quyidagi tugmani bosing:"
            ),
            parse_mode="HTML",
        )
        results.append(InlineQueryResultArticle(
            id=f"{key}_{i}",
            title=f"{info['emoji']} {info['label']}",
            description=f"{topic} · {price:,} so'm dan · {info['cmin']}-{info['cmax']} {info['unit']}",
            input_message_content=content,
            reply_markup=kb,
        ))
    await query.answer(results, cache_time=10, is_personal=True)
