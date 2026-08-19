from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from import_export.admin import ExportMixin

from apps.payments.models import PaymentStatus

from .models import Booking, BookingStatus, BookingStatusHistory, Guest
from .services import set_booking_status

STATUS_COLORS = {
    BookingStatus.PENDING: "#f0ad4e",
    BookingStatus.CONFIRMED: "#5cb85c",
    BookingStatus.CHECKED_IN: "#5bc0de",
    BookingStatus.CHECKED_OUT: "#6c757d",
    BookingStatus.CANCELLED: "#d9534f",
    BookingStatus.EXPIRED: "#d9534f",
}


class GuestInline(admin.TabularInline):
    model = Guest
    extra = 0


class PaymentStatusInline(admin.TabularInline):
    model = PaymentStatus
    extra = 0
    fields = ("amount", "currency", "method", "status", "paid_at")


class BookingStatusHistoryInline(admin.TabularInline):
    model = BookingStatusHistory
    extra = 0
    readonly_fields = ("old_status", "new_status", "changed_by", "changed_at", "comment")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Booking)
class BookingAdmin(ExportMixin, admin.ModelAdmin):
    list_display = (
        "booking_code",
        "user_link",
        "room_type",
        "check_in_date",
        "check_out_date",
        "status_badge",
        "total_price",
        "payment_status_display",
    )
    list_filter = ("status", "room_type", "check_in_date", "room_type__hotel")
    search_fields = ("booking_code", "user__telegram_id", "user__phone_number", "user__first_name")
    date_hierarchy = "check_in_date"
    inlines = [GuestInline, PaymentStatusInline, BookingStatusHistoryInline]
    actions = ["confirm_bookings", "cancel_bookings", "mark_checked_in", "mark_checked_out"]
    readonly_fields = ("booking_code", "nights", "total_price", "created_at", "updated_at")

    @admin.display(description="Mehmon")
    def user_link(self, obj):
        url = reverse("admin:accounts_telegramuser_change", args=[obj.user_id])
        return format_html('<a href="{}">{}</a>', url, obj.user.full_name)

    @admin.display(description="Holat")
    def status_badge(self, obj):
        color = STATUS_COLORS.get(obj.status, "#999")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:10px;font-size:11px;">{}</span>',
            color,
            obj.get_status_display(),
        )

    @admin.display(description="To'lov")
    def payment_status_display(self, obj):
        summary = obj.payment_summary
        return f"{summary['paid']} / {summary['total_price']}"

    def _bulk_transition(self, request, queryset, new_status, comment):
        for booking in queryset:
            set_booking_status(booking, new_status, changed_by=None, comment=comment)

    @admin.action(description="Tasdiqlash")
    def confirm_bookings(self, request, queryset):
        self._bulk_transition(request, queryset.filter(status=BookingStatus.PENDING), BookingStatus.CONFIRMED, "Admin panel orqali tasdiqlandi")

    @admin.action(description="Bekor qilish")
    def cancel_bookings(self, request, queryset):
        self._bulk_transition(request, queryset, BookingStatus.CANCELLED, "Admin panel orqali bekor qilindi")

    @admin.action(description="Check-in belgilash")
    def mark_checked_in(self, request, queryset):
        self._bulk_transition(request, queryset.filter(status=BookingStatus.CONFIRMED), BookingStatus.CHECKED_IN, "Check-in")

    @admin.action(description="Check-out belgilash")
    def mark_checked_out(self, request, queryset):
        self._bulk_transition(request, queryset.filter(status=BookingStatus.CHECKED_IN), BookingStatus.CHECKED_OUT, "Check-out")

    def save_model(self, request, obj, form, change):
        if change:
            original = Booking.objects.get(pk=obj.pk)
            if original.status != obj.status:
                super().save_model(request, obj, form, change)
                BookingStatusHistory.objects.create(
                    booking=obj, old_status=original.status, new_status=obj.status, comment="Admin panel orqali o'zgartirildi"
                )
                return
        super().save_model(request, obj, form, change)
