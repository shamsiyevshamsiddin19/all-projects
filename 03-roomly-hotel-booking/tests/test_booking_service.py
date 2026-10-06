from datetime import date, timedelta

import pytest

from apps.bookings.models import BookingStatus
from apps.bookings.services import cancel_booking, check_availability, create_booking
from apps.core.exceptions import BookingNotCancellableError, InvalidBookingDatesError, NoRoomsAvailableError
from tests.factories import RoomFactory, RoomTypeFactory, TelegramUserFactory

pytestmark = pytest.mark.django_db


def test_check_availability_counts_free_rooms():
    room_type = RoomTypeFactory()
    RoomFactory(room_type=room_type)
    RoomFactory(room_type=room_type)

    available = check_availability(room_type.id, date.today() + timedelta(days=1), date.today() + timedelta(days=3))
    assert available == 2


def test_create_booking_reduces_availability():
    room_type = RoomTypeFactory()
    RoomFactory(room_type=room_type)
    user = TelegramUserFactory()

    check_in = date.today() + timedelta(days=1)
    check_out = date.today() + timedelta(days=3)
    booking = create_booking(user, room_type, check_in, check_out, adults=2)

    assert booking.status == BookingStatus.PENDING
    assert booking.nights == 2
    assert booking.total_price == room_type.base_price * 2
    assert check_availability(room_type.id, check_in, check_out) == 0


def test_create_booking_raises_when_no_rooms_available():
    room_type = RoomTypeFactory()
    RoomFactory(room_type=room_type)
    user = TelegramUserFactory()

    check_in = date.today() + timedelta(days=1)
    check_out = date.today() + timedelta(days=3)
    create_booking(user, room_type, check_in, check_out, adults=1)

    with pytest.raises(NoRoomsAvailableError):
        create_booking(TelegramUserFactory(), room_type, check_in, check_out, adults=1)


def test_create_booking_invalid_dates():
    room_type = RoomTypeFactory()
    RoomFactory(room_type=room_type)
    user = TelegramUserFactory()
    with pytest.raises(InvalidBookingDatesError):
        create_booking(user, room_type, date.today(), date.today(), adults=1)


def test_cancel_booking_marks_cancelled_and_frees_room():
    room_type = RoomTypeFactory()
    RoomFactory(room_type=room_type)
    user = TelegramUserFactory()
    check_in = date.today() + timedelta(days=1)
    check_out = date.today() + timedelta(days=3)
    booking = create_booking(user, room_type, check_in, check_out, adults=1)

    cancel_booking(booking, reason="test")
    booking.refresh_from_db()

    assert booking.status == BookingStatus.CANCELLED
    assert check_availability(room_type.id, check_in, check_out) == 1


def test_cannot_cancel_booking_starting_today():
    room_type = RoomTypeFactory()
    RoomFactory(room_type=room_type)
    user = TelegramUserFactory()
    booking = create_booking(user, room_type, date.today(), date.today() + timedelta(days=1), adults=1)

    with pytest.raises(BookingNotCancellableError):
        cancel_booking(booking)
