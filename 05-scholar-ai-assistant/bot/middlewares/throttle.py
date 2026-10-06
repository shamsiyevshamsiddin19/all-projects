"""Spam himoyasi — bir foydalanuvchi juda tez-tez bosib AI/serverni yuklamasin.

Oddiy xabar/tugma: 0.6 soniyada bir marta.
Buyurtma berish (AI sarflaydigan) handler'lar: 4 soniyada bir marta.
"""
from __future__ import annotations
import time
from typing import Any, Awaitable, Callable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

_last: dict[int, float] = {}        # umumiy oxirgi bosish vaqti
_last_heavy: dict[int, float] = {}  # "og'ir" (AI) amal oxirgi vaqti

_GENERAL_GAP = 0.6
_HEAVY_GAP = 2.5
_HEAVY_TRIGGERS = ("📝 Buyurtma berish", "doctype:", "pay:balance:", "confirm:")


def _is_heavy(event: TelegramObject) -> bool:
    if isinstance(event, Message) and event.text:
        return event.text in _HEAVY_TRIGGERS
    if isinstance(event, CallbackQuery) and event.data:
        return any(event.data.startswith(t) for t in _HEAVY_TRIGGERS)
    return False


class ThrottleMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = getattr(event, "from_user", None)
        if user is None:
            return await handler(event, data)
        uid = user.id
        now = time.monotonic()

        if _is_heavy(event):
            if now - _last_heavy.get(uid, 0) < _HEAVY_GAP:
                if isinstance(event, CallbackQuery):
                    await event.answer("⚡ Juda tez bosdingiz — bir soniyadan so'ng qayta bosing",
                                       show_alert=False)
                return
            _last_heavy[uid] = now
        else:
            if now - _last.get(uid, 0) < _GENERAL_GAP:
                if isinstance(event, CallbackQuery):
                    await event.answer()
                return
        _last[uid] = now
        return await handler(event, data)
