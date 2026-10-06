"""To'liq ishlaydigan namuna: FastAPI + Uzum Bank.

Ishga tushirish:

    pip install -r requirements.txt
    cp .env.example .env          # va qiymatlarni to'ldiring
    uvicorn examples.quickstart_fastapi:app --reload --port 8000

Uzum Bank kabinetiga yoziladigan bazaviy callback manzil:

    https://sizning-domen.uz/uzum

(Uzum Bank shu manzilga /check, /create, /confirm, /reverse, /status
qo'shib chaqiradi.)

DIQQAT: Uzum Bank'da Click/Payme'dagidek "to'lov havolasi" YO'Q.
Foydalanuvchi Uzum Bank ilovasida xizmatingizni `service_id` orqali qidirib
topadi va to'lovni O'SHA YERDA boshlaydi — sizning saytingizdan emas.
"""

from __future__ import annotations

import logging
import os

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from uzum_payment import UzumTransaction, get_config
from uzum_payment.uzum_methods import (
    handle_check,
    handle_confirm,
    handle_create,
    handle_reverse,
    handle_status,
)
from uzum_payment.uzum_orders import demo_create_order

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(title="Uzum Bank to'lov namunasi")


async def _read_json(request: Request) -> dict:
    try:
        return await request.json()
    except Exception:
        return {}


@app.post("/uzum/check")
async def uzum_check(request: Request):
    status_code, body = handle_check(await _read_json(request), request.headers.get("authorization"))
    return JSONResponse(body, status_code=status_code)


@app.post("/uzum/create")
async def uzum_create(request: Request):
    status_code, body = handle_create(await _read_json(request), request.headers.get("authorization"))
    return JSONResponse(body, status_code=status_code)


@app.post("/uzum/confirm")
async def uzum_confirm(request: Request):
    status_code, body = handle_confirm(await _read_json(request), request.headers.get("authorization"))
    return JSONResponse(body, status_code=status_code)


@app.post("/uzum/reverse")
async def uzum_reverse(request: Request):
    status_code, body = handle_reverse(await _read_json(request), request.headers.get("authorization"))
    return JSONResponse(body, status_code=status_code)


@app.post("/uzum/status")
async def uzum_status(request: Request):
    status_code, body = handle_status(await _read_json(request), request.headers.get("authorization"))
    return JSONResponse(body, status_code=status_code)


@app.post("/orders")
def create_order(product: str, amount_som: int) -> dict:
    """Namuna: buyurtma yaratadi (Uzum Bank ilovasida shu `account` bilan topiladi)."""
    order_id = "1"  # namuna uchun; siz o'z bazangizdan olasiz
    demo_create_order(order_id, amount_som * 100, product)

    return {
        "order_id": order_id,
        "amount_tiyin": amount_som * 100,
        "service_id": get_config().service_id,
        "eslatma": (
            "Foydalanuvchi Uzum Bank ilovasida xizmatingizni service_id orqali "
            f"topadi va 'account' maydoniga {order_id} kiritadi."
        ),
    }
