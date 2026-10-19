"""Subdomain rules — these guard a public DNS namespace, keep them strict."""
import re

from django.core.exceptions import ValidationError

SLUG_RE = re.compile(r"^[a-z0-9]([a-z0-9-]{1,61}[a-z0-9])?$")

# Anything that could impersonate platform infrastructure or break mail/TLS.
RESERVED_SLUGS = {
    "www", "api", "admin", "administrator", "root", "mail", "smtp", "imap",
    "pop", "pop3", "webmail", "ns", "ns1", "ns2", "dns", "mx", "ftp", "sftp",
    "ssh", "git", "registry", "docker", "cdn", "static", "assets", "img",
    "images", "media", "files", "download", "downloads", "status", "health",
    "dashboard", "panel", "console", "account", "accounts", "auth", "login",
    "logout", "signup", "signin", "register", "billing", "pay", "payment",
    "checkout", "invoice", "support", "help", "docs", "doc", "blog", "news",
    "about", "contact", "legal", "privacy", "terms", "security", "abuse",
    "postmaster", "hostmaster", "webmaster", "noc", "test", "staging", "dev",
    "demo", "beta", "alpha", "preview", "internal", "private", "vpn", "proxy",
    "gateway", "monitor", "metrics", "grafana", "prometheus", "loki", "redis",
    "db", "database", "postgres", "mysql", "backup", "nexcloud", "whost",
    "autoconfig", "autodiscover", "_domainkey", "dmarc", "spf",
}


def validate_slug(value: str) -> None:
    """Raise ValidationError unless `value` is a safe, free-standing label."""
    if not value:
        raise ValidationError("Nom bo'sh bo'lishi mumkin emas.")
    if len(value) < 3:
        raise ValidationError("Nom kamida 3 ta belgidan iborat bo'lishi kerak.")
    if len(value) > 63:
        raise ValidationError("Nom 63 ta belgidan oshmasligi kerak.")
    if not SLUG_RE.match(value):
        raise ValidationError(
            "Faqat kichik lotin harflari, raqamlar va defis (-) ishlatiladi. "
            "Defis bilan boshlanmasligi va tugamasligi kerak."
        )
    if "--" in value:
        raise ValidationError("Ketma-ket ikkita defis ishlatib bo'lmaydi.")
    if value in RESERVED_SLUGS:
        raise ValidationError(f"«{value}» — band nom, boshqasini tanlang.")
    if value.startswith("xn--"):
        raise ValidationError("«xn--» bilan boshlanadigan nomlar ishlatilmaydi.")
