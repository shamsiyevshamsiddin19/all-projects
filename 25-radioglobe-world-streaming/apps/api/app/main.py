from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import settings
from app.database import engine, Base
from app.routers import health, map, countries, channels, play, stream_proxy, search

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure database tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown resources
    await engine.dispose()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production customize via settings.ALLOWED_ORIGINS
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers under /api/v1
app.include_router(health.router, prefix=settings.API_V1_STR)
app.include_router(map.router, prefix=settings.API_V1_STR)
app.include_router(countries.router, prefix=settings.API_V1_STR)
app.include_router(channels.router, prefix=settings.API_V1_STR)
app.include_router(play.router, prefix=settings.API_V1_STR)
app.include_router(stream_proxy.router, prefix=settings.API_V1_STR)
app.include_router(search.router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "api_v1": settings.API_V1_STR
    }
