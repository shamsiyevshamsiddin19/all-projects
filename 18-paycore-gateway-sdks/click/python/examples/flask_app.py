"""Flask loyihangizga ulash — to'liq ishlaydigan namuna.

Ishga tushirish:

    pip install flask python-dotenv
    cp .env.example .env
    python -m examples.flask_app
"""

from __future__ import annotations

import logging

from flask import Flask, jsonify, request

from click_payment import handle_complete, handle_prepare, payment_url
from click_payment import click_orders

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = Flask(__name__)


# =============================================================================
#  CLICK ENDPOINT'LARI — loyihangizga aynan shu ikkitasini qo'shasiz
# =============================================================================


def _request_data() -> dict:
    """Click so'rovidan maydonlarni oladi (form -> JSON -> query)."""
    if request.form:
        return request.form.to_dict()

    body = request.get_json(silent=True)
    if isinstance(body, dict):
        return body

    return request.args.to_dict()


@app.post("/click/prepare")
def click_prepare():
    return jsonify(handle_prepare(_request_data()))


@app.post("/click/complete")
def click_complete():
    return jsonify(handle_complete(_request_data()))


# =============================================================================
#  SIZNING ILOVANGIZ
# =============================================================================


@app.post("/orders")
def create_order():
    product = request.args.get("product", "Mahsulot")
    amount = int(request.args.get("amount", 5000))

    order = click_orders.create_order(
        merchant_trans_id=f"ORD{_next_id()}",
        amount=amount,
        user_id=1,
        product=product,
    )

    return jsonify(
        {
            "merchant_trans_id": order.merchant_trans_id,
            "amount": int(order.amount),
            "pay_url": payment_url(order.merchant_trans_id, order.amount),
        }
    )


@app.get("/orders/<merchant_trans_id>")
def order_status(merchant_trans_id: str):
    order = click_orders.find_order(merchant_trans_id)
    if order is None:
        return jsonify({"error": "topilmadi"}), 404
    return jsonify(
        {
            "merchant_trans_id": order.merchant_trans_id,
            "status": order.status,
            "amount": int(order.amount),
        }
    )


_counter = 0


def _next_id() -> int:
    global _counter
    _counter += 1
    return _counter


if __name__ == "__main__":
    app.run(port=8000, debug=True)
