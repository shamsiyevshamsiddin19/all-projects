"""Telegram Mini App — backend (arxitektura 11-bo'lim, BOSQICH 4).

- initData ni HMAC-SHA256 bilan tekshiradi (11.1 — K3 yechimi).
- Profil, video yuklash (chunked), jarayon (polling), natija.
- Dev-rejim (MINIAPP_DEV=1): brauzerда initData'siz sinash uchun.

Sahifa: GET /app  ·  Statik: /app/static/*  ·  API: /api/*
"""
from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import logging
import os
import shutil
import time
import uuid
from urllib.parse import parse_qsl

from aiogram.types import FSInputFile, InlineKeyboardButton, WebAppInfo
from aiohttp import web

from access import check_can_process
from config import settings
from db.crud import (
    create_donation,
    create_payment,
    create_video,
    effective_plan,
    finish_video,
    get_effective_settings,
    get_effective_tariff,
    get_or_create_user,
    get_user_by_tg,
    videos_done_today,
)
from web.server import base_url, publish_file
from worker.download import detect_source, download_video, probe_url
from worker.ffmpeg_utils import probe_duration
from worker.pipeline import cleanup, cleanup_all, job_paths, process_video_modes

logger = logging.getLogger(__name__)

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_MINIAPP_DIR = os.path.join(_BASE, "miniapp")

# Jarayon holatlari (xotirada — bitta jarayonli aiohttp uchun yetarli)
_JOBS: dict[str, dict] = {}

# Oldindan yuklangan ("staged") videolar — foydalanuvchi faylni tanlashi bilan
# yuklanadi, "Subtitr yozish" bosilganda darrov ishlovga o'tadi (vaqt ketmaydi).
_STAGED: dict[str, dict] = {}

# Bot username (main.py da get_me orqali o'rnatiladi) — Profil tugmalari uchun
BOT_USERNAME: str = ""

# Bot instansi (main.py da o'rnatiladi) — "Chatga yuborish" tugmasi uchun
BOT = None

_TRANSLATE_MODES = ("translate", "dual", "dual_vocab", "vocabulary")


def _dl_local(url: str) -> str:
    """Publish havolasidan (/dl/<token>.<ext>) lokal fayl yo'lini chiqaradi."""
    name = os.path.basename(url.rsplit("/dl/", 1)[-1].split("?")[0])
    return os.path.join(settings.download_dir, name)


def _read_modes(src: dict) -> list[str]:
    """So'rovdan rejim(lar)ni o'qiydi — `modes` (ro'yxat/vergulli) yoki `mode`."""
    raw = src.get("modes")
    if isinstance(raw, list):
        modes = [str(m) for m in raw if m]
    elif isinstance(raw, str):
        modes = [m for m in raw.split(",") if m]
    else:
        modes = []
    if not modes:
        modes = [src.get("mode", "original")]
    out: list[str] = []
    for m in modes:  # takrorlanmasin, tartib saqlansin
        if m not in out:
            out.append(m)
    return out


# ---------------------------------------------------------------- auth

