"""Yordamchi FastAPI backend — barcha action'lar `/api?action=...` orqali dispatch qilinadi."""

from __future__ import annotations

import json
import logging
from logging.handlers import RotatingFileHandler

from fastapi import FastAPI, Request
from starlette.middleware.sessions import SessionMiddleware

from .config import settings
from .errors import ApiError, register_exception_handlers
from .handlers import activity, auth, boost, dictionary, goals, language_topics, lms, misc, quiz, reja, sport, storage
from . import db, security

# --- Log sozlash (aylanuvchi fayl — cheksiz o'smaydi) ---
settings.LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        RotatingFileHandler(
            settings.LOG_DIR / "app.log",
            maxBytes=5 * 1024 * 1024,  # 5 MB
            backupCount=3,
            encoding="utf-8",
        ),
    ],
)
logger = logging.getLogger("yordamchi")

app = FastAPI(title="Yordamchi API", docs_url=None, redoc_url=None, openapi_url=None)

# Sessiya (imzolangan cookie — server tomonda saqlash shart emas).
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET,
    session_cookie=settings.SESSION_COOKIE,
    https_only=settings.SESSION_HTTPS_ONLY,
    same_site="lax",
    max_age=settings.SESSION_MAX_AGE,
)

if settings.CORS_ORIGINS:
    from fastapi.middleware.cors import CORSMiddleware

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

register_exception_handlers(app)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    return response


@app.on_event("startup")
def _startup() -> None:
    try:
        db.init_schema()
    except Exception:  # noqa: BLE001
        logger.exception("Schema init xatosi (baza ulanmagan bo'lishi mumkin)")


# Kirmasdan turib ham chaqirilishi mumkin bo'lgan yagona action'lar.
# Qolgan HAMMASI (o'qish ham) tizimga kirishni talab qiladi — ma'lumot shaxsiy:
# maqsadlar, lug'at, mavzular, sport va `storage_bootstrap` (ism, bio, avatar...).
PUBLIC_ACTIONS = {"log_client"}


async def _read_json_body(request: Request) -> dict:
    try:
        raw = await request.body()
    except Exception:
        return {}
    if not raw or not raw.strip():
        return {}
    try:
        decoded = json.loads(raw)
        return decoded if isinstance(decoded, dict) else {}
    except (ValueError, TypeError):
        return {}


