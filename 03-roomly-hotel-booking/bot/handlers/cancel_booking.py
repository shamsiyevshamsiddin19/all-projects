from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from apps.bookings.models import Booking
from apps.core.exceptions import BookingNotCancellableError

from ..keyboards.inline import cancel_confirm_keyboard
from ..states import CancelBookingStates

router = Router(name="cancel_booking")


@router.callback_query(F.data.startswith("cancel_booking:"))
async def ask_cancel_confirmation(callback: CallbackQuery, state: FSMContext):
    booking_id = int(callback.data.split(":")[1])
    await state.update_data(cancel_booking_id=booking_id)
    await state.set_state(CancelBookingStates.confirming_cancel)
    await callback.message.answer(
        "Rostdan ham bu bronni bekor qilmoqchimisiz?", reply_markup=cancel_confirm_keyboard(booking_id)
    )
    await callback.answer()


@router.callback_query(F.data == "cancel_abort")
async def abort_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Bekor qilinmadi, bron saqlanib qoldi.")
    await callback.answer()


@router.callback_query(F.data.startswith("cancel_confirm:"), CancelBookingStates.confirming_cancel)
async def do_cancel(callback: CallbackQuery, state: FSMContext, user):
    from asgiref.sync import sync_to_async

    from apps.bookings.services import cancel_booking as cancel_booking_service

    booking_id = int(callback.data.split(":")[1])
    try:
        booking = await Booking.objects.aget(id=booking_id, user=user)
    except Booking.DoesNotExist:
        await callback.answer("Bron topilmadi", show_alert=True)
        await state.clear()
        return

    try:
        await sync_to_async(cancel_booking_service)(booking, reason="Mehmon tomonidan bekor qilindi", cancelled_by=user)
    except BookingNotCancellableError as exc:
        await callback.message.edit_text(f"❌ {exc}")
        await state.clear()
        await callback.answer()
        return

    await state.clear()
    await callback.message.edit_text(f"✅ Bron {booking.booking_code} bekor qilindi.")
    await callback.answer()
