from django.contrib import admin
from django.utils import timezone

from .models import PaymentState, PaymentStatus


@admin.register(PaymentStatus)
class PaymentStatusAdmin(admin.ModelAdmin):
    list_display = ("booking", "amount", "method", "status", "paid_at")
    list_filter = ("method", "status")
    search_fields = ("booking__booking_code", "transaction_id")
    actions = ["mark_as_paid", "mark_as_refunded"]

    @admin.action(description="To'landi deb belgilash")
    def mark_as_paid(self, request, queryset):
        for payment in queryset:
            payment.status = PaymentState.PAID
            payment.paid_at = timezone.now()
            payment.save()  # signal orqali Booking avtomatik CONFIRMED bo'ladi

    @admin.action(description="Qaytarildi deb belgilash")
    def mark_as_refunded(self, request, queryset):
        for payment in queryset:
            payment.status = PaymentState.REFUNDED
            payment.save()
