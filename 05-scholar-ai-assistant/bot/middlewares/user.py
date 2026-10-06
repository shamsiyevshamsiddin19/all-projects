from __future__ import annotations
from typing import Any, Awaitable, Callable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from db.crud import get_or_create_user


class UserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = None
        if isinstance(event, Message) and event.from_user:
            user = event.from_user
        elif isinstance(event, CallbackQuery) and event.from_user:
            user = event.from_user

        if user:
            db_user = await get_or_create_user(
                user_id=user.id,
                username=user.username,
                full_name=user.full_name,
            )
            data["db_user"] = db_user
            if db_user.is_banned:
                return  # ban → hech narsa qilmaymiz

        return await handler(event, data)
