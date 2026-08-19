from django.contrib import admin
from import_export.admin import ExportMixin

from .models import TelegramUser


@admin.register(TelegramUser)
class TelegramUserAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ("telegram_id", "full_name_display", "username", "role", "is_blocked", "registered_at")
    list_filter = ("role", "is_blocked", "language")
    search_fields = ("telegram_id", "username", "first_name", "last_name", "phone_number")
    actions = ["block_users", "unblock_users"]
    readonly_fields = ("telegram_id", "registered_at", "last_activity_at")

    @admin.display(description="F.I.Sh.")
    def full_name_display(self, obj):
        return obj.full_name

    @admin.action(description="Tanlangan foydalanuvchilarni bloklash")
    def block_users(self, request, queryset):
        queryset.update(is_blocked=True)

    @admin.action(description="Tanlangan foydalanuvchilarni blokdan chiqarish")
    def unblock_users(self, request, queryset):
        queryset.update(is_blocked=False)
