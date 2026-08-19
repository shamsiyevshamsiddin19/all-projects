from aiogram import Dispatcher

from . import booking, cancel_booking, my_bookings, rooms, staff, start


def register_all_handlers(dp: Dispatcher) -> None:
    dp.include_router(start.router)
    dp.include_router(rooms.router)
    dp.include_router(booking.router)
    dp.include_router(my_bookings.router)
    dp.include_router(cancel_booking.router)
    dp.include_router(staff.router)
