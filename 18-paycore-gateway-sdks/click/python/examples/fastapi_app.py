"""FastAPI loyihangizga ulash — to'liq ishlaydigan namuna.

Ishga tushirish (loyiha ildizidan):

    pip install -r requirements.txt
    cp .env.example .env          # va qiymatlarni to'ldiring
    uvicorn examples.fastapi_app:app --port 8000

Sinash:

    curl -X POST "http://localhost:8000/orders?product=Kitob&amount=5000"
    # javobdagi pay_url ni brauzerda oching
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from starlette.concurrency import run_in_threadpool

from click_payment import handle_complete, handle_prepare, payment_url
from click_payment import click_orders

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = FastAPI(title="Click to'lov namunasi")


# =============================================================================
#  CLICK ENDPOINT'LARI — loyihangizga aynan shu ikkitasini qo'shasiz
# =============================================================================
#
# Click kabinetiga shu manzillarni yozasiz:
#     Prepare URL:  https://sizning-domen.uz/click/prepare
#     Complete URL: https://sizning-domen.uz/click/complete


async def _request_data(request: Request) -> dict:
    """Click so'rovidan maydonlarni oladi.

    Click odatda form-encoded POST yuboradi, lekin JSON ham kelishi mumkin.
    """
    try:
        form = await request.form()
        if form:
            return dict(form)
    except Exception:
        pass

    try:
        body = await request.json()
        if isinstance(body, dict):
            return body
    except Exception:
        pass

    return dict(request.query_params)


@app.post("/click/prepare")
async def click_prepare(request: Request) -> dict:
    data = await _request_data(request)
    # handle_prepare sinxron (baza bilan ishlaydi) — event loop'ni
    # bloklamaslik uchun threadpool'da chaqiramiz.
    return await run_in_threadpool(handle_prepare, data)


@app.post("/click/complete")
async def click_complete(request: Request) -> dict:
    data = await _request_data(request)
    return await run_in_threadpool(handle_complete, data)


# =============================================================================
#  SIZNING ILOVANGIZ
# =============================================================================


@app.post("/orders")
def create_order(product: str, amount: int) -> dict:
    """Buyurtma yaratadi va Click to'lov havolasini qaytaradi."""
    # O'z tizimingizda buyurtma allaqachon bazangizda bo'ladi — siz faqat
    # unga unikal merchant_trans_id berasiz.
    order = click_orders.create_order(
        merchant_trans_id=f"ORD{_next_id()}",
        amount=amount,
        user_id=1,
        product=product,
    )

    return {
        "merchant_trans_id": order.merchant_trans_id,
        "amount": int(order.amount),
        "pay_url": payment_url(order.merchant_trans_id, order.amount),
    }


@app.get("/orders/{merchant_trans_id}")
def order_status(merchant_trans_id: str) -> dict:
    """To'lov holatini bazadan o'qiydi — frontend shu yerni so'rab turadi."""
    order = click_orders.find_order(merchant_trans_id)
    if order is None:
        return {"error": "topilmadi"}
    return {
        "merchant_trans_id": order.merchant_trans_id,
        "status": order.status,
        "amount": int(order.amount),
    }


_counter = 0


def _next_id() -> int:
    """Namuna uchun oddiy hisoblagich (haqiqiy loyihada buyurtma id'si bo'ladi)."""
    global _counter
    _counter += 1
    return _counter
