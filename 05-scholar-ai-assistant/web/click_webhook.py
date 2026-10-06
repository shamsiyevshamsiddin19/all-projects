"""Click to'lov webhook — Prepare + Complete (myxvest ko'prigi orqali).

Click ikki marta murojaat qiladi:
  action=0 (Prepare)  — to'lovni tasdiqlaymiz (payment mavjudligini tekshiramiz)
  action=1 (Complete) — to'lov yakunlanadi → buyurtma generatsiyasi / balans

Har so'rovda md5 sign_string tekshiriladi (subtitr bilan bir xil pattern).
merchant_trans_id = MUST<payment_id>.
"""
from __future__ import annotations
import asyncio
import logging
from aiohttp import web
from payment.click import prepare_sign, complete_sign, parse_payment_id
from db.crud import get_payment, mark_payment_paid, update_balance, get_order, set_order_status
from config import settings

logger = logging.getLogger(__name__)


def _err(p: dict, code: int, note: str, confirm: bool = False) -> web.Response:
    body = {
        "click_trans_id": p.get("click_trans_id", ""),
        "merchant_trans_id": p.get("merchant_trans_id", ""),
        "error": code,
        "error_note": note,
    }
    if confirm:
        body["merchant_confirm_id"] = p.get("merchant_prepare_id", 0) or 0
    else:
        body["merchant_prepare_id"] = 0
    return web.json_response(body)


async def _click_prepare(request: web.Request) -> web.Response:
    p = dict(await request.post())
    if prepare_sign(p) != p.get("sign_string", ""):
        return _err(p, -1, "SIGN CHECK FAILED")

    pid = parse_payment_id(p.get("merchant_trans_id", ""))
    payment = await get_payment(pid) if pid else None
    if not payment:
        return _err(p, -5, "Order not found")
    if payment.status == "paid":
        return _err(p, -4, "Already paid")
    try:
        if abs(float(p.get("amount", "0")) - float(payment.amount)) > 0.01:
            return _err(p, -2, "Incorrect amount")
    except ValueError:
        return _err(p, -2, "Incorrect amount")

    return web.json_response({
        "click_trans_id": p.get("click_trans_id", ""),
        "merchant_trans_id": p.get("merchant_trans_id", ""),
        "merchant_prepare_id": payment.id,
        "error": 0,
        "error_note": "Success",
    })


async def _click_complete(request: web.Request) -> web.Response:
    p = dict(await request.post())
    if complete_sign(p) != p.get("sign_string", ""):
        return _err(p, -1, "SIGN CHECK FAILED", confirm=True)

    pid = parse_payment_id(p.get("merchant_trans_id", ""))
    payment = await get_payment(pid) if pid else None
    if not payment:
        return _err(p, -5, "Order not found", confirm=True)

    try:
        click_error = int(p.get("error", "0"))
    except ValueError:
        click_error = 0
    if click_error < 0:
        return _err(p, -9, "Transaction cancelled", confirm=True)

    if payment.status == "paid":
        return _err(p, -4, "Already paid", confirm=True)

    click_trans_id = p.get("click_trans_id", "")
    await mark_payment_paid(payment.id, click_trans_id)

    # To'lov muvaffaqiyatli — keyingi ishlarni fonda bajaramiz
    asyncio.create_task(_post_payment(request.app, payment.id))

    return web.json_response({
        "click_trans_id": click_trans_id,
        "merchant_trans_id": p.get("merchant_trans_id", ""),
        "merchant_confirm_id": payment.id,
        "error": 0,
        "error_note": "Success",
    })


async def _post_payment(app, payment_id: int):
    """To'lov tasdiqlangach: buyurtma generatsiyasi yoki balans to'ldirish."""
    bot = app.get("bot")
    if not bot:
        return
    payment = await get_payment(payment_id)
    if not payment:
        return

    # Balans to'ldirish (order_id yo'q)
    if not payment.order_id:
        await update_balance(payment.user_id, payment.amount)
        try:
            await bot.send_message(
                payment.user_id,
                f"✅ <b>Hisobingiz to'ldirildi!</b>\n"
                f"💰 <b>+{payment.amount:,} so'm</b> balansingizga qo'shildi.",
                parse_mode="HTML",
            )
        except Exception:
            pass
        from services.notifications import notify_topup
        await notify_topup(bot, payment.user_id, payment.amount)
        return

    # Buyurtma to'lovi
    order = await get_order(payment.order_id)
    if not order or order.status not in ("pending",):
        return
    await set_order_status(order.id, "generating")
    try:
        await bot.send_message(
            payment.user_id,
            "✅ <b>To'lov qabul qilindi!</b>",
            parse_mode="HTML",
        )
    except Exception:
        pass

    # Adminga xabarnoma (Click orqali to'langan buyurtma)
    from db.crud import get_user
    from services.notifications import notify_new_order
    u = await get_user(payment.user_id)
    await notify_new_order(bot, u or _FakeUser(payment.user_id), order.doc_type,
                           order.topic, order.page_count, order.price, "Click")

    data = {
        "doc_type": order.doc_type,
        "topic": order.topic,
        "details": order.details or {},
        "language": order.language,
        "page_count": order.page_count,
        "file_format": order.file_format or "docx",
    }
    from bot.handlers.order import _generate_and_send
    asyncio.create_task(_generate_and_send(bot, payment.user_id, order.id, data))


class _FakeUser:
    """get_user None qaytarsa — minimal obyekt (notify uchun)."""
    def __init__(self, uid: int):
        self.id = uid
        self.username = None


def setup_click_routes(app: web.Application) -> None:
    app.router.add_post("/mustaqil/click/prepare", _click_prepare)
    app.router.add_post("/mustaqil/click/complete", _click_complete)
