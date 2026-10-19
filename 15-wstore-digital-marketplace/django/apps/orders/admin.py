from django.contrib import admin
from django.db.models import F
from django.utils import timezone
from .models import Order, ClickTransaction, Withdrawal

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id_short", "buyer", "product", "amount_display", "status", "provider", "created_at")
    list_filter = ("status", "provider", "created_at")
    search_fields = ("id", "buyer__username", "buyer__email", "product__title", "download_token")

    def id_short(self, obj):
        return f"#{str(obj.id)[:8]}"
    id_short.short_description = "ID"

    def amount_display(self, obj):
        return f"{int(obj.amount):,} so'm".replace(",", " ")
    amount_display.short_description = "Summa"


@admin.register(ClickTransaction)
class ClickTransactionAdmin(admin.ModelAdmin):
    list_display = ("id", "merchant_trans_id", "kind", "amount_display", "status", "click_trans_id", "created_at")
    list_filter = ("kind", "status", "created_at")
    search_fields = ("id", "merchant_trans_id", "click_trans_id", "order__id", "product__title")

    def amount_display(self, obj):
        return f"{int(obj.amount):,} so'm".replace(",", " ")
    amount_display.short_description = "Summa"


@admin.register(Withdrawal)
class WithdrawalAdmin(admin.ModelAdmin):
    list_display = ("id_short", "seller", "amount_display", "masked_card", "status", "created_at", "paid_at")
    list_filter = ("status", "created_at")
    search_fields = ("seller__username", "seller__email", "card_number")
    actions = ["mark_paid", "mark_rejected"]

    def id_short(self, obj):
        return f"#{str(obj.id)[:8]}"
    id_short.short_description = "ID"

    def amount_display(self, obj):
        return f"{int(obj.amount):,} so'm".replace(",", " ")
    amount_display.short_description = "Summa"

    @admin.action(description="Tanlangan so'rovlarni to'langan (PAID) deb belgilash")
    def mark_paid(self, request, queryset):
        count = queryset.update(status=Withdrawal.WithdrawalStatus.PAID, paid_at=timezone.now())
        self.message_user(request, f"{count} ta pul yechish so'rovi to'landi deb belgilandi.")

    @admin.action(description="Tanlangan so'rovlarni rad etish (REJECTED) va mablag'ni balansga qaytarish")
    def mark_rejected(self, request, queryset):
        count = 0
        for w in queryset.filter(status=Withdrawal.WithdrawalStatus.PENDING):
            w.status = Withdrawal.WithdrawalStatus.REJECTED
            w.save(update_fields=["status"])
            # refund balance to seller (F() — atomik)
            type(w.seller).objects.filter(pk=w.seller_id).update(
                balance=F("balance") + w.amount
            )
            count += 1
        self.message_user(request, f"{count} ta so'rov rad etildi va mablag' sotuvchilar balansiga qaytarildi.")
