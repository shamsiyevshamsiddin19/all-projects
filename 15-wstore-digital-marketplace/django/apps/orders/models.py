import uuid
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

class Order(models.Model):
    class PayStatus(models.TextChoices):
        PENDING = "PENDING", _("Kutilmoqda")
        PAID = "PAID", _("To'landi")
        FAILED = "FAILED", _("Bekor qilindi")
        REFUNDED = "REFUNDED", _("Qaytarildi")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders",
        verbose_name=_("Xaridor")
    )
    product = models.ForeignKey(
        "store.Product",
        on_delete=models.CASCADE,
        related_name="orders",
        verbose_name=_("Mahsulot")
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_("Summa (so'm)")
    )
    status = models.CharField(
        max_length=20,
        choices=PayStatus.choices,
        default=PayStatus.PENDING,
        verbose_name=_("Holati")
    )
    provider = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name=_("To'lov usuli (click, payme, balance)")
    )
    download_token = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        unique=True,
        verbose_name=_("Yuklab olish xavfsiz tokeni")
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Yaratilgan vaqti"))

    class Meta:
        verbose_name = _("Buyurtma")
        verbose_name_plural = _("Buyurtmalar")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{str(self.id)[:8]} — {self.product.title} ({self.get_status_display()})"


class ClickTransaction(models.Model):
    class ClickKind(models.TextChoices):
        PURCHASE = "PURCHASE", _("Mahsulot xaridi")
        LISTING = "LISTING", _("E'lon to'lovi")

    kind = models.CharField(
        max_length=20,
        choices=ClickKind.choices,
        verbose_name=_("Turi")
    )
    order = models.ForeignKey(
        Order,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="click_transactions",
        verbose_name=_("Buyurtma")
    )
    product = models.ForeignKey(
        "store.Product",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="listing_payments",
        verbose_name=_("Mahsulot (e'lon to'lovi uchun)")
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_("Summa (so'm)")
    )
    status = models.CharField(
        max_length=20,
        choices=Order.PayStatus.choices,
        default=Order.PayStatus.PENDING,
        verbose_name=_("Holati")
    )
    click_trans_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_("Click Tranzaksiya ID")
    )
    merchant_trans_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_("Merchant Tranzaksiya Param (masalan WSTP123)")
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Yaratilgan vaqti"))
    paid_at = models.DateTimeField(blank=True, null=True, verbose_name=_("To'langan vaqti"))

    class Meta:
        verbose_name = _("Click Tranzaksiyasi")
        verbose_name_plural = _("Click Tranzaksiyalari")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Click #{self.id} — {self.merchant_trans_id or self.kind} ({self.amount} so'm)"


class Withdrawal(models.Model):
    class WithdrawalStatus(models.TextChoices):
        PENDING = "PENDING", _("Kutilmoqda")
        PAID = "PAID", _("To'landi")
        REJECTED = "REJECTED", _("Rad etildi")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="withdrawals",
        verbose_name=_("Sotuvchi")
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_("Summa (so'm)")
    )
    card_number = models.CharField(
        max_length=30,
        verbose_name=_("Karta raqami (Uzcard/Humo)")
    )
    status = models.CharField(
        max_length=20,
        choices=WithdrawalStatus.choices,
        default=WithdrawalStatus.PENDING,
        verbose_name=_("Holati")
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("So'rov vaqti"))
    paid_at = models.DateTimeField(blank=True, null=True, verbose_name=_("To'langan vaqti"))

    class Meta:
        verbose_name = _("Pul yechish so'rovi")
        verbose_name_plural = _("Pul yechish so'rovlari")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Withdrawal #{str(self.id)[:8]} — {self.seller.display_name} ({self.amount} so'm)"

    @property
    def masked_card(self):
        cleaned = self.card_number.replace(" ", "")
        if len(cleaned) >= 4:
            return f"**** **** **** {cleaned[-4:]}"
        return self.card_number
