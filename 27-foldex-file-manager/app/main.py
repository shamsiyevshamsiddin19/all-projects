# -*- coding: utf-8 -*-
"""
Foldex Asosiy FastAPI Ilovasi (main.py).
FastAPI veb-serveri va aiogram 3.x Telegram botini bitta
yagona arxitekturaga birlashtiruvchi markaziy kirish nuqtasi.
Lifespan orqali ma'lumotlar bazasi va Telegram webhookini boshqaradi.
"""

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select

from app.api import auth, files, folders, stats, webhook
from app.api.deps import get_admin_optional
from app.bot.handlers import file_upload, inline, navigation, start
from app.bot.loader import bot, dp
from app.bot.middlewares.auth import AdminAuthMiddleware
from app.core.config import settings, BASE_DIR
from app.core.database import async_session_maker, engine, Base
from app.core.security import create_access_token
from app.models.auth_token import AdminAuthToken
import app.models  # Barcha modellar Base.metadata ga to'liq ulanishi uchun

# 1. Shablonlar (Jinja2 Templates) va Statik fayllar yo'llari
TEMPLATES_DIR = BASE_DIR / "app" / "templates"
STATIC_DIR = BASE_DIR / "app" / "static"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# 2. Ilovaning hayot siklini (Lifespan) boshqarish
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Ilova ishga tushganda (startup):
    - DB jadvallarini yaratadi;
    - Standart papkalarni (baza bo'sh bo'lsa) kiritadi;
    - aiogram bot routerlari va middlewarelarini ro'yxatdan o'tkazadi;
    - Webhook yoki polling rejimini sozlaydi.

    Ilova to'xtaganda (shutdown):
    - Bot va DB ulanishlarini toza yopadi.
    """
    # --- STARTUP ---
    print("🚀 Foldex ilovasi ishga tushmoqda...")

    # a) Ma'lumotlar bazasi jadvallarini yaratish (Alembic bo'lmagan holatda ham avtomatik yaratiladi)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # c) Telegram Bot Middleware va Handlerlarini ro'yxatdan o'tkazish
    # Qat'iy bitta foydalanuvchi tekshiruvi (TELEGRAM_ADMIN_ID: 7883409434)
    auth_middleware = AdminAuthMiddleware()
    dp.message.middleware(auth_middleware)
    dp.callback_query.middleware(auth_middleware)
    dp.inline_query.middleware(auth_middleware)

    # Kiruvchi va chiquvchi xabarlarni kuzatish (kechki avtomatik tozalash uchun)
    from app.bot.middlewares.tracker import (
        IncomingMessageTrackerMiddleware,
        OutgoingMessageTrackerMiddleware,
    )
    from app.services.cleanup_service import nightly_cleanup_loop

    dp.message.outer_middleware(IncomingMessageTrackerMiddleware())
    bot.session.middleware(OutgoingMessageTrackerMiddleware())

    # Handler routerlarini ulash
    dp.include_router(start.router)
    dp.include_router(navigation.router)
    dp.include_router(inline.router)
    dp.include_router(file_upload.router)

    # d) Telegram Bot Webhook, Komandalar menyusi va Foniy vazifalar
    polling_task = None
    cleanup_task = None

    if settings.BOT_TOKEN:
        try:
            from aiogram.types import BotCommand, BotCommandScopeDefault
            await bot.set_my_commands(
                commands=[
                    BotCommand(command="start", description="📂 Bosh sahifa"),
                    BotCommand(command="home", description="🏠 Bosh sahifaga qaytish"),
                    BotCommand(command="search", description="🔍 Fayllarni qidirish"),
                    BotCommand(command="clear", description="🧹 Chatni tozalash"),
                    BotCommand(command="admin", description="🌐 Veb-Admin Panel"),
                    BotCommand(command="login", description="🔑 Bir martalik kirish havolasi"),
                    BotCommand(command="help", description="💡 Yordam va qo'llanma"),
                ],
                scope=BotCommandScopeDefault(),
            )
            print("✅ Telegram bot buyruqlari muvaffaqiyatli ro'yxatdan o'tkazildi.")

            # Har kuni kechqurun xabarlarni avtomatik tozalovchi fon vazifasini ishga tushirish
            cleanup_task = asyncio.create_task(nightly_cleanup_loop(bot))

            if settings.USE_WEBHOOK and settings.DOMAIN:
                webhook_url = f"{settings.DOMAIN}/api/webhook/telegram"
                print(f"📡 Webhook o'rnatilmoqda: {webhook_url}")
                await bot.set_webhook(
                    url=webhook_url,
                    secret_token=settings.WEBHOOK_SECRET,
                    drop_pending_updates=True
                )
            else:
                # Mahalliy test rejimida foniy polling
                print("🔄 Polling rejimi yoqilmoqda...")
                await bot.delete_webhook(drop_pending_updates=True)
                polling_task = asyncio.create_task(dp.start_polling(bot))
        except Exception as e:
            print(f"⚠️ Telegram botni ulashda ogohlantirish: {e}")

    yield

    # --- SHUTDOWN ---
    print("🛑 Foldex ilovasi to'xtatilmoqda...")
    if cleanup_task:
        cleanup_task.cancel()
    if polling_task:
        polling_task.cancel()
    if settings.BOT_TOKEN:
        try:
            await bot.session.close()
        except Exception:
            pass
    await engine.dispose()
    print("✅ Barcha resurslar xavfsiz yopildi.")


# 3. FastAPI ilova nusxasini yaratish
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Telegram File Manager Bot va Veb-Admin Paneli",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None
)

# 4. CORS xavfsizlik sozlamalari
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.DOMAIN, "http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 5. Statik fayllarni ulash (/static)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# 6. API Routerlarini ro'yxatdan o'tkazish
app.include_router(auth.router)
app.include_router(folders.router)
app.include_router(files.router)
app.include_router(stats.router)
app.include_router(webhook.router)


# 7. HTML Sahifalar (Frontend Marshrutlari)
@app.get("/", response_class=HTMLResponse)
async def serve_index(
    request: Request,
    admin_id: Optional[int] = Depends(get_admin_optional)
):
    """
    Boshqaruv panelining bosh sahifasi.
    Agar administrator tizimga kirmagan bo'lsa va Telegram WebApp bo'lmasa,
    /login sahifasiga yo'naltiradi.
    """
    # Telegram Mini App ichida ochilganda window.Telegram.WebApp.initData orqali
    # kirishga imkon berish uchun index.html yuklanishi lozim (auth.js tekshiradi)
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/login", response_class=HTMLResponse)
async def serve_login(request: Request):
    """Autentifikatsiya sahifasi."""
    return templates.TemplateResponse(request=request, name="login.html")


@app.get("/auth/verify")
async def verify_magic_link(
    token: str = Query(..., description="Bir martalik kirish tokeni"),
    response: Response = None
):
    """
    Botdagi /login komandasi yuborgan bir martalik xavfsiz havolani qayta ishlash.
    Havola bosilganda HTTPOnly JWT cookie o'rnatib, bosh sahifaga yo'naltiradi.
    """
    async with async_session_maker() as db:
        stmt = select(AdminAuthToken).where(
            AdminAuthToken.token == token,
            AdminAuthToken.is_used == False
        )
        res = await db.execute(stmt)
        token_obj = res.scalar_one_or_none()

        if not token_obj:
            return RedirectResponse(url="/login?error=invalid_token", status_code=status.HTTP_302_FOUND)

        # Tokenni ishlatilgan deb belgilash
        token_obj.is_used = True
        await db.commit()

        # JWT token generatsiya qilish
        jwt_token = create_access_token(data={"sub": str(token_obj.telegram_user_id), "role": "admin"})

        redirect_resp = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
        redirect_resp.set_cookie(
            key="foldex_token",
            value=jwt_token,
            httponly=True,
            secure=settings.DOMAIN.startswith("https"),
            samesite="lax",
            max_age=settings.JWT_ACCESS_TOKEN_EXPIRE_DAYS * 86400
        )
        return redirect_resp


@app.get("/health")
async def health_check():
    """Tizim salomatligini tekshirish (Healthcheck) endpointi."""
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "admin_id": settings.TELEGRAM_ADMIN_ID
    }