def _dispatch_query_action(request: Request, action: str, body: dict, q):
    db_name = (q.get("db") or "").strip()

    table = {
        "storage_bootstrap": lambda: storage.bootstrap(request, body),
        "storage_sync": lambda: storage.sync(request, body),
        "storage_clear": lambda: storage.clear(request, body),
        "sport_get_all": lambda: sport.get_all(request, body),
        "sport_check_updates": lambda: sport.check_updates(request, body, q.get("last_sync", "")),
        "sport_delete_exercise": lambda: sport.delete_exercise(request, body),
        "get_structure": lambda: quiz.get_structure(request, body),
        "create_db": lambda: quiz.create_db(request, body),
        "rename_fan": lambda: quiz.rename_fan(request, body),
        "delete_fan": lambda: quiz.delete_fan(request, body),
        "rename_db": lambda: quiz.rename_db(request, body),
        "delete_db": lambda: quiz.delete_db(request, body),
        "upload_base": lambda: quiz.upload_base(request, body, db_name),
        "get_data": lambda: quiz.get_data(request, body, db_name),
        "mark_solved": lambda: quiz.mark_solved(request, body, db_name),
        "set_flag": lambda: quiz.set_flag(request, body, db_name),
        "reset_history": lambda: quiz.reset_history(request, body, db_name),
        "add_question": lambda: quiz.add_question(request, body, db_name),
        "edit_question": lambda: quiz.edit_question(request, body, db_name),
        "delete_question": lambda: quiz.delete_question(request, body, db_name),
        "mark_wrong": lambda: quiz.mark_wrong(request, body, db_name),
        "clear_wrong": lambda: quiz.clear_wrong(request, body, db_name),
        "save_wrong_snapshot": lambda: quiz.save_wrong_snapshot(request, body, db_name),
        "list_wrong_snapshots": lambda: quiz.list_wrong_snapshots(request, body, db_name),
        "get_wrong_snapshot": lambda: quiz.get_wrong_snapshot(
            request, body, int(q.get("id") or 0) if str(q.get("id") or "").isdigit() else 0
        ),
        "delete_wrong_snapshot": lambda: quiz.delete_wrong_snapshot(request, body),
        "save_quiz_result": lambda: quiz.save_quiz_result(request, body),
        "get_quiz_results": lambda: quiz.get_quiz_results(request, body, db_name),
        "add_goal_folder": lambda: goals.add_goal_folder(request, body),
        "edit_goal_folder": lambda: goals.edit_goal_folder(request, body),
        "delete_goal_folder": lambda: goals.delete_goal_folder(request, body),
        "add_goal_section": lambda: goals.add_goal_section(request, body),
        "edit_goal_section": lambda: goals.edit_goal_section(request, body),
        "delete_goal_section": lambda: goals.delete_goal_section(request, body),
        "add_goal": lambda: goals.add_goal(request, body),
        "toggle_goal": lambda: goals.toggle_goal(request, body),
        "edit_goal": lambda: goals.edit_goal(request, body),
        "delete_goal": lambda: goals.delete_goal(request, body),
        "get_dict_data": lambda: dictionary.get_dict_data(request, body, q.get("lang", "")),
        "save_dict_cat": lambda: dictionary.save_dict_cat(request, body),
        "rename_dict_cat": lambda: dictionary.rename_dict_cat(request, body),
        "delete_dict_cat": lambda: dictionary.delete_dict_cat(request, body),
        "get_mistakes": lambda: dictionary.get_mistakes(request, body, q.get("lang", ""), q.get("category", "")),
        "add_mistake": lambda: dictionary.add_mistake(request, body),
        "remove_mistake": lambda: dictionary.remove_mistake(request, body),
        "save_mistake_snapshot": lambda: dictionary.save_mistake_snapshot(request, body),
        "list_mistake_snapshots": lambda: dictionary.list_mistake_snapshots(request, body, q.get("lang", "")),
        "get_mistake_snapshot": lambda: dictionary.get_mistake_snapshot(
            request, body, int(q.get("id") or 0) if str(q.get("id") or "").isdigit() else 0
        ),
        "delete_mistake_snapshot": lambda: dictionary.delete_mistake_snapshot(request, body),
        "get_eng_settings": lambda: dictionary.get_eng_settings(request, body),
        "save_eng_settings": lambda: dictionary.save_eng_settings(request, body),
        "get_rus_settings": lambda: dictionary.get_rus_settings(request, body),
        "save_rus_settings": lambda: dictionary.save_rus_settings(request, body),
        "save_state": lambda: dictionary.save_state(request, body),
        "get_topics": lambda: language_topics.get_topics(request, body, q.get("lang", "")),
        "get_topic": lambda: language_topics.get_topic(
            request, body, int(q.get("id") or 0) if str(q.get("id") or "").isdigit() else 0
        ),
        "add_topic": lambda: language_topics.add_topic(request, body),
        "rename_topic": lambda: language_topics.rename_topic(request, body),
        "upload_topic_content": lambda: language_topics.upload_topic_content(request, body),
        "delete_topic": lambda: language_topics.delete_topic(request, body),
        "delete_lang_topics": lambda: language_topics.delete_lang_topics(request, body),
        "save_app_icon": lambda: misc.save_app_icon(request, body),
        "log_client": lambda: misc.log_client(request, body),
        "health": lambda: misc.health(request, body),
        "log_activity": lambda: activity.log_activity(request, body),
        "unlog_activity": lambda: activity.unlog_activity(request, body),
        "get_activity_log": lambda: activity.get_activity_log(
            request, body, q.get("from", ""), q.get("to", ""), q.get("section", "")
        ),
        # LMS (lms_connect/lms_sync — tarmoqqa chiqadi, shuning uchun async
        # tarmoqda alohida ushlanadi, quyidagi api_entry'ga qarang)
        "lms_status": lambda: lms.get_status(request, body),
        "lms_schedule": lambda: lms.get_schedule(request, body, q.get("from", ""), q.get("to", "")),
        "lms_options": lambda: lms.set_options(request, body),
        "lms_disconnect": lambda: lms.disconnect(request, body),

        # Favqulodda kirish kodi — boshqaruv Sozlamalardan chaqiriladi.
        # Kirishning O'ZI bu yerda EMAS: u `amal=kod_bilan_kirish` orqali
        # auth yo'lidan o'tadi, chunki bu yo'l sessiya talab qilmasligi
        # kerak. Bu uchtasi esa aksincha — faqat ichkaridan.
        "kirish_kodi_holati": lambda: auth.handle_auth_action(
            request, {"amal": "kirish_kodi_holati"}),
        "kirish_kodi_yangilash": lambda: auth.handle_auth_action(
            request, {"amal": "kirish_kodi_yangilash"}),
        "kirish_kodi_ochirish": lambda: auth.handle_auth_action(
            request, {"amal": "kirish_kodi_ochirish"}),
    }

    handler = table.get(action)
    if handler is None:
        raise ApiError(f"Noma'lum action: {action}", 400)
    return handler()


