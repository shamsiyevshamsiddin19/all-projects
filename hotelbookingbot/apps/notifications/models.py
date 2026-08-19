from django.db import models

from apps.bookings.models import Booking


class NotificationType(models.TextChoices):
    BOOKING_CONFIRMED = "BOOKING_CONFIRMED", "Bron tasdiqlandi"
    BOOKING_CANCELLED = "BOOKING_CANCELLED", "Bron bekor qilindi"
    REMINDER = "REMINDER", "Eslatma"
    PROMO = "PROMO", "Aksiya"
    SYSTEM = "SYSTEM", "Tizim"


class Notification(models.Model):
    user = models.ForeignKey("accounts.TelegramUser", on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=255)
    message = models.TextField()
    notif_type = models.CharField(max_length=30, choices=NotificationType.choices)
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Bildirishnoma"
        verbose_name_plural = "Bildirishnomalar"

    def __str__(self):
        return f"{self.title} -> {self.user}"


class PromoCode(models.Model):
    code = models.CharField(max_length=30, unique=True)
    discount_percent = models.PositiveSmallIntegerField()
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    max_uses = models.PositiveIntegerField(null=True, blank=True)
    used_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Promo kod"
        verbose_name_plural = "Promo kodlar"

    def __str__(self):
        return self.code

    def is_valid(self, now=None):
        from django.utils import timezone

        now = now or timezone.now()
        if not self.is_active or not (self.valid_from <= now <= self.valid_to):
            return False
        if self.max_uses is not None and self.used_count >= self.max_uses:
            return False
        return True


class Review(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name="review")
    user = models.ForeignKey("accounts.TelegramUser", on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Sharh"
        verbose_name_plural = "Sharhlar"

    def __str__(self):
        return f"{self.booking.booking_code}: {self.rating}/5"
