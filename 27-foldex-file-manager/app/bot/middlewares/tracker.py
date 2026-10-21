# -*- coding: utf-8 -*-
"""
Foldex Xabarlarni Kuzatish Middleware-lari (Incoming va Outgoing Tracker).
- Chatdagi barcha xabarlarning ID sini ma'lumotlar bazasiga yozadi.
- Foydalanuvchi har 5-marta buyruq/tugma bosganida oldingi barcha xabarlarni
  avtomatik tozalaydi (/start xabari saqlanadi).
"""

from typing import Any, Callable, Dict, Awaitable
from aiogram import BaseMiddleware, Bot
from aiogram.client.session.middlewares.base import BaseRequestMiddleware
from aiogram.methods import TelegramMethod
from aiogram.methods.base import Response
from aiogram.types import Message, TelegramObject

from app.services.cleanup_service import CleanupService

# Har bir chat uchun bosilgan buyruqlar hisoblagichi
_chat_click_counts: Dict[int, int] = {}


class IncomingMessageTrackerMiddleware(BaseMiddleware):
    """
    Foydalanuvchi tomonidan yuborilgan barcha xabarlarni qayd qiladi.
    Har 5-chi buyruq kelganda, oldingi to'plangan xabarlarni avtomatik o'chiradi.
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

            if is_start:
                _chat_click_counts[event.chat.id] = 0
            else:
                # Har 5-chi buyruq bosilganda oldingi xabarlarni o'chirish
                current_count = _chat_click_counts.get(event.chat.id, 0) + 1
                if current_count >= 5:
                    print(f"🧹 5-chi buyruq bosildi (chat {event.chat.id}): oldingi xabarlar tozalanmoqda...")
                    await CleanupService.cleanup_previous_messages(
                        bot=event.bot,
                        chat_id=event.chat.id,
                        exclude_message_ids=[event.message_id]
                    )
                    _chat_click_counts[event.chat.id] = 0
                else:
                    _chat_click_counts[event.chat.id] = current_count

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
