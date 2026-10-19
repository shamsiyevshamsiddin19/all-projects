import uuid
from decimal import Decimal
from django.conf import settings
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext, gettext_lazy as _

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name=_("Kategoriya nomi"))
    slug = models.SlugField(max_length=100, unique=True, verbose_name=_("Slug"))
    icon = models.CharField(max_length=50, default="box", verbose_name=_("Ikonka nomi"))

    class Meta:
        verbose_name = _("Kategoriya")
        verbose_name_plural = _("Kategoriyalar")
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def display_name(self):
        """
        Kategoriya nomini joriy tilda qaytaradi.

        Kategoriyalar — saytning o'z taksonomiyasi (mahsulot nomlaridan farqli
        ravishda foydalanuvchi yozgan matn emas), shuning uchun nomlari tarjima
        katalogiga kiritilgan. Katalogda yo'q nom (admin qo'shgan yangi
        kategoriya) o'z holicha qaytadi.
        """
        return gettext(self.name)


class Product(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", _("Qoralama (to'lov kutilmoqda)")
        PENDING = "PENDING", _("Moderatsiyada")
        ACTIVE = "ACTIVE", _("Faol (sotuvda)")
        REJECTED = "REJECTED", _("Rad etilgan")
        PAUSED = "PAUSED", _("Vaqtincha to'xtatilgan")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, verbose_name=_("Sarlavha"))
    slug = models.SlugField(max_length=255, unique=True, verbose_name=_("Slug"))
    description = models.TextField(verbose_name=_("Batafsil tavsif"))
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_("Narxi (USD)")
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="products",
        verbose_name=_("Kategoriya")
    )
    subcategory = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name=_("Ichki toifa")
    )
    tech_stack = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_("Texnologiyalar")
    )
    features = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_("Xususiyatlar ro'yxati")
    )
    
    # Images
    cover_image_file = models.ImageField(
        upload_to="covers/",
        blank=True,
        null=True,
        verbose_name=_("Muqova rasmi (fayl)")
    )
    cover_image_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name=_("Muqova rasmi (havola)")
    )
    screenshots = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_("Skrinshotlar havolalari")
    )
    
    # Source code archive
    file_archive = models.FileField(
        upload_to="products/archives/",
        blank=True,
        null=True,
        verbose_name=_("Loyiha ZIP arxivi")
    )
    file_key = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_("Tashqi fayl kaliti")
    )

    demo_url = models.URLField(
        blank=True,
        null=True,
        verbose_name=_("Jonli demo havola")
    )
    telegram_username = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_("Sotuvchining Telegram username'i")
    )
    badge = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name=_("Belgi/Badge (masalan: TOP SOTUV)")
    )
    rating = models.FloatField(default=0.0, verbose_name=_("Reyting"))
    sales_count = models.PositiveIntegerField(default=0, verbose_name=_("Sotuvlar soni"))

    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="products",
        verbose_name=_("Sotuvchi")
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name=_("Holati")
    )
    is_deleted = models.BooleanField(
        default=False,
        verbose_name=_("O'chirilgan (arxiv)")
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Yaratilgan vaqti"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Yangilangan vaqti"))

    class Meta:
        verbose_name = _("Mahsulot")
        verbose_name_plural = _("Mahsulotlar")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.price} USD)"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title) or "product"
            candidate = base_slug
            count = 1
            while Product.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                candidate = f"{base_slug}-{count}"
                count += 1
            self.slug = candidate
        super().save(*args, **kwargs)

    @property
    def display_badge(self):
        """
        Badge saytning o'z yorlig'i ("TOP SOTUV", "YANGI"), mahsulot nomidan
        farqli ravishda sotuvchi matni emas — shuning uchun tarjima qilinadi.
        Katalogda yo'q qiymat o'z holicha qaytadi.
        """
        return gettext(self.badge) if self.badge else ""

    @property
    def cover_url(self):
        if self.cover_image_file:
            return self.cover_image_file.url
        if self.cover_image_url:
            return self.cover_image_url
        return "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800&q=80"

    @property
    def price_som(self):
        return int(self.price * settings.PRODUCT_UZS_RATE)

    @property
    def reviews_count(self):
        return self.reviews.count()

    def update_rating(self):
        reviews = self.reviews.all()
        if reviews.exists():
            avg = sum(r.rating for r in reviews) / reviews.count()
            self.rating = round(avg, 1)
        else:
            self.rating = 0.0
        self.save(update_fields=["rating"])


class Review(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name=_("Mahsulot")
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name=_("Foydalanuvchi")
    )
    rating = models.PositiveSmallIntegerField(
        default=5,
        verbose_name=_("Baho (1-5)")
    )
    comment = models.TextField(verbose_name=_("Izoh matni"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Yozilgan vaqti"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Yangilangan vaqti"))

    class Meta:
        verbose_name = _("Sharh")
        verbose_name_plural = _("Sharhlar")
        unique_together = ("product", "user")
        ordering = ["-created_at"]

    @property
    def is_verified_buyer(self):
        from orders.models import Order
        return Order.objects.filter(buyer=self.user, product=self.product, status=Order.PayStatus.PAID).exists()

    def __str__(self):
        return f"{self.user} -> {self.product.title} ({self.rating}★)"


class Wishlist(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wishlist_items",
        verbose_name=_("Foydalanuvchi")
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="wishlisted_by",
        verbose_name=_("Mahsulot")
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Qo'shilgan vaqti"))

    class Meta:
        verbose_name = _("Sevimlilar")
        verbose_name_plural = _("Sevimlilar")
        unique_together = ("user", "product")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} ❤️ {self.product.title}"


class Report(models.Model):
    class ReportStatus(models.TextChoices):
        OPEN = "OPEN", _("Ko'rib chiqilmagan")
        RESOLVED = "RESOLVED", _("Hal qilingan")

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="reports",
        verbose_name=_("Mahsulot")
    )
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="filed_reports",
        verbose_name=_("Shikoyat qiluvchi")
    )
    reason = models.CharField(max_length=200, verbose_name=_("Sabab"))
    comment = models.TextField(blank=True, null=True, verbose_name=_("Qo'shimcha izoh"))
    status = models.CharField(
        max_length=20,
        choices=ReportStatus.choices,
        default=ReportStatus.OPEN,
        verbose_name=_("Holati")
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Shikoyat vaqti"))

    class Meta:
        verbose_name = _("Shikoyat")
        verbose_name_plural = _("Shikoyatlar")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Shikoyat #{self.id} — {self.product.title} ({self.reason})"
