from django.conf import settings
from django.db import models
from django.urls import reverse

from .validators import validate_slug


class ServerQuerySet(models.QuerySet):
    def alive(self):
        return self.filter(is_deleted=False)


class Server(models.Model):
    """A user-named deployment target that owns one subdomain."""

    class Status(models.TextChoices):
        PROVISIONING = "provisioning", "Tayyorlanmoqda"
        READY = "ready", "Tayyor"
        SUSPENDED = "suspended", "To'xtatilgan"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="servers"
    )
    name = models.CharField("nom", max_length=80)
    slug = models.SlugField(
        "subdomen", max_length=63, unique=True, validators=[validate_slug],
        help_text="<slug>.whost.uz sifatida beriladi",
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PROVISIONING
    )
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ServerQuerySet.as_manager()

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "server"
        verbose_name_plural = "serverlar"
        indexes = [models.Index(fields=["owner", "is_deleted"])]

    def __str__(self):
        return f"{self.name} ({self.domain})"

    def get_absolute_url(self):
        return reverse("servers:detail", args=[self.slug])

    @property
    def domain(self) -> str:
        return f"{self.slug}.{settings.PLATFORM_DOMAIN}"

    @property
    def url(self) -> str:
        return f"https://{self.domain}"

    @property
    def ssh_remote(self) -> str:
        """What the user pastes into `git remote add`."""
        return f"git@git.{settings.PLATFORM_DOMAIN}:{self.slug}.git"

    @property
    def active_key(self):
        return self.ssh_keys.filter(is_revoked=False).first()


class SshKey(models.Model):
    """Public half of a keypair. The private half is never stored here."""

    server = models.ForeignKey(
        Server, on_delete=models.CASCADE, related_name="ssh_keys"
    )
    public_key = models.TextField("ochiq kalit")
    fingerprint = models.CharField(max_length=64, unique=True, db_index=True)
    is_revoked = models.BooleanField(default=False)
    downloaded_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "SSH kalit"
        verbose_name_plural = "SSH kalitlar"

    def __str__(self):
        return f"{self.server.slug} — {self.fingerprint[:24]}…"

    @property
    def filename(self) -> str:
        return f"{self.server.slug}_ed25519"
