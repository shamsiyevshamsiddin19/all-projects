"""FastAPI ilova: Telegram webhook + web mini-app API + health.

Ishga tushirish:  uvicorn app.main:app --port 8090
Webhook:  POST /boost/webhook   (Telegram shu yerga update yuboradi)
Web API:  GET/POST /boost/api?action=...
"""

from __future__ import annotations

import hmac
import json
import logging

from fastapi import FastAPI, File, Form, Request, Response, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, PlainTextResponse

from . import db
from .config import APP_ROOT, settings
from .handlers import handle_update
from .media import MAX_UPLOAD_BYTES, upload_to_telegram
from .miniauth import resolve_owner
from .webapp import JsonResult, handle_action

APP_ROOT.joinpath("logs").mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler(settings.LOG_FILE, encoding="utf-8")],
)
logger = logging.getLogger("boostday")

app = FastAPI(title="Boostday Bot", docs_url=None, redoc_url=None, openapi_url=None)


@app.on_event("startup")
def _startup() -> None:
    try:
        db.migrate()
    except Exception:  # noqa: BLE001
        logger.exception("Bot schema init xatosi (baza ulanmagan bo'lishi mumkin)")
    try:
        from .tg import set_chat_menu_button

        set_chat_menu_button()
    except Exception:  # noqa: BLE001
        logger.exception("Chat menu tugmasini o'rnatishda xato")


def _json(payload: dict) -> JSONResponse:
    return JSONResponse(content=json.loads(json.dumps(payload, ensure_ascii=False)),
                        media_type="application/json; charset=utf-8")


# --- Telegram webhook ---
@app.get("/boost/webhook")
async def webhook_info():
    return PlainTextResponse("Boostday webhook endpoint is ready. Use Telegram setWebhook with POST updates.")


@app.post("/boost/webhook")
async def webhook(request: Request):
    secret = settings.WEBHOOK_SECRET
    if secret:
        header = request.headers.get("x-telegram-bot-api-secret-token", "")
        if not hmac.compare_digest(secret, header):
            logger.warning("INVALID_SECRET from %s", request.client.host if request.client else "?")
            return PlainTextResponse("Forbidden", status_code=403)

    raw = await request.body()
    try:
        update = json.loads(raw)
    except (ValueError, TypeError):
        update = None
    if not update:
        return PlainTextResponse("OK")

    try:
        handle_update(update)
    except Exception:  # noqa: BLE001
        logger.exception("WEBHOOK_FATAL")
        return PlainTextResponse("Webhook error", status_code=500)

    return PlainTextResponse("OK")


# --- Web mini-app API ---
@app.api_route("/boost/api", methods=["GET", "POST"])
async def boost_api(request: Request):
    params: dict = {}
    params.update(dict(request.query_params))
    if request.method == "POST":
        try:
            form = await request.form()
            params.update({k: v for k, v in form.items()})
        except Exception:
            pass

    action = str(params.get("action", "") or "").strip()

    if action == "health":
        return _json(_boost_health())

    # --- Owner aniqlash: mini app (initData) yoki sayt (admin) ---
    # Client yuborgan owner_id'ga ISHONMAYMIZ — serverda aniqlaymiz.
    init_data = str(params.get("init_data", "") or "")
    # Sayt tomoni maxfiy kalitni sarlavhada yuboradi (URL'da emas — log'ga tushmasin)
    site_secret = request.headers.get("X-Site-Secret", "") or str(params.get("site_secret", "") or "")
    auth = resolve_owner(init_data, site_secret)
    if not auth["ok"]:
        return _json({"ok": False, "message": auth["error"]})
    params["owner_id"] = str(auth["owner_id"])
    params.pop("site_secret", None)

    try:
        return _json(handle_action(action, params))
    except JsonResult as jr:
        return _json(jr.payload)
    except Exception:  # noqa: BLE001
        logger.exception("BOOST_API_FATAL")
        return _json({"ok": False, "message": "Server xatoligi. Iltimos, keyinroq urinib ko'ring."})


# --- Mini App: galereyadan tanlangan faylni yuklab file_id olish ---
@app.post("/boost/upload")
async def boost_upload(
    init_data: str = Form(""),
    kind: str = Form("document"),
    file: UploadFile = File(...),
):
    auth = resolve_owner(init_data)
    if not auth["ok"] or not auth.get("chat_id"):
        return _json({"ok": False, "message": auth.get("error") or "Avtorizatsiya kerak"})

    content = await file.read()
    if not content:
        return _json({"ok": False, "message": "Fayl bo'sh"})
    if len(content) > MAX_UPLOAD_BYTES:
        return _json({"ok": False, "message": f"Fayl juda katta (max {MAX_UPLOAD_BYTES // (1024 * 1024)}MB)"})

    safe_kind = kind if kind in ("photo", "video", "audio", "document") else "document"
    try:
        result = upload_to_telegram(auth["chat_id"], safe_kind, file.filename or "file", content,
                                    file.content_type or "")
    except Exception:  # noqa: BLE001
        logger.exception("BOOST_UPLOAD_FATAL")
        return _json({"ok": False, "message": "Yuklashda kutilmagan xato"})

    if not result.get("ok"):
        return _json({"ok": False, "message": result.get("error", "Yuklashda xato")})
    return _json({"ok": True, "message": "Yuklandi", "file_id": result["file_id"], "type": result["type"]})


# --- Mini App sahifasi (Telegram WebApp) ---
@app.get("/boost/app")
async def boost_app() -> Response:
    path = APP_ROOT / "miniapp.html"
    if path.is_file():
        return FileResponse(str(path), media_type="text/html; charset=utf-8")
    return HTMLResponse("<h1>Mini app hali o'rnatilmagan</h1>", status_code=404)


def _boost_health() -> dict:
    import sys

    payload = {
        "ok": True, "service": "boostday",
        "runtime": {"python": sys.version.split()[0], "framework": "fastapi"},
        "db": {"connected": False, "error": None}, "tables": {},
    }
    try:
        db.value("SELECT 1")
        payload["db"]["connected"] = True
        for t in ["users", "user_channels", "plans", "history", "settings", "sent_logs"]:
            # t oldindan qat'iy ro'yxatdan (injection'siz); PostgreSQL uchun qo'shtirnoq.
            payload["tables"][t] = db.value(f'SELECT COUNT(*) FROM "{t}"') if db.table_exists(t) else None
    except Exception as e:  # noqa: BLE001
        payload["ok"] = False
        payload["db"]["error"] = str(e)
        logger.exception("Boost health xatosi")
    return payload


@app.get("/healthz")
async def healthz():
    return {"ok": True}