def verify_init_data(init_data: str, bot_token: str, max_age: int = 86400) -> dict | None:
    """Telegram initData ni tekshiradi. To'g'ri bo'lsa user dict, aks holda None."""
    if not init_data:
        return None
    try:
        parsed = dict(parse_qsl(init_data, keep_blank_values=True))
    except (ValueError, TypeError):
        return None
    received_hash = parsed.pop("hash", None)
    if not received_hash:
        return None
    data_check = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    calc_hash = hmac.new(secret_key, data_check.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(calc_hash, received_hash):
        return None
    try:
        auth_date = int(parsed.get("auth_date", "0"))
    except ValueError:
        return None
    if max_age and time.time() - auth_date > max_age:
        return None
    user = None
    if parsed.get("user"):
        try:
            user = json.loads(parsed["user"])
        except (ValueError, TypeError):
            user = None
    return {"user": user, "auth_date": auth_date}


# ---------------------------------------------------------------- brauzer token

def make_web_token(telegram_id: int, days: int = 30) -> str:
    """Brauzerda kirish uchun imzolangan token (stateless, HMAC). Botda
    yaratiladi → /app?t=TOKEN havolasi. Telegram tashqarisida auth qiladi."""
    exp = int(time.time()) + days * 86400
    msg = f"{telegram_id}.{exp}"
    sig = hmac.new(settings.bot_token.encode(), msg.encode(), hashlib.sha256).hexdigest()[:32]
    raw = f"{msg}.{sig}"
    return base64.urlsafe_b64encode(raw.encode()).decode().rstrip("=")


def verify_web_token(token: str) -> int | None:
    """Brauzer tokenini tekshiradi. To'g'ri va muddati o'tmagan bo'lsa
    telegram_id, aks holda None."""
    if not token:
        return None
    try:
        pad = "=" * (-len(token) % 4)
        raw = base64.urlsafe_b64decode(token + pad).decode()
        tid_s, exp_s, sig = raw.split(".")
        msg = f"{tid_s}.{exp_s}"
        expect = hmac.new(settings.bot_token.encode(), msg.encode(), hashlib.sha256).hexdigest()[:32]
        if not hmac.compare_digest(expect, sig):
            return None
        if int(exp_s) < int(time.time()):
            return None
        return int(tid_s)
    except (ValueError, TypeError):
        return None


async def _auth_user(request: web.Request):
    """So'rovdan foydalanuvchini aniqlaydi (initData / brauzer token / dev)."""
    init_data = request.headers.get("X-Init-Data", "")
    info = verify_init_data(init_data, settings.bot_token)
    if info and info.get("user"):
        u = info["user"]
        return await get_or_create_user(int(u["id"]), u.get("username"))
    # Brauzer token (Telegram tashqarisida — bot bergan havola orqali)
    wt = request.headers.get("X-Web-Token", "")
    tid = verify_web_token(wt)
    if tid is not None:
        return await get_user_by_tg(tid)
    if settings.miniapp_dev:
        dev_id = next(iter(settings.admin_id_set), 1)
        return await get_or_create_user(dev_id, "dev")
    return None


# ---------------------------------------------------------------- API: me

async def api_me(request: web.Request) -> web.Response:
    user = await _auth_user(request)
    if user is None:
        return web.json_response({"error": "unauthorized"}, status=401)
    plan = effective_plan(user)
    tariff = await get_effective_tariff(plan)
    used = await videos_done_today(user.id)
    eff = await get_effective_settings()
    return web.json_response({
        "username": user.username,
        "telegram_id": user.telegram_id,
        "blocked": user.is_blocked,
        "plan": plan,
        "plan_title": tariff.title,
        "daily": tariff.daily_videos,
        "used": used,
        "max_minutes": tariff.max_minutes,
        "modes": list(tariff.modes),
        "plan_until": (
            user.plan_until.strftime("%d.%m.%Y")
            if user.plan_until and plan != "free" else None
        ),
        "max_mb": settings.miniapp_max_mb,
        "bot_username": BOT_USERNAME,
        "price_basic": eff["price_basic"],
        "price_premium": eff["price_premium"],
        "sub_days": eff.get("sub_days", settings.sub_days),
        "pay_enabled": settings.click_configured,
    })


# ---------------------------------------------------------------- API: weblink/public

async def api_weblink(request: web.Request) -> web.Response:
    """Joriy foydalanuvchi uchun brauzerda ochiladigan (tokenli) havola."""
    user = await _auth_user(request)
    if user is None:
        return web.json_response({"error": "unauthorized"}, status=401)
    token = make_web_token(user.telegram_id)
    return web.json_response({"url": f"{base_url()}/app?t={token}"})


async def api_public(request: web.Request) -> web.Response:
    """Auth talab qilmaydigan ma'lumot — landing sahifasi uchun (bot, narxlar)."""
    eff = await get_effective_settings()
    return web.json_response({
        "bot_username": BOT_USERNAME,
        "price_basic": eff["price_basic"],
        "price_premium": eff["price_premium"],
        "sub_days": eff.get("sub_days", settings.sub_days),
    })


# ---------------------------------------------------------------- API: subscribe

async def api_subscribe(request: web.Request) -> web.Response:
    """Tanlangan tarif uchun to'lov yozuvi yaratib, Click havolasini qaytaradi.

    Mini App shu havolani ochadi → Click ilovasi ishga tushadi. To'lov tugagach
    myxvest ko'prigi orqali callback keladi va obuna avtomatik faollashadi.
    """
    user = await _auth_user(request)
    if user is None:
        return web.json_response({"error": "unauthorized"}, status=401)
    if not settings.click_configured:
        return web.json_response(
            {"error": "To'lov hozircha mavjud emas. Keyinroq urinib ko'ring."},
            status=503,
        )
    try:
        data = await request.json()
    except Exception:
        data = {}
    plan = (data.get("plan") or "basic").strip().lower()
    if plan not in ("basic", "premium"):
        plan = "basic"

    eff = await get_effective_settings()
    amount = eff["price_premium"] if plan == "premium" else eff["price_basic"]
    payment_id = await create_payment(user.id, plan, amount)
    pay_url = settings.click_pay_url(f"SUBT{payment_id}", amount)
    return web.json_response({"pay_url": pay_url, "plan": plan, "amount": amount})


async def api_donate(request: web.Request) -> web.Response:
    """Donat — summa + izoh qabul qilib, Click havolasini qaytaradi.

    transaction_param "SUBTD{id}" — myxvest ko'prigi donat callback'ini botga
    uzatadi, to'lov tugagach web/click.py donatni "paid" qiladi.
    """
    user = await _auth_user(request)
    if user is None:
        return web.json_response({"error": "unauthorized"}, status=401)
    if not settings.click_configured:
        return web.json_response(
            {"error": "To'lov hozircha mavjud emas."}, status=503)
    try:
        data = await request.json()
    except Exception:
        data = {}
    try:
        amount = int(data.get("amount") or 0)
    except (ValueError, TypeError):
        amount = 0
    if amount < 1000:
        return web.json_response(
            {"error": "Minimal summa 1 000 so'm."}, status=400)
    if amount > 100_000_000:
        return web.json_response({"error": "Juda katta summa."}, status=400)
    comment = (data.get("comment") or "").strip()[:200] or None

    donation_id = await create_donation(user.id, amount, comment)
    pay_url = settings.click_pay_url(f"SUBTD{donation_id}", amount)
    return web.json_response({"pay_url": pay_url, "amount": amount})


async def api_donors(request: web.Request) -> web.Response:
    """Minnatdorchilik devori — to'langan donatlar ro'yxati (profil pasti).

    Auth talab qilmaydi (api_public kabi): maxfiy ma'lumot yo'q — faqat
    ko'rsatishga ruxsat etilgan homiylar va tasdiqlangan izohlar.
    """
    from db.crud import list_wall_donations

    donors = await list_wall_donations()
    return web.json_response({"donors": donors})


# ---------------------------------------------------------------- API: upload

def _parse_style(raw, user):
    """Uslubni qaytaradi (dict yoki None). Bepul tarif -> None (standart uslub)."""
    if effective_plan(user) == "free":
        return None
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str) and raw.strip():
        try:
            return json.loads(raw)
        except (ValueError, TypeError):
            return None
    return None


