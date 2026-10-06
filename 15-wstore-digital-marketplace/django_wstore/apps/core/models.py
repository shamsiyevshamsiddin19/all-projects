import uuid
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
