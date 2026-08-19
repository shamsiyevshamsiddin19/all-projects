"""/feedback — foydalanuvchi fikri to'g'ridan-to'g'ri adminlarga boradi.

Foydalanuvchi /feedback <matn> yuboradi; matn barcha ADMIN_IDS ga
foydalanuvchi ma'lumoti bilan uzatiladi. Bot javob bermay qo'ygan/xato
holatlarda foydalanuvchi ovozi yo'qolmasligi uchun eng qisqa yo'l.
"""
from __future__ import annotations

import html
import logging

from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import Message

from config import settings

logger = logging.getLogger(__name__)
router = Router()

_MAX_LEN = 1500


@router.message(Command("feedback"))
async def cmd_feedback(message: Message, bot: Bot) -> None:
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        await message.answer(
            "💬 <b>Fikr-mulohaza</b>\n\n"
            "Taklif, muammo yoki minnatdorchilikni shunday yuboring:\n"
            "<code>/feedback Tarjima juda zo'r, lekin ...</code>\n\n"
            "Xabaringiz to'g'ridan-to'g'ri dasturchiga boradi.",
            parse_mode="HTML",
        )
        return

    text = parts[1].strip()[:_MAX_LEN]
    u = message.from_user
    who = f"@{u.username}" if u.username else (u.full_name or "?")
    note = (
        f"💬 <b>Yangi fikr</b> — {html.escape(who)} "
        f"(<code>{u.id}</code>):\n\n{html.escape(text)}"
    )
    delivered = False
    for aid in settings.admin_id_set:
        try:
            await bot.send_message(aid, note, parse_mode="HTML")
            delivered = True
        except Exception:
            logger.warning("Feedback adminга (%s) yetmadi", aid)

    if delivered:
        await message.answer(
            "✅ Rahmat! Fikringiz dasturchiga yetkazildi — albatta o'qiladi. 🙌"
        )
    else:
        await message.answer(
            "✅ Rahmat! Fikringiz qabul qilindi."
        )
