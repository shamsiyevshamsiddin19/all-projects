from django.apps import AppConfig


class PaymentsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.payments"
    verbose_name = "To'lovlar"

    def ready(self):
        from . import signals  # noqa: F401
