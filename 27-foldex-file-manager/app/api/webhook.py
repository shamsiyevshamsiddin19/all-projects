# -*- coding: utf-8 -*-
"""
Foldex Telegram Webhook API yo'li.
FastAPI orqali Telegram serverlaridan kelayotgan barcha yangilanishlarni (updates)
qabul qiladi va aiogram Dispatcher ga uzatadi.
"""

from fastapi import APIRouter, Header, HTTPException, Request, status
from aiogram.types import Update

from app.bot.loader import bot, dp
from app.core.config import settings

router = APIRouter(prefix="/api/webhook", tags=["Telegram Webhook"])


@router.post("/telegram")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str = Header(None)
):
    """
    Telegram Bot API dan kelgan webhook so'rovlarini qabul qiladi.
    Xavfsizlik: X-Telegram-Bot-Api-Secret-Token orqali soxta so'rovlardan himoyalangan.
    """
    if settings.WEBHOOK_SECRET and x_telegram_bot_api_secret_token != settings.WEBHOOK_SECRET:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Noto'g'ri webhook maxfiy kaliti!"
        )

    try:
        data = await request.json()
        update = Update.model_validate(data, context={"bot": bot})
        await dp.feed_webhook_update(bot=bot, update=update)
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}
