from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, ErrorLog

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "email", "role", "balance_display", "referral_code", "referrals_count", "is_staff")
    list_filter = ("role", "is_staff", "is_superuser", "created_at")
    search_fields = ("username", "email", "first_name", "last_name", "referral_code", "google_id")
    fieldsets = BaseUserAdmin.fieldsets + (
        ("wstore Qo'shimcha Sozlamalar", {
            "fields": ("role", "balance", "avatar", "google_id", "referral_code", "referred_by", "referral_bonus_paid")
        }),
    )

    def balance_display(self, obj):
        return f"{int(obj.balance):,} so'm".replace(",", " ")
    balance_display.short_description = "Balans"

    def referrals_count(self, obj):
        return obj.referrals.count()
    referrals_count.short_description = "Taklif qilganlar"


@admin.register(ErrorLog)
class ErrorLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "context", "short_message")
    list_filter = ("created_at",)
    search_fields = ("message", "context")
    readonly_fields = ("created_at",)

    def short_message(self, obj):
        return obj.message[:80]
    short_message.short_description = "Xabar"
