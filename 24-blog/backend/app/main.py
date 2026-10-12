from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .database import engine, Base
from .routers import auth, categories, posts, comments, users

# Ma'lumotlar bazasi jadvallarini yaratish (agar hali mavjud bo'lmasa)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Blog API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS sozlamalari (Frontend ulanishi uchun)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routerlarni ulash
app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(posts.router)
app.include_router(comments.router)
app.include_router(users.router)

# Asosiy salomlashish va holat tekshiruvi endpointi
@app.get("/", tags=["Root"])
def root():
    return {
        "status": "online",
        "service": "Blog Backend API",
        "version": "1.0.0",
        "database": "PostgreSQL",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }

@app.get("/api/health", tags=["Root"])
def health_check():
    return {
        "status": "healthy",
        "database": "connected"
    }

# Frontend statik fayllarini ulash (agar mavjud bo'lsa)
FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent
if (FRONTEND_DIR / "index.html").exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")
