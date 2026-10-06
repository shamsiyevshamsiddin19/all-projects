"""Flask uchun tayyor Payme endpointi.

Ishlatish:

    from flask import Flask
    from examples.flask_app import app

Yoki o'z loyihangizga shu blueprint'ni qo'shing:

    from payme_payment import handle_request
    from flask import Flask, request, jsonify

    app = Flask(__name__)

    @app.post("/payme")
    def payme_webhook():
        return jsonify(handle_request(request.get_json(), request.headers.get("Authorization")))
"""

from __future__ import annotations

from flask import Flask, jsonify, request

from payme_payment import checkout_url, handle_request, som_to_tiyin
from payme_payment import payme_orders as orders

app = Flask(__name__)


@app.post("/payme")
def payme_webhook():
    body = request.get_json(silent=True) or {}
    auth = request.headers.get("Authorization")
    return jsonify(handle_request(body, auth))


@app.post("/orders")
def create_order():
    import time

    product = request.args.get("product", "Mahsulot")
    amount = int(request.args.get("amount", 5000))
    order_id = f"ORD{time.time_ns()}"

    orders.demo_create_order(order_id, som_to_tiyin(amount), product)

    return jsonify(
        {
            "order_id": order_id,
            "amount": amount,
            "pay_url": checkout_url({"order_id": order_id}, som_to_tiyin(amount)),
        }
    )


@app.get("/orders/<order_id>")
def order_status(order_id: str):
    account = orders.find_account({"order_id": order_id})
    if account is None:
        return jsonify({"error": "topilmadi"}), 404
    return jsonify(
        {"order_id": order_id, "payable": account.payable, "amount_tiyin": account.amount}
    )


if __name__ == "__main__":
    app.run(port=8000, debug=True)