async def _save_upload(part, dest: str, max_bytes: int) -> int:
    size = 0
    with open(dest, "wb") as f:
        while True:
            chunk = await part.read_chunk(1 << 16)
            if not chunk:
                break
            size += len(chunk)
            if size > max_bytes:
                f.close()
                try:
                    os.remove(dest)
                except OSError:
                    pass
                raise ValueError("Fayl juda katta")
            f.write(chunk)
    return size


async def api_upload(request: web.Request) -> web.Response:
    user = await _auth_user(request)
    if user is None:
        return web.json_response({"error": "unauthorized"}, status=401)
    if user.is_blocked:
        return web.json_response({"error": "Hisobingiz bloklangan."}, status=403)

    os.makedirs(settings.work_dir, exist_ok=True)
    job_id = uuid.uuid4().hex[:12]
    paths = job_paths(job_id)
    fields: dict[str, str] = {}
    got_file = False

    try:
        reader = await request.multipart()
        while True:
            part = await reader.next()
            if part is None:
                break
            if part.name == "file":
                await _save_upload(part, paths["video"], settings.miniapp_max_mb * 1024 * 1024)
                got_file = True
            else:
                fields[part.name] = (await part.text()).strip()
    except ValueError as exc:
        return web.json_response({"error": str(exc)}, status=413)
    except Exception:
        logger.exception("Mini App upload xatosi")
        return web.json_response({"error": "Yuklashda xatolik"}, status=400)

    if not got_file:
        return web.json_response({"error": "Video fayl topilmadi"}, status=400)

    modes = _read_modes(fields)
    lang = fields.get("lang", "auto")
    style = _parse_style(fields.get("style"), user)

    tariff = await get_effective_tariff(effective_plan(user))
    bad = [m for m in modes if m not in tariff.modes]
    if bad:
        cleanup(job_id)
        return web.json_response(
            {"error": f"'{bad[0]}' rejimi {tariff.title} tarifida yo'q."}, status=403
        )
    ok, reason = await check_can_process(user, 0, mode="")
    if not ok:
        cleanup(job_id)
        return web.json_response({"error": reason}, status=403)

    if any(m in _TRANSLATE_MODES for m in modes):
        source_lang, target_lang = "auto", lang
    else:
        source_lang, target_lang = lang, None

    video_id = await create_video(
        user.id, ",".join(modes), 0, source_type="miniapp", target_lang=target_lang
    )
    _JOBS[job_id] = {
        "state": "processing", "progress": "📥 Qabul qilindi, navbatda...",
        "result_url": None, "kind": None, "error": None,
    }
    asyncio.create_task(_run_job(
        job_id, paths["video"], modes, source_lang, target_lang,
        video_id, tariff.max_minutes, style=style,
    ))
    return web.json_response({"job_id": job_id})


