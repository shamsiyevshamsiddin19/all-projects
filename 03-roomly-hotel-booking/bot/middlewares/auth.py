from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update


class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        from apps.accounts.models import TelegramUser

        tg_user = None
        if isinstance(event, Update):
            if event.message:
                tg_user = event.message.from_user
            elif event.callback_query:
                tg_user = event.callback_query.from_user

        if tg_user is None:
            return await handler(event, data)

        user, _ = await TelegramUser.objects.aget_or_create(
            telegram_id=tg_user.id,
            defaults={
                "username": tg_user.username,
                "first_name": tg_user.first_name or "",
                "last_name": tg_user.last_name or "",
            },
        )
        data["user"] = user
        return await handler(event, data)
