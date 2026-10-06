from aiogram.fsm.state import State, StatesGroup


class BookingStates(StatesGroup):
    choosing_room_type = State()
    viewing_room_details = State()
    choosing_check_in = State()
    choosing_check_out = State()
    choosing_guests_count = State()
    entering_guest_info = State()
    confirming_booking = State()
    choosing_payment_method = State()


class ProfileStates(StatesGroup):
    waiting_for_phone = State()
    choosing_language = State()


class CancelBookingStates(StatesGroup):
    choosing_booking_to_cancel = State()
    confirming_cancel = State()
    entering_cancel_reason = State()


class StaffStates(StatesGroup):
    waiting_for_role_target = State()
    waiting_for_block_target = State()
