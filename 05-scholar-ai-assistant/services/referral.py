"""Referal bonus berish xizmati."""
from __future__ import annotations
from db.crud import award_referral_bonus
from config import settings


async def check_and_award(bot, user_id: int, doc_type: str):
    """Birinchi to'lovda referral bonusini beradi."""
    bonus = settings.ref_bonus(doc_type)
    referrer_id = await award_referral_bonus(user_id, doc_type, bonus)
    if referrer_id:
        try:
            await bot.send_message(
                referrer_id,
                f"🎉 <b>Referal bonus!</b>\n\n"
                f"Siz taklif qilgan foydalanuvchi to'lov qildi.\n"
                f"💰 Balansingizga <b>+{bonus:,} so'm</b> qo'shildi!\n\n"
                f"<i>Bonus hisob balansingizda, keyingi buyurtmada foydalaning.</i>",
                parse_mode="HTML",
            )
        except Exception:
            pass