# ---------------------------------------------------------------- API: stage/process

async def api_stage(request: web.Request) -> web.Response:
    """Faylni oldindan yuklab, vaqtinchalik saqlaydi (stage_id qaytaradi).

    Frontend faylni tanlashi bilan chaqiradi — yuklash foydalanuvchi rejim/til
    tanlayotgan vaqtda fonда tugaydi. Keyin api_process darrov ishlovni boshlaydi.
    """
    user = await _auth_user(request)
    if user is None:
        return web.json_response({"error": "unauthorized"}, status=401)
    if user.is_blocked:
        return web.json_response({"error": "Hisobingiz bloklangan."}, status=403)

    os.makedirs(settings.work_dir, exist_ok=True)
    stage_id = uuid.uuid4().hex[:12]
    dest = os.path.join(settings.work_dir, f"stage_{stage_id}.mp4")
    got = False
    try:
        reader = await request.multipart()
        while True:
            part = await reader.next()
            if part is None:
                break
            if part.name == "file":
                await _save_upload(part, dest, settings.miniapp_max_mb * 1024 * 1024)
                got = True
    except ValueError as exc:
        return web.json_response({"error": str(exc)}, status=413)
    except Exception:
        logger.exception("Mini App stage xatosi")
        return web.json_response({"error": "Yuklashda xatolik"}, status=400)
    if not got:
        return web.json_response({"error": "Video fayl topilmadi"}, status=400)

    _STAGED[stage_id] = {"path": dest, "user_id": user.id, "ts": time.time()}
    return web.json_response({"stage_id": stage_id})


