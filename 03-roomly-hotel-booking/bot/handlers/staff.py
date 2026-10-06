from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from apps.accounts.models import RoleChoices, TelegramUser
from apps.bookings.models import Booking, BookingStatus
from apps.bookings.services import set_booking_status

from ..filters.role_filter import RoleFilter
from ..keyboards.inline import staff_pending_keyboard

router = Router(name="staff")

OPERATOR_UP = [RoleChoices.OPERATOR, RoleChoices.MANAGER, RoleChoices.ADMIN, RoleChoices.SUPERADMIN]
MANAGER_UP = [RoleChoices.MANAGER, RoleChoices.ADMIN, RoleChoices.SUPERADMIN]
ADMIN_UP = [RoleChoices.ADMIN, RoleChoices.SUPERADMIN]


@router.message(Command("pending"), RoleFilter(OPERATOR_UP))
async def pending_bookings(message: Message):
    bookings = [
        b
        async for b in Booking.objects.filter(status=BookingStatus.PENDING)
        .select_related("room_type", "user")
        .order_by("created_at")[:10]
    ]
    if not bookings:
        await message.answer("Hozircha kutilayotgan bronlar yo'q. ✅")
        return

    for booking in bookings:
        text = (
            f"🟡 <b>{booking.booking_code}</b>\n"
            f"Mehmon: {booking.user.full_name}\n"
            f"Xona turi: {booking.room_type.name}\n"
            f"Sanalar: {booking.check_in_date} — {booking.check_out_date}\n"
            f"Narx: {booking.total_price} {booking.room_type.currency}"
        )
        await message.answer(text, reply_markup=staff_pending_keyboard(booking.id))


@router.message(Command("today_checkins"), RoleFilter(OPERATOR_UP))
async def today_checkins(message: Message):
    from django.utils import timezone

    today = timezone.localdate()
    bookings = [
        b
        async for b in Booking.objects.filter(check_in_date=today, status=BookingStatus.CONFIRMED)
        .select_related("room_type", "user")
    ]
    if not bookings:
        await message.answer("Bugun kirish yo'q.")
        return
    text = "\n".join(f"• {b.booking_code} — {b.user.full_name} ({b.room_type.name})" for b in bookings)
    await message.answer(f"📥 <b>Bugungi kirishlar</b>\n\n{text}")


@router.message(Command("today_checkouts"), RoleFilter(OPERATOR_UP))
async def today_checkouts(message: Message):
    from django.utils import timezone

    today = timezone.localdate()
    bookings = [
        b
        async for b in Booking.objects.filter(check_out_date=today, status=BookingStatus.CHECKED_IN)
        .select_related("room_type", "user")
    ]
    if not bookings:
        await message.answer("Bugun chiqish yo'q.")
        return
    text = "\n".join(f"• {b.booking_code} — {b.user.full_name} ({b.room_type.name})" for b in bookings)
    await message.answer(f"📤 <b>Bugungi chiqishlar</b>\n\n{text}")


@router.message(Command("stats"), RoleFilter(MANAGER_UP))
async def stats_handler(message: Message):
    from django.db.models import Sum
    from django.utils import timezone

    from apps.payments.models import PaymentState, PaymentStatus

    today = timezone.localdate()
    today_count = await Booking.objects.filter(created_at__date=today).acount()
    week_count = await Booking.objects.filter(created_at__date__gte=today - timezone.timedelta(days=7)).acount()
    total_paid = await PaymentStatus.objects.filter(status=PaymentState.PAID).aaggregate(total=Sum("amount"))

    await message.answer(
        f"📊 <b>Statistika</b>\n\n"
        f"Bugungi bronlar: {today_count}\n"
        f"Haftalik bronlar: {week_count}\n"
        f"Jami to'langan: {total_paid['total'] or 0}"
    )


@router.message(Command("block"), RoleFilter(ADMIN_UP))
async def block_user(message: Message):
    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Foydalanish: /block <telegram_id>")
        return
    telegram_id = int(parts[1])
    try:
        target = await TelegramUser.objects.aget(telegram_id=telegram_id)
    except TelegramUser.DoesNotExist:
        await message.answer("Foydalanuvchi topilmadi.")
        return
    target.is_blocked = True
    await target.asave(update_fields=["is_blocked"])
    await message.answer(f"🚫 {target.full_name} bloklandi.")


@router.message(Command("setrole"), RoleFilter(ADMIN_UP))
async def set_role(message: Message):
    parts = message.text.split()
    if len(parts) != 3 or not parts[1].isdigit() or parts[2].upper() not in RoleChoices.values:
        await message.answer(f"Foydalanish: /setrole <telegram_id> <{'|'.join(RoleChoices.values)}>")
        return
    telegram_id = int(parts[1])
    role = parts[2].upper()
    try:
        target = await TelegramUser.objects.aget(telegram_id=telegram_id)
    except TelegramUser.DoesNotExist:
        await message.answer("Foydalanuvchi topilmadi.")
        return
    target.role = role
    await target.asave(update_fields=["role"])
    await message.answer(f"✅ {target.full_name} uchun rol o'rnatildi: {role}")


@router.callback_query(F.data.startswith("staff_confirm:"))
async def staff_confirm(callback: CallbackQuery, user):
    if user.role not in OPERATOR_UP:
        await callback.answer("Sizda ruxsat yo'q", show_alert=True)
        return
    from asgiref.sync import sync_to_async

    booking_id = int(callback.data.split(":")[1])
    try:
        booking = await Booking.objects.aget(id=booking_id)
    except Booking.DoesNotExist:
        await callback.answer("Bron topilmadi", show_alert=True)
        return
    await sync_to_async(set_booking_status)(booking, BookingStatus.CONFIRMED, changed_by=user, comment="Bot orqali tasdiqlandi")
    await callback.message.edit_text(callback.message.text + "\n\n✅ Tasdiqlandi")
    await callback.answer()


@router.callback_query(F.data.startswith("staff_reject:"))
async def staff_reject(callback: CallbackQuery, user):
    if user.role not in OPERATOR_UP:
        await callback.answer("Sizda ruxsat yo'q", show_alert=True)
        return
    from asgiref.sync import sync_to_async

    booking_id = int(callback.data.split(":")[1])
    try:
        booking = await Booking.objects.aget(id=booking_id)
    except Booking.DoesNotExist:
        await callback.answer("Bron topilmadi", show_alert=True)
        return
    await sync_to_async(set_booking_status)(booking, BookingStatus.CANCELLED, changed_by=user, comment="Bot orqali rad etildi")
    await callback.message.edit_text(callback.message.text + "\n\n❌ Rad etildi")
    await callback.answer()
