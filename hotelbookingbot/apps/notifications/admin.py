from django.contrib import admin

from .models import Notification, PromoCode, Review


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "notif_type", "is_sent", "created_at")
    list_filter = ("notif_type", "is_sent")
    search_fields = ("title", "user__telegram_id")


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ("code", "discount_percent", "valid_from", "valid_to", "used_count", "max_uses", "is_active")
    list_filter = ("is_active",)
    search_fields = ("code",)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("booking", "user", "rating", "created_at")
    list_filter = ("rating",)
    search_fields = ("booking__booking_code",)
