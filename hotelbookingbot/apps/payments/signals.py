from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.bookings.models import BookingStatus
from apps.bookings.services import set_booking_status

from .models import PaymentState, PaymentStatus


@receiver(post_save, sender=PaymentStatus)
def confirm_booking_on_payment(sender, instance: PaymentStatus, **kwargs):
    if instance.status != PaymentState.PAID:
        return
    booking = instance.booking
    if booking.status == BookingStatus.PENDING:
        set_booking_status(booking, BookingStatus.CONFIRMED, comment="To'lov qabul qilindi (avtomatik tasdiqlash)")
