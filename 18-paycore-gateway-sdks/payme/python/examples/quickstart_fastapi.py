"""To'liq ishlaydigan namuna: FastAPI + Payme.

Payme'da Click'dagidek ikkita endpoint (prepare/complete) emas — BITTA
endpoint bor. Payme "method" maydoniga qarab qaysi amalni bajarishni
o'zi aytadi (CheckPerformTransaction, CreateTransaction va h.k.).

Ishga tushirish:

    pip install -r requirements.txt
    cp .env.example .env          # va qiymatlarni to'ldiring
    uvicorn examples.quickstart_fastapi:app --reload --port 8000

Sinash:

    curl -X POST "http://localhost:8000/orders?product=Kitob&amount=5000"
    # javobdagi `pay_url` ni brauzerda ochasiz
"""

from __future__ import annotations

import logging
import os

from fastapi import FastAPI, Header, Request
from fastapi.responses import HTMLResponse

from payme_payment import checkout_url, handle_request, som_to_tiyin
from payme_payment import payme_orders as orders

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(title="Payme to'lov namunasi")


@app.post("/payme")
async def payme_webhook(
    request: Request,
    authorization: str | None = Header(default=None),
) -> dict:
    """Payme kabinetiga yoziladigan YAGONA manzil.

    Payme "method" maydoniga qarab CheckPerformTransaction, CreateTransaction,
    PerformTransaction, CancelTransaction, CheckTransaction yoki GetStatement
    so'raydi — hammasi shu bitta endpoint orqali keladi.
    """
    body = await request.json()
    return handle_request(body, authorization)


@app.post("/orders")
def create_order(product: str, amount: int) -> dict:
    """Buyurtma yaratadi va Payme to'lov havolasini qaytaradi."""
    order_id = f"ORD{__import__('time').time_ns()}"
    orders.demo_create_order(order_id, som_to_tiyin(amount), product)

    return {
        "order_id": order_id,
        "amount": amount,
        "pay_url": checkout_url({"order_id": order_id}, som_to_tiyin(amount)),
    }


@app.get("/orders/{order_id}")
def order_status(order_id: str) -> dict:
    """Buyurtma holatini tekshirish."""
    account = orders.find_account({"order_id": order_id})
    if account is None:
        return {"error": "topilmadi"}
    return {
        "order_id": order_id,
        "payable": account.payable,
        "amount_tiyin": account.amount,
    }


@app.get("/payment/result", response_class=HTMLResponse)
def payment_result() -> str:
    """Payme'dan qaytgan foydalanuvchi tushadigan sahifa (return_url).

    DIQQAT: bu sahifaga tushish to'lov o'tganini BILDIRMAYDI. Haqiqiy
    holatni yuqoridagi /orders/{order_id} dan (ya'ni bazadan) o'qing.
    """
    return """
    <h2>Rahmat!</h2>
    <p>To'lov holati tekshirilmoqda. Bir necha soniyada yangilanadi.</p>
    """
