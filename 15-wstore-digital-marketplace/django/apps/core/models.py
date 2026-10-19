import hashlib
import secrets
import uuid
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

def generate_referral_code():
    return uuid.uuid4().hex[:12]

class User(AbstractUser):
    class Role(models.TextChoices):
        BUYER = "BUYER", _("Xaridor")
        SELLER = "SELLER", _("Sotuvchi")
        ADMIN = "ADMIN", _("Admin")

    email = models.EmailField(_("Email manzili"), unique=True)
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.BUYER,
        verbose_name=_("Rol")
    )
    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Balans (so'm)")
    )
    avatar = models.URLField(max_length=500, blank=True, null=True, verbose_name=_("Avatar havolasi"))

    # Google hisobining doimiy identifikatori (OpenID `sub`). Faqat email
    # bo'yicha bog'lash yetarli emas: foydalanuvchi Google'dagi emailini
    # o'zgartirsa, keyingi safar u yangi hisob bo'lib qolardi.
    google_id = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        unique=True,
        db_index=True,
        verbose_name=_("Google ID"),
    )
    
    # Referral system
    referral_code = models.CharField(
        max_length=32,
        unique=True,
        default=generate_referral_code,
        verbose_name=_("Referal kodi")
    )
    referred_by = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="referrals",
        verbose_name=_("Taklif qilgan foydalanuvchi")
    )
    referral_bonus_paid = models.BooleanField(
        default=False,
        verbose_name=_("Referal bonusi to'landimi")
    )

    # ---- Sotuvchi profili ----
    # Sotuvchi bo'lish uchun to'ldiriladigan qo'shimcha ma'lumotlar.
    # `seller_since` to'lgan bo'lsa — foydalanuvchi onboarding'dan o'tgan.
    telegram_username = models.CharField(
        max_length=100, blank=True, null=True,
        verbose_name=_("Telegram username"),
        help_text=_("Xaridorlar siz bilan shu orqali bog'lanadi"),
    )
    card_number = models.CharField(
        max_length=30, blank=True, null=True,
        verbose_name=_("Karta raqami (Uzcard/Humo)"),
        help_text=_("Sotuvdan tushgan mablag' shu kartaga yechiladi"),
    )
    bio = models.TextField(
        blank=True, null=True, max_length=500,
        verbose_name=_("O'zingiz haqingizda"),
    )
    website = models.URLField(
        blank=True, null=True,
        verbose_name=_("Shaxsiy sayt yoki portfolio"),
    )
    seller_since = models.DateTimeField(
        blank=True, null=True,
        verbose_name=_("Sotuvchi bo'lgan sana"),
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Ro'yxatdan o'tgan"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Yangilangan"))

    class Meta:
        verbose_name = _("Foydalanuvchi")
        verbose_name_plural = _("Foydalanuvchilar")
        ordering = ["-created_at"]

    def __str__(self):
        return self.get_full_name() or self.username or self.email

    @property
    def display_name(self):
        return self.get_full_name() or self.first_name or self.username or self.email.split("@")[0]

    @property
    def initials(self):
        name = self.display_name.strip()
        return name[0].upper() if name else "?"

    @property
    def is_seller(self):
        return self.role in [self.Role.SELLER, self.Role.ADMIN] or self.is_staff

    @property
    def seller_onboarded(self):
        """
        Sotuvchi anketasini to'ldirganmi.

        `is_seller` dan farqi: u faqat rolni tekshiradi, bu esa
        «Sotuvchi bo'lish» qadamidan o'tganini bildiradi. Sotuvchi paneli
        va API kalitlari aynan shunga qarab ochiladi.
        """
        return bool(self.seller_since)

    @property
    def is_admin_user(self):
        return self.role == self.Role.ADMIN or self.is_staff or self.is_superuser


class ErrorLog(models.Model):
    message = models.TextField(verbose_name=_("Xabar"))
    stack = models.TextField(blank=True, null=True, verbose_name=_("Xatolik steki"))
    context = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Kontekst/URL"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Yuz bergan vaqti"))

    class Meta:
        verbose_name = _("Tizim xatoligi")
        verbose_name_plural = _("Tizim xatoliklari")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.created_at.strftime('%Y-%m-%d %H:%M')}: {self.message[:60]}"


class ApiToken(models.Model):
    """
    Sotuvchining API kaliti — tashqi skript yoki AI agent uning nomidan
    mahsulot yuklashi/tahrirlashi va sotuv statistikasini o'qishi uchun.

    Token BAZAGA OCHIQ HOLDA YOZILMAYDI: faqat SHA-256 xeshi saqlanadi.
    To'liq qiymat foydalanuvchiga bir marta — yaratilgan payti ko'rsatiladi.
    Shuning uchun baza sizib chiqsa ham kalitlar bilan hech narsa qilib
    bo'lmaydi (parollar qanday saqlansa, shu mantiq).

    Kalit FAQAT egasining o'z ma'lumotlariga yo'l ochadi — API'dagi har bir
    so'rov `token.user` bo'yicha filtrlanadi.
    """

    PREFIX = "wst_"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="api_tokens",
        verbose_name=_("Egasi"),
    )
    name = models.CharField(
        max_length=80,
        verbose_name=_("Nomi"),
        help_text=_("Masalan: «AI yuklovchi» yoki «Lokal skript»"),
    )
    token_hash = models.CharField(max_length=64, unique=True, db_index=True)
    # Ro'yxatda ko'rsatish uchun — to'liq token emas, faqat boshi
    token_prefix = models.CharField(max_length=16, verbose_name=_("Ko'rinishi"))

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Yaratilgan"))
    last_used_at = models.DateTimeField(blank=True, null=True, verbose_name=_("Oxirgi ishlatilgan"))
    revoked_at = models.DateTimeField(blank=True, null=True, verbose_name=_("Bekor qilingan"))

    class Meta:
        verbose_name = _("API kalit")
        verbose_name_plural = _("API kalitlar")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.token_prefix}…)"

    @property
    def is_active(self):
        return self.revoked_at is None

    @staticmethod
    def hash_token(raw):
        return hashlib.sha256(raw.encode()).hexdigest()

    @classmethod
    def generate(cls, user, name):
        """
        Yangi kalit yaratadi va (obyekt, ochiq_token) juftligini qaytaradi.
        Ochiq token shu yerdan boshqa hech qayerda saqlanmaydi.
        """
        raw = cls.PREFIX + secrets.token_urlsafe(32)
        token = cls.objects.create(
            user=user,
            name=name.strip()[:80] or "API kalit",
            token_hash=cls.hash_token(raw),
            token_prefix=raw[:12],
        )
        return token, raw

    @classmethod
    def authenticate(cls, raw):
        """
        Ochiq token bo'yicha faol kalitni topadi. Topilmasa None.
        Xeshdan qidiriladi — bazada ochiq token yo'q.
        """
        if not raw or not raw.startswith(cls.PREFIX):
            return None
        return (
            cls.objects.select_related("user")
            .filter(token_hash=cls.hash_token(raw), revoked_at__isnull=True)
            .first()
        )

    def touch(self):
        """Oxirgi ishlatilgan vaqtni yangilaydi (har so'rovda chaqiriladi)."""
        from django.utils import timezone
        self.last_used_at = timezone.now()
        self.save(update_fields=["last_used_at"])