async def api_process(request: web.Request) -> web.Response:
    """Oldindan yuklangan (staged) videoni ishlovga yuboradi."""
    user = await _auth_user(request)
    if user is None:
        return web.json_response({"error": "unauthorized"}, status=401)

    try:
        data = await request.json()
    except Exception:
        data = {}
    stage_id = (data.get("stage_id") or "").strip()
    staged = _STAGED.get(stage_id)
    if not staged or staged["user_id"] != user.id or not os.path.isfile(staged["path"]):
        return web.json_response(
            {"error": "Yuklangan video topilmadi. Iltimos videoni qaytadan tanlang."},
            status=400,
        )

    modes = _read_modes(data)
    lang = data.get("lang", "auto")
    style = _parse_style(data.get("style"), user)

    tariff = await get_effective_tariff(effective_plan(user))
    bad = [m for m in modes if m not in tariff.modes]
    if bad:
        return web.json_response(
            {"error": f"'{bad[0]}' rejimi {tariff.title} tarifida yo'q."}, status=403
        )
    ok, reason = await check_can_process(user, 0, mode=(modes[0] if modes else ""))
    if not ok:
        return web.json_response({"error": reason}, status=403)

    if "transcript" in modes:
        source_lang = "auto"
        target_lang = None if lang in ("none", "", None) else lang
    elif any(m in _TRANSLATE_MODES for m in modes):
        source_lang, target_lang = "auto", lang
    else:
        source_lang, target_lang = lang, None

    # Staged faylni job video yo'liga NUSXALAYMIZ (asl staged saqlanadi —
    # foydalanuvchi shu videodan boshqa rejimni qayta yozdira oladi, qayta
    # yuklamasdan). TTL yangilanadi, eskirsa cleanup_jobs_loop o'chiradi.
    staged["ts"] = time.time()
    job_id = uuid.uuid4().hex[:12]
    paths = job_paths(job_id)
    try:
        shutil.copy(staged["path"], paths["video"])
    except OSError:
        logger.exception("Staged faylni nusxalab bo'lmadi")
        return web.json_response({"error": "Ichki xatolik. Qayta urinib ko'ring."}, status=500)

    video_id = await create_video(
        user.id, ",".join(modes), 0, source_type="miniapp", target_lang=target_lang
    )
    _JOBS[job_id] = {
        "state": "processing", "progress": "Qabul qilindi, navbatda...",
        "result_url": None, "kind": None, "error": None,
    }
    asyncio.create_task(_run_job(
        job_id, paths["video"], modes, source_lang, target_lang,
        video_id, tariff.max_minutes, style=style,
    ))
    return web.json_response({"job_id": job_id})


