from datetime import date, timedelta

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from apps.bookings.services import check_availability, create_booking
from apps.core.exceptions import InvalidBookingDatesError, NoRoomsAvailableError
from apps.hotels.models import RoomType

from ..keyboards.inline import confirm_booking_keyboard, guests_count_keyboard
from ..keyboards.reply import main_menu_keyboard
from ..states import BookingStates
from ..utils.calendar_kb import build_calendar

router = Router(name="booking")


@router.callback_query(F.data.startswith("book:"))
async def start_booking(callback: CallbackQuery, state: FSMContext):
    room_type_id = int(callback.data.split(":")[1])
    await state.update_data(room_type_id=room_type_id)
    await state.set_state(BookingStates.choosing_check_in)

    today = date.today()
    await callback.message.answer(
        "📅 Kirish sanasini tanlang:", reply_markup=build_calendar(today.year, today.month, purpose="checkin")
    )
    await callback.answer()


@router.callback_query(F.data.startswith("cal:"), BookingStates.choosing_check_in)
async def pick_check_in(callback: CallbackQuery, state: FSMContext):
    _, purpose, action, value = callback.data.split(":", 3)
    if action == "nav":
        year, month = map(int, value.split("-"))
        await callback.message.edit_reply_markup(reply_markup=build_calendar(year, month, purpose=purpose))
        await callback.answer()
        return
    if action != "pick":
        await callback.answer()
        return

    check_in = date.fromisoformat(value)
    await state.update_data(check_in=check_in.isoformat())
    await state.set_state(BookingStates.choosing_check_out)

    next_month_date = check_in + timedelta(days=1)
    await callback.message.edit_text(
        f"Kirish sanasi: {check_in}\n📅 Endi chiqish sanasini tanlang:",
        reply_markup=build_calendar(next_month_date.year, next_month_date.month, min_date=next_month_date, purpose="checkout"),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("cal:"), BookingStates.choosing_check_out)
async def pick_check_out(callback: CallbackQuery, state: FSMContext):
    _, purpose, action, value = callback.data.split(":", 3)
    data = await state.get_data()
    check_in = date.fromisoformat(data["check_in"])

    if action == "nav":
        year, month = map(int, value.split("-"))
        await callback.message.edit_reply_markup(
            reply_markup=build_calendar(year, month, min_date=check_in + timedelta(days=1), purpose=purpose)
        )
        await callback.answer()
        return
    if action != "pick":
        await callback.answer()
        return

    check_out = date.fromisoformat(value)
    room_type_id = data["room_type_id"]

    available = await check_availability_async(room_type_id, check_in, check_out)
    if available <= 0:
        await callback.message.edit_text(
            "😔 Afsuski bu sanalarda bo'sh xona yo'q. Boshqa sanalarni tanlang.\n\n📅 Kirish sanasini tanlang:",
            reply_markup=build_calendar(check_in.year, check_in.month, purpose="checkin"),
        )
        await state.set_state(BookingStates.choosing_check_in)
        await callback.answer()
        return

    await state.update_data(check_out=check_out.isoformat(), adults=1, children=0)
    await state.set_state(BookingStates.choosing_guests_count)
    await callback.message.edit_text(
        f"Kirish: {check_in}\nChiqish: {check_out}\n\n👥 Kattalar sonini tanlang:",
        reply_markup=guests_count_keyboard(1),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("guests:"), BookingStates.choosing_guests_count)
async def choose_guests(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split(":")[1]
    data = await state.get_data()
    adults = data.get("adults", 1)

    if action == "inc":
        adults = min(adults + 1, 10)
        await state.update_data(adults=adults)
        await callback.message.edit_reply_markup(reply_markup=guests_count_keyboard(adults))
        await callback.answer()
        return
    if action == "dec":
        adults = max(adults - 1, 1)
        await state.update_data(adults=adults)
        await callback.message.edit_reply_markup(reply_markup=guests_count_keyboard(adults))
        await callback.answer()
        return
    if action == "noop":
        await callback.answer()
        return

    room_type = await RoomType.objects.aget(id=data["room_type_id"])
    check_in = date.fromisoformat(data["check_in"])
    check_out = date.fromisoformat(data["check_out"])
    nights = (check_out - check_in).days
    total_price = room_type.base_price * nights

    await state.set_state(BookingStates.confirming_booking)
    text = (
        f"<b>Bron xulosasi</b>\n\n"
        f"🏨 Xona turi: {room_type.name}\n"
        f"📅 {check_in} — {check_out} ({nights} kecha)\n"
        f"👥 Mehmonlar: {adults} kattalar\n"
        f"💵 Jami narx: {total_price} {room_type.currency}"
    )
    await callback.message.edit_text(text, reply_markup=confirm_booking_keyboard())
    await callback.answer()


@router.callback_query(F.data == "booking:cancel", BookingStates.confirming_booking)
async def cancel_booking_flow(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Bron bekor qilindi.")
    await callback.message.answer("Asosiy menyu:", reply_markup=main_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == "booking:confirm", BookingStates.confirming_booking)
async def confirm_booking_flow(callback: CallbackQuery, state: FSMContext, user):
    data = await state.get_data()
    room_type = await RoomType.objects.aget(id=data["room_type_id"])
    check_in = date.fromisoformat(data["check_in"])
    check_out = date.fromisoformat(data["check_out"])
    adults = data.get("adults", 1)

    try:
        booking = await create_booking_async(user, room_type, check_in, check_out, adults)
    except NoRoomsAvailableError:
        await callback.message.edit_text("😔 Afsuski bu oraliqda xona band bo'lib qoldi. Qaytadan urinib ko'ring.")
        await state.clear()
        await callback.answer()
        return
    except InvalidBookingDatesError:
        await callback.message.edit_text("Sanalarda xatolik. Qaytadan boshlang.")
        await state.clear()
        await callback.answer()
        return

    await state.clear()
    await callback.message.edit_text(
        f"✅ Bronlash so'rovingiz qabul qilindi!\nKod: <b>{booking.booking_code}</b>\n"
        f"Operator tasdiqlaganidan so'ng xabar beramiz.\n\n"
        f"Istasangiz, hoziroq onlayn to'lab, bronni avtomatik tasdiqlatib olishingiz mumkin:"
    )
    await send_pay_button(callback.message, booking)
    await callback.message.answer("Asosiy menyu:", reply_markup=main_menu_keyboard())
    await callback.answer()


async def send_pay_button(message, booking):
    from django.conf import settings

    from apps.payments.gateways.click import payment_url

    from ..keyboards.inline import pay_click_keyboard

    if not settings.CLICK_MERCHANT_ID:
        return
    url = payment_url(booking)
    await message.answer(
        f"💳 {booking.total_price} {booking.room_type.currency} — Click orqali to'lash:",
        reply_markup=pay_click_keyboard(url),
    )


async def check_availability_async(room_type_id, check_in, check_out):
    from asgiref.sync import sync_to_async

    return await sync_to_async(check_availability)(room_type_id, check_in, check_out)


async def create_booking_async(user, room_type, check_in, check_out, adults):
    from asgiref.sync import sync_to_async

    return await sync_to_async(create_booking)(user, room_type, check_in, check_out, adults)
