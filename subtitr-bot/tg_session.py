"""Telegram sessiya/bot yaratish uchun yagona joy — local server qo'llab-quvvatlashi bilan.

LOCAL_BOT_API o'rnatilgan bo'lsa (o'z serverimizdagi telegram-bot-api, --local
rejim), bot ham worker ham o'sha serverga ulanadi — katta fayllar (2GB gacha)
yuklab olish va yuborish uchun. Bo'lmasa oddiy bulut api.telegram.org.
"""
from __future__ import annotations

from aiogram import Bot
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer

from config import settings


def make_session(timeout: int | None = None) -> AiohttpSession:
    """AiohttpSession yaratadi — local API sozlangan bo'lsa o'shanga yo'naltiradi."""
    t = timeout if timeout is not None else settings.bot_request_timeout
    if settings.local_bot_api:
        api = TelegramAPIServer.from_base(settings.local_bot_api, is_local=True)
        return AiohttpSession(api=api, timeout=t)
    return AiohttpSession(timeout=t)


def make_bot(timeout: int | None = None) -> Bot:
    """settings.bot_token bilan Bot yaratadi (local API sozlangan bo'lsa o'shanda)."""
    return Bot(token=settings.bot_token, session=make_session(timeout))


def local_to_host_path(path: str) -> str:
    """Local server (--local) get_file qaytargan KONTEYNER yo'lini host yo'liga o'giradi.

    Masalan: /var/lib/telegram-bot-api/<token>/videos/file_5.mp4
          -> /root/bot_deploy/telegram-bot-api-data/<token>/videos/file_5.mp4
    LOCAL_API_HOST_DIR bo'sh bo'lsa yoki yo'l mos kelmasa — o'zgarishsiz qaytaradi.
    """
    cdir = settings.local_api_container_dir
    hdir = settings.local_api_host_dir
    if hdir and cdir and path.startswith(cdir):
        return hdir + path[len(cdir):]
    return path