async def _run_job(job_id, in_path, modes, source_lang, target_lang,
                   video_id, max_minutes, url=None, style=None) -> None:
    job = _JOBS[job_id]

    async def progress(text: str) -> None:
        job["progress"] = text

    try:
        if url:
            job["progress"] = "Video havoladan yuklab olinmoqda..."
            await asyncio.to_thread(download_video, url, in_path)
        duration = await asyncio.to_thread(probe_duration, in_path)
        if max_minutes and duration > max_minutes * 60:
            raise RuntimeError(
                f"Video {int(duration // 60)} daqiqa — tarif limiti {max_minutes} daqiqa."
            )
        results = await process_video_modes(
            in_path, job_id, progress,
            modes=modes, source_lang=source_lang, target_lang=target_lang, style=style,
        )

        # Har natijani publish qilamiz + chatga yuborish ro'yxatini yig'amiz
        out_results: list[dict] = []
        chat_files: list[dict] = []
        for out_path, kind, mode in results:
            if kind in ("text", "vocab"):
                base = out_path[:-4]
                try:
                    with open(out_path, encoding="utf-8-sig") as f:
                        preview = f.read(8000)
                except OSError:
                    preview = ""
                try:
                    with open(base + ".title", encoding="utf-8-sig") as f:
                        slug = f.read().strip()
                except OSError:
                    slug = ""
                slug = slug or ("matn" if kind == "text" else "lugat")
                txt_url = publish_file(out_path, ".txt")
                pdf_url = publish_file(base + ".pdf", ".pdf")
                out_results.append({"kind": kind, "mode": mode, "preview": preview,
                                    "txt_url": txt_url, "pdf_url": pdf_url})
                chat_files += [
                    {"path": _dl_local(pdf_url), "name": slug + ".pdf"},
                    {"path": _dl_local(txt_url), "name": slug + ".txt"},
                ]
            else:
                # kind: srt / audio / video
                if kind == "srt":
                    suffix, fname = ".srt", "subtitle.srt"
                elif kind == "audio":
                    suffix, fname = ".mp3", "audio.mp3"
                else:
                    suffix, fname = ".mp4", "subtitled.mp4"
                u = publish_file(out_path, suffix)
                out_results.append({"kind": kind, "mode": mode, "result_url": u})
                chat_files.append({"path": _dl_local(u), "name": fname})

        if len(out_results) == 1:
            r = out_results[0]
            common = dict(state="done", progress="Tayyor!", kind=r["kind"],
                          done_at=time.time(), chat_files=chat_files)
            if r["kind"] in ("text", "vocab"):
                job.update(result_url=r["pdf_url"], txt_url=r["txt_url"],
                           pdf_url=r["pdf_url"], preview=r["preview"], **common)
            else:
                job.update(result_url=r["result_url"], **common)
        else:
            job.update(state="done", progress="Tayyor!", kind="multi",
                       results=out_results, chat_files=chat_files, done_at=time.time())
        await finish_video(video_id, "done")
    except Exception as exc:
        logger.exception("Mini App job xatosi (%s)", job_id)
        job.update(state="error", progress="Xatolik", error=str(exc),
                   done_at=time.time())
        await finish_video(video_id, "error", error_message=str(exc))
    finally:
        cleanup_all(job_id)


async def cleanup_jobs_loop() -> None:
    """Tugagan joblarni vaqti-vaqti bilan xotiradan o'chiradi (TTL 1 soat)."""
    while True:
        await asyncio.sleep(600)
        try:
            now = time.time()
            stale = [
                jid for jid, j in _JOBS.items()
                if j.get("done_at") and now - j["done_at"] > 3600
            ]
            for jid in stale:
                _JOBS.pop(jid, None)
            # Tashlab ketilgan staged videolar (1 soatdan oshgan) — o'chiramiz
            stale_st = [sid for sid, s in _STAGED.items() if now - s.get("ts", now) > 3600]
            for sid in stale_st:
                s = _STAGED.pop(sid, None)
                if s:
                    try:
                        os.remove(s["path"])
                    except OSError:
                        pass
        except Exception:
            logger.exception("Mini App job tozalash xatosi")


