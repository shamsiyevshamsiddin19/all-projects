import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update

logger = logging.getLogger("bot")


class LoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if isinstance(event, Update):
            if event.message:
                logger.info("message from=%s text=%r", event.message.from_user.id, event.message.text)
            elif event.callback_query:
                logger.info(
                    "callback from=%s data=%r", event.callback_query.from_user.id, event.callback_query.data
                )
        return await handler(event, data)
