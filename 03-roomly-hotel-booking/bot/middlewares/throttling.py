import time
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update

DEFAULT_RATE_LIMIT_SECONDS = 0.7


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, rate_limit: float = DEFAULT_RATE_LIMIT_SECONDS):
        self.rate_limit = rate_limit
        self._last_seen: dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user_id = None
        if isinstance(event, Update):
            if event.message:
                user_id = event.message.from_user.id
            elif event.callback_query:
                user_id = event.callback_query.from_user.id

        if user_id is not None:
            now = time.monotonic()
            last = self._last_seen.get(user_id, 0)
            if now - last < self.rate_limit:
                return None
            self._last_seen[user_id] = now

        return await handler(event, data)
