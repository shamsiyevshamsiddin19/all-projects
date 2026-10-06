from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from apps.bookings.models import Booking, BookingStatus
from apps.bookings.services import expire_stale_pending_bookings

from .models import Notification, NotificationType
from .telegram_client import send_message

STATUS_MESSAGES = {
    BookingStatus.CONFIRMED: ("✅ Bron tasdiqlandi", "Bron ({code}) tasdiqlandi. Kirish sanasi: {check_in}."),
    BookingStatus.CANCELLED: ("❌ Bron bekor qilindi", "Bron ({code}) bekor qilindi."),
    BookingStatus.EXPIRED: ("⌛ Bron muddati o'tdi", "Bron ({code}) vaqtida tasdiqlanmagani uchun avtomatik bekor qilindi."),
    BookingStatus.CHECKED_IN: ("🏨 Xush kelibsiz!", "Bron ({code}) bo'yicha check-in belgilandi."),
    BookingStatus.CHECKED_OUT: ("👋 Xayr!", "Bron ({code}) bo'yicha check-out belgilandi. Tashrifingiz uchun rahmat!"),
}


@shared_task
def notify_new_booking_to_staff(booking_id: int):
    if not settings.ADMIN_GROUP_CHAT_ID:
        return
    try:
        booking = Booking.objects.select_related("user", "room_type").get(id=booking_id)
    except Booking.DoesNotExist:
        return

    text = (
        f"🆕 <b>Yangi bron</b>\n"
        f"Kod: {booking.booking_code}\n"
        f"Mehmon: {booking.user.full_name} (@{booking.user.username or '-'})\n"
        f"Xona turi: {booking.room_type.name}\n"
        f"Sanalar: {booking.check_in_date} — {booking.check_out_date}\n"
        f"Mehmonlar: {booking.adults}+{booking.children}\n"
        f"Narx: {booking.total_price} {booking.room_type.currency}"
    )
    reply_markup = {
        "inline_keyboard": [
            [
                {"text": "✅ Tasdiqlash", "callback_data": f"staff_confirm:{booking.id}"},
                {"text": "❌ Rad etish", "callback_data": f"staff_reject:{booking.id}"},
            ]
        ]
    }
    send_message(settings.ADMIN_GROUP_CHAT_ID, text, reply_markup=reply_markup)


@shared_task
def notify_booking_status_change(booking_id: int):
    try:
        booking = Booking.objects.select_related("user").get(id=booking_id)
    except Booking.DoesNotExist:
        return

    template = STATUS_MESSAGES.get(booking.status)
    if not template:
        return

    title, body = template
    message = body.format(code=booking.booking_code, check_in=booking.check_in_date)

    notification = Notification.objects.create(
        user=booking.user,
        title=title,
        message=message,
        notif_type=_status_to_notif_type(booking.status),
    )
    ok = send_message(booking.user.telegram_id, f"<b>{title}</b>\n{message}")

    if ok:
        notification.is_sent = True
        notification.sent_at = timezone.now()
        notification.save(update_fields=["is_sent", "sent_at"])

    if settings.ADMIN_GROUP_CHAT_ID and booking.status == BookingStatus.CANCELLED:
        send_message(settings.ADMIN_GROUP_CHAT_ID, f"❌ Bron bekor qilindi: {booking.booking_code}")


def _status_to_notif_type(status: str) -> str:
    return {
        BookingStatus.CONFIRMED: NotificationType.BOOKING_CONFIRMED,
        BookingStatus.CANCELLED: NotificationType.BOOKING_CANCELLED,
        BookingStatus.EXPIRED: NotificationType.BOOKING_CANCELLED,
    }.get(status, NotificationType.SYSTEM)


@shared_task
def expire_pending_bookings_task():
    from django.conf import settings as dj_settings

    count = expire_stale_pending_bookings(dj_settings.BOOKING_PENDING_EXPIRY_HOURS)
    return {"expired": count}


@shared_task
def send_checkin_reminders_task():
    tomorrow = timezone.localdate() + timedelta(days=1)
    bookings = Booking.objects.select_related("user").filter(
        status=BookingStatus.CONFIRMED, check_in_date=tomorrow
    )
    sent = 0
    for booking in bookings:
        message = f"📅 Eslatma: ertaga ({booking.check_in_date}) mehmonxonamizga tashrif buyurasiz. Kutamiz!"
        Notification.objects.create(
            user=booking.user, title="Eslatma", message=message, notif_type=NotificationType.REMINDER
        )
        if send_message(booking.user.telegram_id, message):
            sent += 1
    return {"reminders_sent": sent}
