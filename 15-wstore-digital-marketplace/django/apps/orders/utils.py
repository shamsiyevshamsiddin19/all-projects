import secrets
import hmac
import re
import urllib.parse
from decimal import Decimal, InvalidOperation
from django.conf import settings

CLICK_PREFIX_PURCHASE = "WSTP"
CLICK_PREFIX_LISTING = "WSTL"

def generate_secure_download_token():
    return secrets.token_hex(24)

def amount_after_commission(amount_som):
    pct = getattr(settings, "PLATFORM_COMMISSION_PERCENT", 0)
    return round(float(amount_som) * (1 - pct / 100))

def parse_click_transaction_id(merchant_trans_id):
    """
    Extracts numerical transaction ID from 'WSTP42' or 'WSTL7'.
    """
    m = re.match(r"^(WSTP|WSTL)(\d+)$", str(merchant_trans_id or ""))
    if not m:
        return 0
    return int(m.group(2))

def build_click_payment_url(merchant_trans_id, amount_som, return_url):
    params = {
        "service_id": getattr(settings, "CLICK_SERVICE_ID", "99657"),
        "merchant_id": getattr(settings, "CLICK_MERCHANT_ID", "59136"),
        "amount": str(round(float(amount_som))),
        "transaction_param": str(merchant_trans_id),
        "merchant_user_id": getattr(settings, "CLICK_MERCHANT_USER_ID", "81435"),
        "return_url": return_url,
    }
    base_url = getattr(settings, "CLICK_BASE_URL", "https://my.click.uz/services/pay")
    return f"{base_url}?{urllib.parse.urlencode(params)}"

import hashlib
import json
import os

def extract_click_payload(request):
    """Extract parameters from either POST form or JSON body."""
    if request.POST:
        return request.POST.dict()
    try:
        if request.body:
            data = json.loads(request.body.decode("utf-8"))
            if isinstance(data, dict) and all(
                isinstance(value, (str, int, float, type(None))) for value in data.values()
            ):
                return data
    except Exception:
        pass
    return {}

def check_click_auth(data, action):
    """
    Validates either direct Click MD5 signature (sign_string) or bridge secret.
    """
    if not isinstance(data, dict):
        return False
    # Imzo mavjud bo'lsa noto'g'ri imzoni ko'prik kaliti bilan chetlab o'tib bo'lmaydi.
    sign_string = data.get("sign_string")
    if sign_string:
        secret_key = getattr(settings, "CLICK_SECRET_KEY", "")
        if not _usable_secret(secret_key):
            return False
        if str(data.get("service_id")) != str(settings.CLICK_SERVICE_ID):
            return False
        if str(data.get("action")) != str(action):
            return False
        if not isinstance(sign_string, str) or len(sign_string) != 32:
            return False
        click_trans_id = data.get("click_trans_id", "")
        service_id = data.get("service_id", "")
        merchant_trans_id = data.get("merchant_trans_id", "")
        amount = data.get("amount", "")
        sign_time = data.get("sign_time", "")
        prepare_id = data.get("merchant_prepare_id", "") if action == 1 else ""
        if not click_trans_id or not merchant_trans_id or not sign_time or (action == 1 and not prepare_id):
            return False
        raw_str = f"{click_trans_id}{service_id}{secret_key}{merchant_trans_id}{prepare_id}{amount}{action}{sign_time}"
        calc_sign = hashlib.md5(raw_str.encode("utf-8")).hexdigest()
        return hmac.compare_digest(sign_string.lower(), calc_sign)

    # 2. Bridge secret fallback
    received_secret = data.get("secret")
    return check_bridge_secret(received_secret)


def _usable_secret(secret):
    return bool(secret) and secret != "wstore_secret_bridge_key"


def payments_configured():
    return bool(settings.CLICK_SERVICE_ID and settings.CLICK_MERCHANT_ID) and (
        _usable_secret(getattr(settings, "CLICK_SECRET_KEY", ""))
        or _usable_secret(getattr(settings, "CLICK_BRIDGE_SECRET", ""))
    )

def check_bridge_secret(received_secret):
    expected_secret = getattr(settings, "CLICK_BRIDGE_SECRET", "")
    if not isinstance(received_secret, str) or not _usable_secret(expected_secret):
        return False
    return hmac.compare_digest(str(received_secret), str(expected_secret))

def amounts_match(a, b):
    try:
        x = Decimal(str(a))
        y = Decimal(str(b))
        return x.is_finite() and y.is_finite() and x == y
    except (TypeError, ValueError, InvalidOperation):
        return False
