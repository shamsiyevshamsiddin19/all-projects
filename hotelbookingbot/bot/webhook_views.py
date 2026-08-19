"""Production webhook rejimi uchun ASGI view (uvicorn/daphne kabi ASGI server talab qiladi).

Ishga tushirish: BOT_MODE=webhook bo'lsa, `python manage.py run_bot` webhookni
o'rnatadi (setup_webhook) va so'ngra Django ASGI serveri (config.asgi:application,
uvicorn orqali) shu view'ga kelgan yangilanishlarni qabul qiladi.
"""

import json

from aiogram.types import Update
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

_bot = None
_dispatcher = None


def _get_bot_and_dispatcher():
    global _bot, _dispatcher
    if _bot is None:
        from .main import create_bot, create_dispatcher

        _bot = create_bot()
        _dispatcher = create_dispatcher()
    return _bot, _dispatcher


@csrf_exempt
async def telegram_webhook(request):
    if request.method != "POST":
        return HttpResponse(status=405)

    secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if settings.BOT_WEBHOOK_SECRET and secret != settings.BOT_WEBHOOK_SECRET:
        return HttpResponse(status=403)

    bot, dp = _get_bot_and_dispatcher()
    update = Update.model_validate(json.loads(request.body), context={"bot": bot})
    await dp.feed_update(bot, update)
    return JsonResponse({"ok": True})
