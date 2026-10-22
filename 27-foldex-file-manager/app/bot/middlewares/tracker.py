# -*- coding: utf-8 -*-
"""
Foldex Xabarlarni Kuzatish Middleware-lari (Incoming va Outgoing Tracker).
- Chatdagi barcha xabarlarning ID sini ma'lumotlar bazasiga yozadi
  (tungi avtomatik tozalash va /clear buyrug'i uchun).
"""

from typing import Any, Callable, Dict, Awaitable
from aiogram import BaseMiddleware, Bot
from aiogram.client.session.middlewares.base import BaseRequestMiddleware
from aiogram.methods import TelegramMethod
from aiogram.methods.base import Response
from aiogram.types import Message, TelegramObject

from app.services.cleanup_service import CleanupService


class IncomingMessageTrackerMiddleware(BaseMiddleware):
    """
    Foydalanuvchi tomonidan yuborilgan barcha xabarlarni DB ga qayd qiladi.
    """
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        if isinstance(event, Message):
            is_start = bool(event.text and event.text.strip().startswith("/start"))
            await CleanupService.record_message(
                chat_id=event.chat.id,
                message_id=event.message_id,
                is_start=is_start
            )

        return await handler(event, data)


class OutgoingMessageTrackerMiddleware(BaseRequestMiddleware):
    """
    Bot tomonidan yuborilgan barcha xabarlar (matn, fayl, foto va h.k.) ni
    qayd qiladi. Bular tozalashda o'chirilishi uchun is_start=False bo'ladi.
    """
    async def __call__(
        self,
        make_request: Callable[[Bot, TelegramMethod[Any]], Awaitable[Response[Any]]],
        bot: Bot,
        method: TelegramMethod[Any]
    ) -> Response[Any]:
        response = await make_request(bot, method)

        try:
            # Agar qaytgan natija Message obyekti bo'lsa
            if isinstance(response, Message):
                await CleanupService.record_message(
                    chat_id=response.chat.id,
                    message_id=response.message_id,
                    is_start=False
                )
            # Agar natija xabarlar ro'yxati bo'lsa (masalan MediaGroup)
            elif isinstance(response, list):
                for item in response:
                    if isinstance(item, Message):
                        await CleanupService.record_message(
                            chat_id=item.chat.id,
                            message_id=item.message_id,
                            is_start=False
                        )
        except Exception as e:
            print(f"⚠️ Chiquvchi xabarni kuzatishda ogohlantirish: {e}")

        return response
