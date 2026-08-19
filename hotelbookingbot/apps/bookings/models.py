from django.conf import settings
from django.db import models

from apps.hotels.models import Room, RoomType


class BookingStatus(models.TextChoices):
    PENDING = "PENDING", "Kutilmoqda"
    CONFIRMED = "CONFIRMED", "Tasdiqlangan"
    CHECKED_IN = "CHECKED_IN", "Yashab bo'lindi (check-in)"
    CHECKED_OUT = "CHECKED_OUT", "Yakunlangan (check-out)"
    CANCELLED = "CANCELLED", "Bekor qilingan"
    EXPIRED = "EXPIRED", "Muddati o'tgan"


ACTIVE_STATUSES = (BookingStatus.PENDING, BookingStatus.CONFIRMED, BookingStatus.CHECKED_IN)


class Booking(models.Model):
    booking_code = models.CharField(max_length=20, unique=True)
    user = models.ForeignKey("accounts.TelegramUser", on_delete=models.CASCADE, related_name="bookings")
    room_type = models.ForeignKey(RoomType, on_delete=models.PROTECT, related_name="bookings")
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True, related_name="bookings")
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    adults = models.PositiveSmallIntegerField(default=1)
    children = models.PositiveSmallIntegerField(default=0)
    nights = models.PositiveSmallIntegerField()
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=BookingStatus.choices, default=BookingStatus.PENDING, db_index=True)
    special_requests = models.TextField(blank=True, max_length=1000)
    confirmed_by = models.ForeignKey(
        "accounts.TelegramUser", null=True, blank=True, on_delete=models.SET_NULL, related_name="confirmed_bookings"
    )
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancel_reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Bron"
        verbose_name_plural = "Bronlar"
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["check_in_date"]),
            models.Index(fields=["check_out_date"]),
        ]

    def __str__(self):
        return self.booking_code

    @property
    def payment_summary(self):
        paid = self.payments.filter(status="PAID").aggregate(total=models.Sum("amount"))["total"] or 0
        return {"total_price": self.total_price, "paid": paid, "remaining": self.total_price - paid}


class Guest(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="guests")
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20, blank=True)
    document_number = models.CharField(max_length=50, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    is_primary = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Mehmon"
        verbose_name_plural = "Mehmonlar"

    def __str__(self):
        return self.full_name


class BookingStatusHistory(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="history")
    old_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey("accounts.TelegramUser", null=True, blank=True, on_delete=models.SET_NULL)
    changed_at = models.DateTimeField(auto_now_add=True)
    comment = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "Bron holati tarixi"
        verbose_name_plural = "Bron holati tarixi"
        ordering = ["-changed_at"]

    def __str__(self):
        return f"{self.booking.booking_code}: {self.old_status} -> {self.new_status}"
