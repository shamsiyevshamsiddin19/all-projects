from django.conf import settings
from django.db import models


class RoleChoices(models.TextChoices):
    GUEST = "GUEST", "Mehmon"
    OPERATOR = "OPERATOR", "Operator"
    MANAGER = "MANAGER", "Menejer"
    ADMIN = "ADMIN", "Administrator"
    SUPERADMIN = "SUPERADMIN", "Bosh administrator"


STAFF_ROLES = (RoleChoices.OPERATOR, RoleChoices.MANAGER, RoleChoices.ADMIN, RoleChoices.SUPERADMIN)


class LanguageChoices(models.TextChoices):
    UZ = "uz", "O'zbek"
    RU = "ru", "Русский"
    EN = "en", "English"


class TelegramUser(models.Model):
    telegram_id = models.BigIntegerField(unique=True, db_index=True)
    username = models.CharField(max_length=150, null=True, blank=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    language = models.CharField(max_length=2, choices=LanguageChoices.choices, default=LanguageChoices.UZ)
    role = models.CharField(max_length=20, choices=RoleChoices.choices, default=RoleChoices.GUEST, db_index=True)
    linked_admin_user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="telegram_profile",
    )
    is_blocked = models.BooleanField(default=False, db_index=True)
    is_active = models.BooleanField(default=True)
    registered_at = models.DateTimeField(auto_now_add=True)
    last_activity_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Telegram foydalanuvchi"
        verbose_name_plural = "Telegram foydalanuvchilar"
        indexes = [
            models.Index(fields=["telegram_id"]),
            models.Index(fields=["role"]),
            models.Index(fields=["is_blocked"]),
        ]

    def __str__(self):
        return f"{self.full_name} ({self.telegram_id})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def is_staff_role(self):
        return self.role in STAFF_ROLES

    @property
    def active_bookings_count(self):
        return self.bookings.filter(status__in=["PENDING", "CONFIRMED", "CHECKED_IN"]).count()