async def api_url(request: web.Request) -> web.Response:
    user = await _auth_user(request)
    if user is None:
        return web.json_response({"error": "unauthorized"}, status=401)
    if user.is_blocked:
        return web.json_response({"error": "Hisobingiz bloklangan."}, status=403)

    try:
        data = await request.json()
    except Exception:
        data = dict(await request.post())
    url = (data.get("url") or "").strip()
    modes = _read_modes(data)
    lang = data.get("lang", "auto")
    style = _parse_style(data.get("style"), user)

    source = detect_source(url)
    if not source:
        return web.json_response(
            {"error": "Faqat YouTube va Instagram havolalari qabul qilinadi."},
            status=400,
        )
    tariff = await get_effective_tariff(effective_plan(user))
    bad = [m for m in modes if m not in tariff.modes]
    if bad:
        return web.json_response(
            {"error": f"'{bad[0]}' rejimi {tariff.title} tarifida yo'q."}, status=403
        )
    try:
        info = await asyncio.to_thread(probe_url, url)
    except Exception:
        logger.warning("Mini App havola tekshirilmadi: %s", url, exc_info=True)
        if source == "instagram":
            msg = ("Instagram hozircha cheklangan. Videoni Instagram'dan yuklab "
                   "olib, «Fayl» orqali to'g'ridan-to'g'ri yuboring.")
        else:
            msg = "Havoladan video olib bo'lmadi (shaxsiy yoki o'chirilgan?)."
        return web.json_response({"error": msg}, status=400)
    duration = info["duration"]
    ok, reason = await check_can_process(user, duration, mode=(modes[0] if modes else ""))
    if not ok:
        return web.json_response({"error": reason}, status=403)

    if "transcript" in modes:
        source_lang = "auto"
        target_lang = None if lang in ("none", "", None) else lang
    elif any(m in _TRANSLATE_MODES for m in modes):
        source_lang, target_lang = "auto", lang
    else:
        source_lang, target_lang = lang, None

    os.makedirs(settings.work_dir, exist_ok=True)
    job_id = uuid.uuid4().hex[:12]
    paths = job_paths(job_id)
    video_id = await create_video(
        user.id, ",".join(modes), duration, source_type=source, target_lang=target_lang
    )
    _JOBS[job_id] = {
        "state": "processing", "progress": "🔗 Havola qabul qilindi...",
        "result_url": None, "kind": None, "error": None,
    }
    asyncio.create_task(_run_job(
        job_id, paths["video"], modes, source_lang, target_lang,
        video_id, tariff.max_minutes, url=url, style=style,
    ))
    return web.json_response({"job_id": job_id})


async def api_status(request: web.Request) -> web.Response:
    user = await _auth_user(request)
    if user is None:
        return web.json_response({"error": "unauthorized"}, status=401)
    job = _JOBS.get(request.match_info["job_id"])
    if not job:
        return web.json_response({"state": "unknown"})
    resp = {k: job[k] for k in ("state", "progress", "result_url", "kind", "error")}
    if job.get("kind") in ("text", "vocab"):
        resp["txt_url"] = job.get("txt_url")
        resp["pdf_url"] = job.get("pdf_url")
        resp["preview"] = job.get("preview")
    elif job.get("kind") == "multi":
        resp["results"] = job.get("results")
    return web.json_response(resp)


async def api_send_chat(request: web.Request) -> web.Response:
    """Tayyor natija fayl(lar)ini foydalanuvchining Telegram chatiga yuboradi."""
    user = await _auth_user(request)
    if user is None:
        return web.json_response({"error": "unauthorized"}, status=401)
    if BOT is None:
        return web.json_response({"error": "Bot hozircha mavjud emas."}, status=503)
    try:
        data = await request.json()
    except Exception:
        data = {}
    job = _JOBS.get((data.get("job_id") or "").strip())
    if not job or job.get("state") != "done":
        return web.json_response({"error": "Natija topilmadi yoki muddati o'tgan."}, status=400)
    files = job.get("chat_files") or []

    sent = 0
    for f in files:
        path = f.get("path")
        if not path or not os.path.isfile(path):
            continue
        name = str(f.get("name", ""))
        # Telegram Bot API 50MB'gача fayl yuboradi. Kattaroq natija (odatda
        # video) — to'g'ridan-to'g'ri yuborilmaydi (TelegramEntityTooLarge),
        # shuning uchun web-havola yuboramiz (celery_app dagi kabi).
        size_mb = os.path.getsize(path) / (1024 * 1024)
        try:
            if size_mb > settings.max_send_mb:
                dl_url = publish_file(path)
                await BOT.send_message(
                    user.telegram_id,
                    f"🎬 Natija tayyor! Fayl katta ({size_mb:.0f}MB) — havola "
                    f"orqali yuklab oling:\n{dl_url}\n\n@subtitle_srtbot",
                    disable_web_page_preview=True,
                )
            elif name.lower().endswith(".mp4"):
                await BOT.send_video(
                    user.telegram_id, FSInputFile(path, filename=name),
                    caption="🎬 Subtitr tayyor!\n\n@subtitle_srtbot",
                )
            else:
                await BOT.send_document(
                    user.telegram_id, FSInputFile(path, filename=name),
                    caption="@subtitle_srtbot",
                )
            sent += 1
        except Exception:
            logger.exception("Chatga yuborib bo'lmadi (%s)", path)
    if sent == 0:
        return web.json_response(
            {"error": "Yuborib bo'lmadi. Avval botni /start qiling."}, status=400)
    return web.json_response({"ok": True, "sent": sent})


