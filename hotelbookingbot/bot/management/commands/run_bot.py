import asyncio

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Telegram botni ishga tushiradi (BOT_MODE=polling yoki webhook)"

    def handle(self, *args, **options):
        if not settings.BOT_TOKEN:
            self.stderr.write(self.style.ERROR("BOT_TOKEN sozlanmagan (.env fayliga qarang)"))
            return

        if settings.BOT_MODE == "webhook":
            from bot.main import setup_webhook

            asyncio.run(setup_webhook())
            self.stdout.write(
                self.style.SUCCESS(
                    "Webhook o'rnatildi. Yangilanishlarni qabul qilish uchun ASGI serverni ishga tushiring: "
                    "uvicorn config.asgi:application"
                )
            )
            return

        from bot.main import run_polling

        self.stdout.write(self.style.SUCCESS("Bot polling rejimida ishga tushmoqda..."))
        asyncio.run(run_polling())
