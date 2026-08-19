from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from apps.bookings.models import Booking

from ..keyboards.reply import MAIN_MENU_MY_BOOKINGS
from ..utils.formatters import format_booking_line

router = Router(name="my_bookings")


@router.message(F.text == MAIN_MENU_MY_BOOKINGS)
async def my_bookings_handler(message: Message, user):
    from ..keyboards.inline import my_bookings_keyboard

    bookings = [
        b
        async for b in Booking.objects.filter(user=user).select_related("room_type").order_by("-created_at")[:20]
    ]
    if not bookings:
        await message.answer("Sizda hali bronlar yo'q. 🏨 Xonalar bo'limidan bron qiling.")
        return

    text = "📅 <b>Mening bronlarim</b>\n\n" + "\n\n".join(format_booking_line(b) for b in bookings)
    await message.answer(text, reply_markup=my_bookings_keyboard(bookings))


@router.callback_query(F.data.startswith("booking_detail:"))
async def booking_detail(callback: CallbackQuery, user):
    booking_id = int(callback.data.split(":")[1])
    try:
        booking = await Booking.objects.select_related("room_type").aget(id=booking_id, user=user)
    except Booking.DoesNotExist:
        await callback.answer("Bron topilmadi", show_alert=True)
        return

    text = (
        f"<b>{booking.booking_code}</b>\n"
        f"Xona turi: {booking.room_type.name}\n"
        f"Sanalar: {booking.check_in_date} — {booking.check_out_date}\n"
        f"Mehmonlar: {booking.adults} kattalar, {booking.children} bolalar\n"
        f"Holat: {booking.get_status_display()}\n"
        f"Jami narx: {booking.total_price} {booking.room_type.currency}"
    )
    await callback.message.answer(text)

    if booking.status in ("PENDING", "CONFIRMED"):
        from django.conf import settings

        from apps.payments.gateways.click import payment_url
        from apps.payments.models import PaymentState, PaymentStatus

        from ..keyboards.inline import pay_click_keyboard

        already_paid = await PaymentStatus.objects.filter(booking=booking, status=PaymentState.PAID).aexists()
        if settings.CLICK_MERCHANT_ID and not already_paid:
            url = payment_url(booking)
            await callback.message.answer(
                f"💳 {booking.total_price} {booking.room_type.currency} — Click orqali to'lash:",
                reply_markup=pay_click_keyboard(url),
            )

    await callback.answer()
