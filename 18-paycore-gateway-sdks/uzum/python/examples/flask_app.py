"""Flask loyihangizga ulash — to'liq ishlaydigan namuna.

Ishga tushirish:

    pip install flask python-dotenv
    cp .env.example .env
    python -m examples.flask_app
"""

from __future__ import annotations

import logging

from flask import Flask, jsonify, request

from uzum_payment.uzum_methods import (
    handle_check,
    handle_confirm,
    handle_create,
    handle_reverse,
    handle_status,
)

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = Flask(__name__)


def _dispatch(handler):
    data = request.get_json(silent=True) or {}
    status_code, body = handler(data, request.headers.get("Authorization"))
    return jsonify(body), status_code


@app.post("/uzum/check")
def uzum_check():
    return _dispatch(handle_check)


@app.post("/uzum/create")
def uzum_create():
    return _dispatch(handle_create)


@app.post("/uzum/confirm")
def uzum_confirm():
    return _dispatch(handle_confirm)


@app.post("/uzum/reverse")
def uzum_reverse():
    return _dispatch(handle_reverse)


@app.post("/uzum/status")
def uzum_status():
    return _dispatch(handle_status)


if __name__ == "__main__":
    app.run(port=8000, debug=True)
