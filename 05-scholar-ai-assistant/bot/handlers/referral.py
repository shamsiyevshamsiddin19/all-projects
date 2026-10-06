from __future__ import annotations
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from db.crud import get_user, get_referral_stats
from db.models import User
from bot.keyboards.inline import referral_kb, main_menu
from config import settings, DOC_TYPES

router = Router()


@router.message(F.text == "🤝 Referal dastur")
async def referral_menu(message: Message, db_user: User):
    stats = await get_referral_stats(db_user.id)
    link = f"https://t.me/{settings.bot_username}?start=ref_{db_user.referral_code}"

    bonuses = "\n".join(
        f"  {info['emoji']} {info['label']}: +{settings.ref_bonus(key):,} so'm"
        for key, info in DOC_TYPES.items()
    )

    text = f"""🤝 <b>REFERAL DASTUR</b>

📊 <b>Sizning statistikangiz:</b>
👥 Jalb qilganlar: <b>{stats['total']}</b> ta
💳 To'lov qilganlar: <b>{stats['paid']}</b> ta
💰 Jami bonus: <b>{stats['earned']:,}</b> so'm

🔗 <b>Sizning havolangiz:</b>
<code>{link}</code>

🎁 <b>Bonus sxemasi:</b>
Do'stingiz ushbu havola orqali kelib, <b>birinchi to'lov</b> qilganda siz avto bonus olasiz:

{bonuses}

<b>Qanday ishlaydi?</b>
1️⃣ Havolani do'stingizga yuboring
2️⃣ Do'stingiz bot orqali buyurtma beradi
3️⃣ Birinchi to'lovda sizga bonus avtomatik tushadi
4️⃣ Bonus balansdan har qanday buyurtmada ishlatiladi"""

    await message.answer(text, parse_mode="HTML",
                         reply_markup=referral_kb(settings.bot_username, db_user.referral_code))


@router.callback_query(F.data.startswith("copy_ref:"))
async def copy_referral(call: CallbackQuery, db_user: User):
    code = call.data.split(":")[1]
    link = f"https://t.me/{settings.bot_username}?start=ref_{code}"
    await call.message.answer(
        f"📋 <b>Havolani nusxalang:</b>\n<code>{link}</code>",
        parse_mode="HTML",
    )
    await call.answer("✅ Havola yuborildi!")
