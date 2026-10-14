import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.database import Base, close_redis, engine
from app.routers import channels, countries, health, map, play, search, stream_proxy

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("radioglobe")


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not settings.is_production:
        # Productionda sxema Alembic migratsiyalari bilan boshqariladi
        # (`alembic upgrade head`), create_all faqat lokal ishlab chiqish uchun.
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Development rejimi: jadvallar create_all bilan tayyorlandi")
    logger.info("RadioGlobe API ishga tushdi (muhit: %s)", settings.ENVIRONMENT)
    yield
    await close_redis()
    await engine.dispose()
    logger.info("RadioGlobe API to'xtadi")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
    # Productionda interaktiv hujjatlar yopiq
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
    openapi_url=None if settings.is_production else "/openapi.json",
)

# CORS — aniq manzillar ro'yxati. Cookie ishlatilmaydi, shuning uchun
# allow_credentials=False (bu "*" bilan ziddiyatni ham butunlay yo'q qiladi).
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
    max_age=600,
)

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), camera=(), microphone=(), payment=()",
}


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    for key, value in SECURITY_HEADERS.items():
        response.headers.setdefault(key, value)
    if settings.is_production:
        response.headers.setdefault(
            "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
        )
    return response


def _error(status_code: int, code: str, message: str) -> JSONResponse:
    """Hujjatda kelishilgan yagona xato formati."""
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message}},
    )


_CODE_BY_STATUS = {
    400: "bad_request",
    403: "forbidden",
    404: "not_found",
    422: "validation_error",
    429: "rate_limited",
    502: "stream_unavailable",
}


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    code = _CODE_BY_STATUS.get(exc.status_code, "error")
    return _error(exc.status_code, code, str(exc.detail))


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return _error(422, "validation_error", "So'rov parametrlari noto'g'ri")


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Ichki xato tafsilotlari logga yoziladi, foydalanuvchiga chiqmaydi
    logger.exception("Kutilmagan xato: %s %s", request.method, request.url.path)
    return _error(500, "internal_error", "Ichki xatolik yuz berdi")


for router in (health, map, countries, channels, play, stream_proxy, search):
    app.include_router(router.router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "api_v1": settings.API_V1_STR,
    }
