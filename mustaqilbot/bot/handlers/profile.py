from __future__ import annotations
from aiogram import Router, F
from aiogram.types import Message
from db.crud import get_user_orders, get_referral_stats
from db.models import User
from bot.keyboards.inline import main_menu, order_done_kb
from config import DOC_TYPES

router = Router()

_STATUS = {
    "pending": "⏳ Kutmoqda",
    "generating": "🔄 Tayyorlanmoqda",
    "done": "✅ Tayyor",
    "error": "❌ Xato",
    "refunded": "↩️ Qaytarilgan",
}


@router.message(F.text == "👤 Profilim")
async def my_profile(message: Message, db_user: User):
    stats = await get_referral_stats(db_user.id)
    uname = f"@{db_user.username}" if db_user.username else "—"
    text = f"""👤 <b>Profil</b>

🆔 ID: <code>{db_user.id}</code>
👤 Username: {uname}
💰 Balans: <b>{db_user.balance:,} so'm</b>
📦 Buyurtmalar: <b>{db_user.orders_count}</b> ta
🤝 Referallar: <b>{stats['total']}</b> ta
🎁 Referal bonus: <b>{stats['earned']:,} so'm</b>
💳 Jami sarflandi: <b>{db_user.total_spent:,} so'm</b>

🔑 Referal kod: <code>{db_user.referral_code}</code>"""
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "📂 Mening buyurtmalarim")
async def my_orders(message: Message, db_user: User):
    orders = await get_user_orders(db_user.id, limit=10)
    if not orders:
        await message.answer(
            "📭 Hali buyurtmalaringiz yo'q.\n\n"
            "📝 Yangi buyurtma berish uchun «📝 Buyurtma berish» tugmasini bosing.",
            reply_markup=main_menu(),
        )
        return

    for o in orders[:5]:
        info = DOC_TYPES.get(o["doc_type"], {})
        emoji = info.get("emoji", "📄")
        label = info.get("label", o["doc_type"])
        status = _STATUS.get(o["status"], o["status"])
        dt_str = o["created_at"].strftime("%d.%m.%Y %H:%M") if o.get("created_at") else "—"

        text = (
            f"{emoji} <b>{label}</b>\n"
            f"📌 {o['topic'][:60]}\n"
            f"📊 {status} · {o['price']:,} so'm\n"
            f"🕒 {dt_str}"
        )
        kb = order_done_kb(o["id"]) if o["status"] == "done" and o.get("tg_file_id") else None
        await message.answer(text, parse_mode="HTML", reply_markup=kb)

    if len(orders) > 5:
        await message.answer(f"... va yana {len(orders) - 5} ta buyurtma.")