@app.api_route("/api", methods=["GET", "POST"])
async def api_entry(request: Request):
    q = request.query_params
    action = (q.get("action") or "").strip()

    # So'rov toshqinidan himoya (kichik serverni yiqilishdan saqlaydi).
    security.check_request_rate(request)

    # Auth gate: yozuv ham, o'qish ham himoyalangan (faqat PUBLIC_ACTIONS ochiq).
    if action and action not in PUBLIC_ACTIONS:
        security.require_write_access(request)

    # --- Boostday bot (alohida xizmatga proxy, async) ---
    if action.startswith("boost_"):
        boost_action = action[len("boost_"):]
        # Boost rejalari shaxsiy — o'qish uchun ham tizimga kirish shart.
        security.require_write_access(request)
        return await boost.proxy(request, await _read_json_body(request), boost_action)

    # --- Multipart / maxsus (JSON body o'qilmaydi) ---
    if action == "sport_save_exercise":
        return await sport.save_exercise(request)
    if action == "reja_upload":
        return await reja.upload(request)
    if action == "reja_file":
        file_id = int(q.get("id") or 0) if str(q.get("id") or "").isdigit() else 0
        return reja.serve(request, file_id, q.get("token", ""), str(q.get("download") or "") == "1")
    if action == "db_export":
        return await misc.db_export(request)
    if action == "db_import":
        return await misc.db_import(request)

    body = await _read_json_body(request)

    # --- LMS: tashqi saytga (lms.tuit.uz) chiqadigan async amallar ---
    if action == "lms_connect":
        return await lms.connect(request, body)
    if action == "lms_sync":
        return await lms.sync(request, body)

    if action != "":
        return _dispatch_query_action(request, action, body, q)

    if body.get("amal"):
        return auth.handle_auth_action(request, body)

    raise ApiError("So'rov noto'g'ri yuborilgan.", 400)


@app.get("/healthz")
async def healthz():
    return {"ok": True}


# --- LOKAL: `/boost/*` ni Boostday bot xizmatiga yo'naltiruvchi teskari proxy ---
# (Production'da nginx bu ishni bajaradi; BOOST_PROXY_URL bo'sh bo'lsa proxy o'chirilgan.)
if settings.BOOST_PROXY_URL:
    import httpx
    from fastapi import Response as _Resp

    _boost_client = httpx.AsyncClient(base_url=settings.BOOST_PROXY_URL.rstrip("/"), timeout=30.0)
    _HOP = {"content-length", "transfer-encoding", "connection", "content-encoding", "content-type", "host"}

    async def _boost_forward(request: Request, upstream_path: str):
        body = await request.body()
        headers = {k: v for k, v in request.headers.items() if k.lower() not in {"host", "content-length"}}
        try:
            r = await _boost_client.request(
                request.method, "/" + upstream_path,
                params=dict(request.query_params), content=body, headers=headers,
            )
        except Exception:  # noqa: BLE001
            logger.exception("BOOST_PROXY ulanish xatosi")
            return _Resp("Boost xizmatiga ulanib bo'lmadi (lokal).", status_code=502)
        resp_headers = {k: v for k, v in r.headers.items() if k.lower() not in _HOP}
        return _Resp(content=r.content, status_code=r.status_code, headers=resp_headers,
                     media_type=r.headers.get("content-type"))

    @app.api_route("/boost/{upstream_path:path}", methods=["GET", "POST", "OPTIONS"])
    async def _boost_proxy_path(request: Request, upstream_path: str):
        return await _boost_forward(request, "boost/" + upstream_path)


# --- Ixtiyoriy: statik frontend'ni shu app tarqatishi (nginx bo'lmasa) ---
if settings.SERVE_STATIC and settings.FRONTEND_ROOT.is_dir():
    from fastapi.staticfiles import StaticFiles

    app.mount("/", StaticFiles(directory=str(settings.FRONTEND_ROOT), html=True), name="static")
