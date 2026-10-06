"""Click ko'prik API — eski server PHP click_prepare/complete shu yerga
BAZA_ to'lovlarni uzatadi (maxfiy sir bilan). Imzo tekshiruvi PHP'da qoladi;
bu yer faqat to'lov holatini boshqaradi va aktivlashtirish kodini yuboradi.

Javob formati: {"error": <click_error_code>, "prepare_id": <id>}.
Click error kodlari PHP'dagi bilan bir xil (0=ok, -2 amount, -4 paid,
-5 not exist, -6 tx mismatch, -9 cancelled).
"""
from __future__ import annotations

import logging

from aiogram import Bot
from aiohttp import web

import db
from config import settings

logger = logging.getLogger(__name__)

_FINAL = ("cancelled", "failed", "replaced")


def _resolve_payment_id(merchant_trans_id: str) -> int:
    s = str(merchant_trans_id or "")
    if s.startswith(settings.click_tx_prefix):
        s = s[len(settings.click_tx_prefix):]
    return int(s) if s.isdigit() else 0


def _amounts_match(a, b) -> bool:
    try:
        return round(float(a)) == round(float(b))
    except (TypeError, ValueError):
        return False


def _err(code: int, prepare_id: int | None = None) -> web.Response:
    body = {"error": code}
    if prepare_id is not None:
        body["prepare_id"] = prepare_id
    return web.json_response(body)


def setup_click_routes(app: web.Application, bot: Bot) -> None:
    async def _auth(request: web.Request) -> dict | None:
        try:
            data = await request.json()
        except Exception:
            return None
        if data.get("secret") != settings.internal_secret:
            return None
        return data

    async def prepare(request: web.Request) -> web.Response:
        data = await _auth(request)
        if data is None:
            return web.json_response({"error": -1, "note": "forbidden"}, status=403)

        payment_id = _resolve_payment_id(data.get("merchant_trans_id"))
        if payment_id <= 0:
            return _err(-5)
        p = await db.payment_by_id(payment_id)
        if not p:
            return _err(-5)
        if not _amounts_match(data.get("amount"), p["amount"]):
            return _err(-2, payment_id)

        status = p["status"]
        if status == "paid":
            return _err(-4, payment_id)
        if status in _FINAL:
            return _err(-9, payment_id)

        click_trans_id = str(data.get("click_trans_id") or "")
        stored = p["click_trans_id"] or ""
        if stored and stored != click_trans_id:
            return _err(-9, payment_id)

        await db.pool().execute(
            """UPDATE payments SET click_trans_id = $1, amount = $2,
               status = 'pending', paid_at = NULL WHERE id = $3""",
            click_trans_id, int(round(float(p["amount"]))), payment_id,
        )
        logger.info("Baza prepare ok: payment=%s click=%s", payment_id, click_trans_id)
        return _err(0, payment_id)

    async def complete(request: web.Request) -> web.Response:
        data = await _auth(request)
        if data is None:
            return web.json_response({"error": -1, "note": "forbidden"}, status=403)

        payment_id = _resolve_payment_id(data.get("merchant_trans_id"))
        if payment_id <= 0:
            return _err(-5)

        merchant_prepare_id = int(data.get("merchant_prepare_id") or 0)
        if merchant_prepare_id <= 0 or merchant_prepare_id != payment_id:
            return _err(-6, payment_id)

        p = await db.payment_by_id(payment_id)
        if not p:
            return _err(-5, payment_id)
        if not _amounts_match(data.get("amount"), p["amount"]):
            return _err(-2, payment_id)

        click_trans_id = str(data.get("click_trans_id") or "")
        stored = p["click_trans_id"] or ""
        if stored and stored != click_trans_id:
            return _err(-6, payment_id)

        status = p["status"]
        if status == "paid":
            return _err(0, payment_id)  # idempotent
        if status in _FINAL:
            return _err(-9, payment_id)

        click_error = int(data.get("click_error") or data.get("error") or 0)
        if click_error != 0:
            failed = "cancelled" if click_error < 0 else "failed"
            await db.pool().execute(
                "UPDATE payments SET click_trans_id = $1, status = $2, paid_at = NULL WHERE id = $3",
                click_trans_id, failed, payment_id,
            )
            logger.info("Baza complete bekor: payment=%s status=%s", payment_id, failed)
            return _err(-9, payment_id)

        amount = int(round(float(p["amount"])))
        await db.pool().execute(
            "UPDATE payments SET click_trans_id = $1, amount = $2, status = 'paid', paid_at = now() WHERE id = $3",
            click_trans_id, amount, payment_id,
        )
        await db.increment_stats(amount)

        # Aktivlashtirish kodini yuboramiz
        from bot import deliver_activation_key
        try:
            await deliver_activation_key(bot, int(p["chat_id"]), p["base_num"], p["hwid"])
        except Exception:
            logger.exception("Kod yuborilmadi: payment=%s", payment_id)

        logger.info("Baza complete ok: payment=%s chat=%s", payment_id, p["chat_id"])
        return _err(0, payment_id)

    app.router.add_post("/click/baza/prepare", prepare)
    app.router.add_post("/click/baza/complete", complete)
