import random
import string
from datetime import date, timedelta

from django.db import transaction
from django.utils import timezone

from apps.core.exceptions import BookingNotCancellableError, InvalidBookingDatesError, NoRoomsAvailableError
from apps.hotels.models import Room, RoomType

from .models import ACTIVE_STATUSES, Booking, BookingStatus, BookingStatusHistory


def generate_booking_code() -> str:
    today = timezone.localdate().strftime("%Y%m%d")
    for _ in range(20):
        suffix = "".join(random.choices(string.digits, k=4))
        code = f"HB-{today}-{suffix}"
        if not Booking.objects.filter(booking_code=code).exists():
            return code
    raise RuntimeError("Could not generate a unique booking code")


def check_availability(room_type_id: int, check_in: date, check_out: date) -> int:
    """Berilgan sanalar oralig'ida bo'sh xonalar sonini qaytaradi."""
    total_rooms = Room.objects.filter(room_type_id=room_type_id, is_active=True).count()
    booked_rooms = Booking.objects.filter(
        room_type_id=room_type_id,
        status__in=ACTIVE_STATUSES,
        check_in_date__lt=check_out,
        check_out_date__gt=check_in,
    ).count()
    return total_rooms - booked_rooms


@transaction.atomic
def create_booking(user, room_type: RoomType, check_in: date, check_out: date, adults: int, children: int = 0) -> Booking:
    """Tranzaksiya ichida: mavjudlikni qayta tekshirish + booking yaratish (race-condition himoyasi bilan)."""
    if check_out <= check_in:
        raise InvalidBookingDatesError("Chiqish sanasi kirish sanasidan keyin bo'lishi kerak")

    # room_type qatorini qulflab qo'yamiz — shu turdagi xonaga bir vaqtda ikkita bron
    # kirmasligi uchun (mavjud bronlar bo'lmasa ham, RoomType qatori doim mavjud).
    RoomType.objects.select_for_update().get(pk=room_type.id)

    available = check_availability(room_type.id, check_in, check_out)
    if available <= 0:
        raise NoRoomsAvailableError("Ushbu sanalarda bo'sh xona yo'q")

    nights = (check_out - check_in).days
    booking = Booking.objects.create(
        booking_code=generate_booking_code(),
        user=user,
        room_type=room_type,
        check_in_date=check_in,
        check_out_date=check_out,
        adults=adults,
        children=children,
        nights=nights,
        price_per_night=room_type.base_price,
        total_price=room_type.base_price * nights,
        status=BookingStatus.PENDING,
    )
    BookingStatusHistory.objects.create(
        booking=booking, old_status="", new_status=BookingStatus.PENDING, comment="Bron yaratildi"
    )
    return booking


@transaction.atomic
def set_booking_status(booking: Booking, new_status: str, changed_by=None, comment: str = "") -> Booking:
    old_status = booking.status
    booking.status = new_status
    if new_status == BookingStatus.CANCELLED:
        booking.cancelled_at = timezone.now()
        booking.cancel_reason = comment or booking.cancel_reason
    if new_status == BookingStatus.CONFIRMED and changed_by is not None:
        booking.confirmed_by = changed_by
    booking.save()
    BookingStatusHistory.objects.create(
        booking=booking, old_status=old_status, new_status=new_status, changed_by=changed_by, comment=comment
    )
    return booking


def cancel_booking(booking: Booking, reason: str = "", cancelled_by=None) -> Booking:
    if booking.status not in (BookingStatus.PENDING, BookingStatus.CONFIRMED):
        raise BookingNotCancellableError("Bu bronni endi bekor qilib bo'lmaydi")
    if booking.check_in_date <= timezone.localdate():
        raise BookingNotCancellableError("Kirish sanasi bo'lib o'tgan yoki bugun bo'lgan bronni bekor qilib bo'lmaydi")
    return set_booking_status(booking, BookingStatus.CANCELLED, changed_by=cancelled_by, comment=reason)


def expire_stale_pending_bookings(hours: int) -> int:
    threshold = timezone.now() - timedelta(hours=hours)
    stale = Booking.objects.filter(status=BookingStatus.PENDING, created_at__lt=threshold)
    count = 0
    for booking in stale:
        set_booking_status(booking, BookingStatus.EXPIRED, comment="Vaqtida tasdiqlanmadi (avtomatik)")
        count += 1
    return count
