from django.db import models

from apps.bookings.models import Booking


class PaymentMethod(models.TextChoices):
    CASH = "CASH", "Naqd"
    CARD = "CARD", "Karta (terminal)"
    CLICK = "CLICK", "Click"
    BANK_TRANSFER = "BANK_TRANSFER", "Bank o'tkazmasi"


class PaymentState(models.TextChoices):
    PENDING = "PENDING", "Kutilmoqda"
    PAID = "PAID", "To'landi"
    FAILED = "FAILED", "Muvaffaqiyatsiz"
    REFUNDED = "REFUNDED", "Qaytarildi"
    PARTIALLY_PAID = "PARTIALLY_PAID", "Qisman to'landi"


class PaymentStatus(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="UZS")
    method = models.CharField(max_length=20, choices=PaymentMethod.choices)
    status = models.CharField(max_length=20, choices=PaymentState.choices, default=PaymentState.PENDING)
    transaction_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "To'lov"
        verbose_name_plural = "To'lovlar"

    def __str__(self):
        return f"{self.booking.booking_code} — {self.amount} {self.currency} ({self.status})"


class ClickTransaction(models.Model):
    """Click Merchant API so'rovlari uchun audit jadval (idempotentlik va debugging uchun)."""

    payment = models.ForeignKey(PaymentStatus, on_delete=models.CASCADE, related_name="click_transactions")
    click_trans_id = models.CharField(max_length=50, db_index=True)
    click_paydoc_id = models.CharField(max_length=50, blank=True)
    merchant_trans_id = models.CharField(max_length=50, db_index=True)
    action = models.PositiveSmallIntegerField(help_text="0=Prepare, 1=Complete")
    error_code = models.IntegerField(default=0)
    raw_request = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Click tranzaksiyasi"
        verbose_name_plural = "Click tranzaksiyalari"
