from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.core.config import get_settings
from app.routers.api import router as api_router
from app.services.catalog_service import get_catalog

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Ilova ishga tushishida katalogni tekshiradi va tezkor xotiraga oladi."""

    get_catalog()
    yield


settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    description="Turli yo'nalishlardagi qisqa, takrorlanuvchi mashqlar platformasi.",
    version="1.0.0",
    docs_url="/api/docs" if settings.app_env != "production" else None,
    redoc_url=None,
    lifespan=lifespan,
)
app.add_middleware(GZipMiddleware, minimum_size=700)
app.include_router(api_router)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def home(request: Request) -> HTMLResponse:
    """Mashqlar katalogining bosh sahifasini qaytaradi."""

    return templates.TemplateResponse(request=request, name="index.html", context={"host": settings.app_host})


@app.get("/mashq/{exercise_id}", response_class=HTMLResponse, include_in_schema=False)
async def exercise_page(request: Request, exercise_id: str) -> HTMLResponse:
    """Mashq uchun alohida, to'g'ridan-to'g'ri ochiladigan sahifani qaytaradi."""

    exercise = get_catalog().exercise(exercise_id).public()
    return templates.TemplateResponse(
        request=request,
        name="exercise.html",
        context={"host": settings.app_host, "exercise": exercise},
    )
