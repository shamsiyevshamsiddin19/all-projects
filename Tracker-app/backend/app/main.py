import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.analytics import router as analytics_router
from app.api.v1.assignments import router as assignments_router
from app.api.v1.auth import router as auth_router
from app.api.v1.files import router as files_router
from app.api.v1.groups import router as groups_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.submissions import router as submissions_router
from app.api.v1.users import router as users_router
from app.core.config import settings
from app.core.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup
    await init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="Teacher-Student Task Management App Master API with Role-Based Access Control, Submissions, Grading, Analytics and Export.",
    version="1.0.0",
    lifespan=lifespan,
)

# Setup CORS middleware.
# allow_credentials=False — bu app kirish/kuki emas, JWT Bearer token bilan
# ishlaydi, shuning uchun cookie-asosli credentials shart emas. "*" (barcha
# manba) bilan allow_credentials=True birga ishlatilishi brauzerlar
# tomonidan CORS spetsifikatsiyasiga zid hisoblanadi va kelajakda
# kuki-asosli funksiya qo'shilsa xavfsizlik teshigiga aylanishi mumkin edi.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else ["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount uploads static folder
if os.path.exists(settings.UPLOAD_DIR):
    app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Include API v1 Routers
api_v1_str = settings.API_V1_STR
app.include_router(auth_router, prefix=api_v1_str)
app.include_router(users_router, prefix=api_v1_str)
app.include_router(groups_router, prefix=api_v1_str)
app.include_router(assignments_router, prefix=api_v1_str)
app.include_router(submissions_router, prefix=api_v1_str)
app.include_router(analytics_router, prefix=api_v1_str)
app.include_router(notifications_router, prefix=api_v1_str)
app.include_router(files_router, prefix=api_v1_str)


@app.get("/health", tags=["Health"])
async def health_check():
    """System health check endpoint."""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "version": "1.0.0",
    }


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Welcome to Teacher-Student Task Management API",
        "docs": "/docs",
        "health": "/health",
        "api_v1": settings.API_V1_STR,
    }