# ---------------------------------------------------------------- sahifa

_NO_CACHE = {"Cache-Control": "no-cache, must-revalidate"}


async def _index(request: web.Request) -> web.Response:
    path = os.path.join(_MINIAPP_DIR, "index.html")
    if not os.path.isfile(path):
        return web.Response(status=404, text="Mini App topilmadi")
    return web.FileResponse(path, headers=_NO_CACHE)


async def _static(request: web.Request) -> web.Response:
    name = os.path.basename(request.match_info["name"])
    if name not in ("style.css", "app.js"):
        return web.Response(status=404)
    path = os.path.join(_MINIAPP_DIR, name)
    if not os.path.isfile(path):
        return web.Response(status=404)
    return web.FileResponse(path, headers=_NO_CACHE)


async def _landing(request: web.Request) -> web.Response:
    """Ommaviy landing sahifasi (/) — brauzer tashrifchilari uchun marketing."""
    path = os.path.join(_MINIAPP_DIR, "landing.html")
    if not os.path.isfile(path):
        return web.Response(status=404, text="Sahifa topilmadi")
    return web.FileResponse(path, headers=_NO_CACHE)


def miniapp_open_button(text: str = "📱 Mini App'da ochish") -> InlineKeyboardButton:
    """Mini App ochish tugmasi. HTTPS bo'lsa web_app (Telegram ichida), aks
    holda oddiy havola (brauzerда ochiladi — Telegram web_app HTTPS talab qiladi)."""
    url = f"{base_url()}/app"
    if settings.public_base_url.startswith("https"):
        return InlineKeyboardButton(text=text, web_app=WebAppInfo(url=url))
    return InlineKeyboardButton(text=text, url=url)


def setup_miniapp_routes(app: web.Application) -> None:
    app.router.add_get("/", _landing)
    app.router.add_get("/web", _landing)
    app.router.add_get("/app", _index)
    app.router.add_get("/app/", _index)
    app.router.add_post("/api/me", api_me)
    app.router.add_post("/api/public", api_public)
    app.router.add_get("/api/public", api_public)
    app.router.add_post("/api/weblink", api_weblink)
    app.router.add_post("/api/subscribe", api_subscribe)
    app.router.add_post("/api/donate", api_donate)
    app.router.add_get("/api/donors", api_donors)
    app.router.add_post("/api/stage", api_stage)
    app.router.add_post("/api/process", api_process)
    app.router.add_post("/api/upload", api_upload)
    app.router.add_post("/api/url", api_url)
    app.router.add_get("/api/status/{job_id}", api_status)
    app.router.add_post("/api/send", api_send_chat)
    app.router.add_get("/app/static/{name}", _static)
    app.router.add_static("/static/", path=os.path.join(_MINIAPP_DIR, "static"), name="static")
    app.router.add_get("/favicon.ico", lambda r: web.Response(status=204))
