"""Admin buyruqlari (test uchun). To'liq boshqaruv keyin admin saytda bo'ladi.

/grant <tarif> [kun]            -> o'zingizga tarif beradi (test)
/grant <telegram_id> <tarif> [kun] -> boshqa foydalanuvchiga
  tarif: free | basic | premium ; kun: default 30
"""
from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from config import settings
from db.crud import set_plan
from tariffs import TARIFFS

router = Router()


def _is_admin(user_id: int) -> bool:
    return user_id in settings.admin_id_set


@router.message(Command("grant"))
async def cmd_grant(message: Message) -> None:
    if not _is_admin(message.from_user.id):
        return  # admin emaslarga e'tibor bermaymiz

    args = message.text.split()[1:]
    if not args:
        await message.answer(
            "Foydalanish:\n"
            "/grant <tarif> [kun] — o'zingizga\n"
            "/grant <telegram_id> <tarif> [kun] — boshqaga\n"
            "tarif: free | basic | premium"
        )
        return

    if args[0].isdigit():
        target_id = int(args[0])
        plan = args[1] if len(args) > 1 else "basic"
        days = int(args[2]) if len(args) > 2 and args[2].isdigit() else 30
    else:
        target_id = message.from_user.id
        plan = args[0]
        days = int(args[1]) if len(args) > 1 and args[1].isdigit() else 30

    if plan not in TARIFFS:
        await message.answer("❌ Noto'g'ri tarif. Mavjud: free, basic, premium")
        return

    found = await set_plan(target_id, plan, days)
    if found:
        await message.answer(
            f"✅ {target_id} ga <b>{plan}</b> tarifi berildi ({days} kun).",
            parse_mode="HTML",
        )
    else:
        await message.answer(
            f"⚠️ {target_id} topilmadi. U avval botga /start bossin."
        )
