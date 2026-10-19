from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    """Email is the identifier — there is no separate username."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra):
        if not email:
            raise ValueError("Email majburiy")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra):
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra)

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        if extra.get("is_staff") is not True:
            raise ValueError("Superuser is_staff=True bo'lishi kerak")
        if extra.get("is_superuser") is not True:
            raise ValueError("Superuser is_superuser=True bo'lishi kerak")
        return self._create_user(email, password, **extra)


class User(AbstractUser):
    username = None
    email = models.EmailField("email", unique=True)
    full_name = models.CharField("to'liq ism", max_length=150, blank=True)
    avatar_url = models.URLField("avatar", blank=True)

    # Free tier until billing lands (docs/05-tariflar-va-billing.md)
    plan = models.CharField(max_length=20, default="free")
    server_limit = models.PositiveIntegerField(default=3)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = "foydalanuvchi"
        verbose_name_plural = "foydalanuvchilar"

    def __str__(self):
        return self.email

    @property
    def display_name(self) -> str:
        return self.full_name or self.email.split("@")[0]

    def can_create_server(self) -> bool:
        return self.servers.filter(is_deleted=False).count() < self.server_limit
