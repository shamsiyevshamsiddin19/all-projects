# -*- coding: utf-8 -*-
"""
Foldex Chat Tozalash Xizmati (Cleanup Service).
Foydalanuvchi talabiga ko'ra har kechqurun chatdagi barcha xabarlarni
avtomatik o'chiradi, faqat yuborilgan /start xabari qoldiriladi.
Shuningdek, /clear buyrug'i orqali ham ixtiyoriy vaqtda xabarlarni
tozalash imkoniyatini taqdim etadi.
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import List
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from sqlalchemy import select, delete

from app.core.config import settings
from app.core.database import async_session_maker
from app.models.chat_message import BotChatMessage


class CleanupService:
    """Chat xabarlarini qayd qilish va kechqurun tozalash xizmati."""

    @staticmethod
    async def record_message(chat_id: int, message_id: int, is_start: bool = False) -> None:
        """
        Chatda yuborilgan yoki qabul qilingan xabar ID sini bazaga yozib qo'yish.
        """
        try:
            async with async_session_maker() as db:
                # Mavjudligini tekshirish
                stmt = select(BotChatMessage.id).where(
                    BotChatMessage.chat_id == chat_id,
                    BotChatMessage.message_id == message_id
                )
                res = await db.execute(stmt)
                if res.scalar_one_or_none() is None:
                    record = BotChatMessage(
                        chat_id=chat_id,
                        message_id=message_id,
                        is_start=is_start
                    )
                    db.add(record)
                    await db.commit()
        except Exception as e:
            # Xabarlarni yozishdagi xatolik asosiy bot oqimiga to'sqinlik qilmasligi kerak
            print(f"⚠️ Xabar ID sini qayd qilishda xatolik: {e}")

    @staticmethod
    async def cleanup_chat_messages(bot: Bot, target_chat_id: int | None = None) -> int:
        """
        Kechqurun chatdagi barcha xabarlarni o'chiradi.
        Faqat /start xabarlari (is_start=True) saqlanib qoladi.
        """
        chat_id = target_chat_id or settings.TELEGRAM_ADMIN_ID
        print(f"🧹 Chat ({chat_id}) tozalash boshlanmoqda...")

        async with async_session_maker() as db:
            # is_start=False bo'lgan xabarlarni olish
            stmt = select(BotChatMessage).where(
                BotChatMessage.chat_id == chat_id,
                BotChatMessage.is_start == False
            ).order_by(BotChatMessage.message_id.desc())

            res = await db.execute(stmt)
            messages_to_delete: List[BotChatMessage] = list(res.scalars().all())

            if not messages_to_delete:
                print("ℹ️ Tozalash uchun xabarlar mavjud emas.")
                return 0

            deleted_ids = []
            msg_ids = [m.message_id for m in messages_to_delete]

            # Telegram API da xabarlarni 100 tadan to'p qilib o'chirish
            batch_size = 100
            for i in range(0, len(msg_ids), batch_size):
                batch = msg_ids[i:i + batch_size]
                try:
                    await bot.delete_messages(chat_id=chat_id, message_ids=batch)
                    deleted_ids.extend(batch)
                except TelegramAPIError as batch_err:
                    # Agar to'p bo'lib o'chirishda xatolik yuz bersa, bittalab o'chirib ko'ramiz
                    for single_id in batch:
                        try:
                            await bot.delete_message(chat_id=chat_id, message_id=single_id)
                            deleted_ids.append(single_id)
                        except TelegramAPIError:
                            # 48 soatdan o'tgan yoki allaqachon o'chirilgan bo'lsa, bazadan baribir o'chiramiz
                            deleted_ids.append(single_id)
                await asyncio.sleep(0.1)

            # O'chirilgan xabarlarni bazadan tozalash
            if deleted_ids:
                del_stmt = delete(BotChatMessage).where(
                    BotChatMessage.chat_id == chat_id,
                    BotChatMessage.message_id.in_(deleted_ids)
                )
                await db.execute(del_stmt)
                await db.commit()

            print(f"✅ Chat tozalash yakunlandi: {len(deleted_ids)} ta xabar o'chirildi.")
            return len(deleted_ids)

    @staticmethod
    async def cleanup_previous_messages(
        bot: Bot,
        chat_id: int,
        exclude_message_ids: List[int] | None = None
    ) -> int:
        """
        Foydalanuvchi har 5-marta buyruq bosganda oldingi to'plangan
        barcha xabarlarni o'chiradi.
        - is_start=True bo'lgan (/start) xabarlar saqlanadi.
        - exclude_message_ids da berilgan (masalan, joriy eng oxirgi xabar) saqlanadi.
        """
        exclude_ids = set(exclude_message_ids or [])
        async with async_session_maker() as db:
            stmt = select(BotChatMessage).where(
                BotChatMessage.chat_id == chat_id,
                BotChatMessage.is_start == False
            ).order_by(BotChatMessage.message_id.desc())

            res = await db.execute(stmt)
            messages = list(res.scalars().all())

            # exclude_ids ga kirmaydigan xabarlarni ajratib olish
            to_delete = [m for m in messages if m.message_id not in exclude_ids]
            if not to_delete:
                return 0

            msg_ids = [m.message_id for m in to_delete]
            deleted_ids = []

            # Telegram API orqali to'p qilib o'chirish
            batch_size = 100
            for i in range(0, len(msg_ids), batch_size):
                batch = msg_ids[i:i + batch_size]
                try:
                    await bot.delete_messages(chat_id=chat_id, message_ids=batch)
                    deleted_ids.extend(batch)
                except TelegramAPIError:
                    for single_id in batch:
                        try:
                            await bot.delete_message(chat_id=chat_id, message_id=single_id)
                            deleted_ids.append(single_id)
                        except TelegramAPIError:
                            deleted_ids.append(single_id)
                await asyncio.sleep(0.05)

            if deleted_ids:
                del_stmt = delete(BotChatMessage).where(
                    BotChatMessage.chat_id == chat_id,
                    BotChatMessage.message_id.in_(deleted_ids)
                )
                await db.execute(del_stmt)
                await db.commit()

            print(f"🧹 Har 5-buyruq tozalashi: {len(deleted_ids)} ta oldingi xabar o'chirildi.")
            return len(deleted_ids)


async def nightly_cleanup_loop(bot: Bot) -> None:
    """
    Har kuni kechqurun soat 23:59 (Asia/Tashkent - UTC+5) da
    chatdagi xabarlarni avtomatik tozalovchi fon vazifasi.
    """
    print("🌙 Kechki avtomatik tozalash xizmati ishga tushirildi (Asia/Tashkent: 23:59).")
    last_cleaned_date = None

    tashkent_tz = timezone(timedelta(hours=5))

    while True:
        try:
            now_tashkent = datetime.now(tashkent_tz)
            today_str = now_tashkent.strftime("%Y-%m-%d")

            # Har kuni kechqurun 23:59 da yoki 00:00 da
            if now_tashkent.hour == 23 and now_tashkent.minute >= 58:
                if last_cleaned_date != today_str:
                    print(f"⏰ Kechqurun soat {now_tashkent.strftime('%H:%M')} — Avtomatik tozalash ishga tushmoqda...")
                    await CleanupService.cleanup_chat_messages(bot)
                    last_cleaned_date = today_str

            await asyncio.sleep(30)
        except asyncio.CancelledError:
            print("🛑 Kechki tozalash fon vazifasi to'xtatildi.")
            break
        except Exception as e:
            print(f"⚠️ Kechki tozalash davomida ogohlantirish: {e}")
            await asyncio.sleep(60)
