"""Click to'lov webhook (SHOP-API): Prepare + Complete (arxitektura 10-bo'lim).

Click ikki marta murojaat qiladi:
  action=0 (Prepare)  — buyurtmani tasdiqlaymiz
  action=1 (Complete) — to'lov yakunlanadi -> obuna faollashadi

Har bir so'rovda imzo (md5 sign_string) tekshiriladi.
"""
from __future__ import annotations

import hashlib
import json
import logging

from aiogram import Bot
from aiohttp import web

from config import settings
from db.crud import (
    get_donation,
    get_effective_settings,
    get_payment,
    get_user_by_id,
    mark_donation_paid,
    mark_payment_paid,
    set_plan,
)


async def _lookup_order(mtid: str):
    """merchant_trans_id -> (tur, yozuv).

    Ko'prik (myxvest PHP) orqali keladigan prefikslar:
      ``SUBTD<id>`` = donat,  ``SUBT<id>`` = obuna.
    Eski/to'g'ridan format ham qo'llab-quvvatlanadi: ``d<id>`` = donat,
    sof son = obuna.
    """
    mtid = (mtid or "").strip()
    if mtid.startswith("SUBTD"):
        digits = mtid[5:]
        return "donation", (await get_donation(int(digits)) if digits.isdigit() else None)
    if mtid.startswith("SUBT"):
        digits = mtid[4:]
        return "payment", (await get_payment(int(digits)) if digits.isdigit() else None)
    if mtid.startswith("d"):
        digits = mtid[1:]
        return "donation", (await get_donation(int(digits)) if digits.isdigit() else None)
    return "payment", (await get_payment(int(mtid)) if mtid.isdigit() else None)

logger = logging.getLogger(__name__)


def _md5(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def _prepare_sign(p: dict) -> str:
    return _md5(
        f"{p.get('click_trans_id','')}{p.get('service_id','')}"
        f"{settings.click_secret_key}{p.get('merchant_trans_id','')}"
        f"{p.get('amount','')}{p.get('action','')}{p.get('sign_time','')}"
    )


def _complete_sign(p: dict) -> str:
    return _md5(
        f"{p.get('click_trans_id','')}{p.get('service_id','')}"
        f"{settings.click_secret_key}{p.get('merchant_trans_id','')}"
        f"{p.get('merchant_prepare_id','')}{p.get('amount','')}"
        f"{p.get('action','')}{p.get('sign_time','')}"
    )


def _err(p: dict, code: int, note: str, confirm: bool = False) -> web.Response:
    body = {
        "click_trans_id": p.get("click_trans_id", ""),
        "merchant_trans_id": p.get("merchant_trans_id", ""),
        "error": code,
        "error_note": note,
    }
    # Click javobда tegishli id maydonini ham kutadi (prepare/complete).
    if confirm:
        body["merchant_confirm_id"] = p.get("merchant_prepare_id", 0) or 0
    else:
        body["merchant_prepare_id"] = 0
    return web.json_response(body)


async def _handle_prepare(request: web.Request) -> web.Response:
    p = dict(await request.post())
    if _prepare_sign(p) != p.get("sign_string", ""):
        return _err(p, -1, "SIGN CHECK FAILED")

    _kind, order = await _lookup_order(p.get("merchant_trans_id", ""))
    if not order:
        return _err(p, -5, "Order not found")
    if order.status == "paid":
        return _err(p, -4, "Already paid")
    try:
        if abs(float(p.get("amount", "0")) - float(order.amount)) > 0.01:
            return _err(p, -2, "Incorrect amount")
    except ValueError:
        return _err(p, -2, "Incorrect amount")

    return web.json_response(
        {
            "click_trans_id": p.get("click_trans_id", ""),
            "merchant_trans_id": p.get("merchant_trans_id", ""),
            "merchant_prepare_id": order.id,
            "error": 0,
            "error_note": "Success",
        }
    )


def make_complete_handler(bot: Bot):
    async def _handle_complete(request: web.Request) -> web.Response:
        p = dict(await request.post())
        if _complete_sign(p) != p.get("sign_string", ""):
            return _err(p, -1, "SIGN CHECK FAILED", confirm=True)

        kind, order = await _lookup_order(p.get("merchant_trans_id", ""))
        if not order:
            return _err(p, -5, "Order not found", confirm=True)

        # Click o'z tomonidan xato bildirsa (bekor qilingan)
        try:
            click_error = int(p.get("error", "0"))
        except ValueError:
            click_error = 0
        if click_error < 0:
            return _err(p, -9, "Transaction cancelled", confirm=True)

        if order.status == "paid":
            return _err(p, -4, "Already paid", confirm=True)

        click_trans_id = p.get("click_trans_id")
        if kind == "donation":
            await mark_donation_paid(order.id, click_trans_id)
            user = await get_user_by_id(order.user_id)
            if user:
                try:
                    await bot.send_message(
                        user.telegram_id,
                        "❤️ Qo'llab-quvvatlaganingiz uchun katta rahmat!\n"
                        f"Donat: <b>{order.amount:,} so'm</b>".replace(",", " "),
                        parse_mode="HTML",
                    )
                except Exception:
                    logger.warning("Donat xabarini yuborib bo'lmadi: %s", user.telegram_id)
        elif order.plan == "longvideo":
            # Uzun video (45+ daqiqa) — bitta martalik to'lov: obuna EMAS,
            # saqlangan meta bilan videoni to'g'ridan-to'g'ri navbatga qo'yamiz.
            await mark_payment_paid(order.id, click_trans_id)
            try:
                meta = json.loads(order.meta or "{}")
                from bot.handlers.video import submit_long_video_job

                await submit_long_video_job(bot, meta)
            except Exception:
                logger.exception("Uzun video ishga tushmadi (payment=%s)", order.id)
                user = await get_user_by_id(order.user_id)
                if user:
                    try:
                        await bot.send_message(
                            user.telegram_id,
                            "⚠️ To'lov qabul qilindi, lekin videoni navbatga "
                            "qo'yishda xatolik bo'ldi. Admin bilan bog'laning.",
                        )
                    except Exception:
                        pass
        else:
            # Obuna: to'lovni belgilash + tarifni faollashtirish
            await mark_payment_paid(order.id, click_trans_id)
            user = await get_user_by_id(order.user_id)
            if user:
                eff = await get_effective_settings()
                days = eff["sub_days"]
                await set_plan(user.telegram_id, order.plan, days)
                try:
                    await bot.send_message(
                        user.telegram_id,
                        f"✅ To'lov qabul qilindi! <b>{order.plan.upper()}</b> "
                        f"obunasi {days} kunga faollashtirildi.\n"
                        f"Tekshirish: /profile",
                        parse_mode="HTML",
                    )
                except Exception:
                    logger.warning("Obuna xabarini yuborib bo'lmadi: %s", user.telegram_id)

        return web.json_response(
            {
                "click_trans_id": p.get("click_trans_id", ""),
                "merchant_trans_id": p.get("merchant_trans_id", ""),
                "merchant_confirm_id": order.id,
                "error": 0,
                "error_note": "Success",
            }
        )

    return _handle_complete


def setup_click_routes(app: web.Application, bot: Bot) -> None:
    app.router.add_post("/click/prepare", _handle_prepare)
    app.router.add_post("/click/complete", make_complete_handler(bot))
