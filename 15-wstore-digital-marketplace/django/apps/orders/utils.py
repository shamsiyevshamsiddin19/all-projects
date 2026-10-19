import secrets
import hmac
import re
import urllib.parse
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
            return json.loads(request.body.decode("utf-8"))
    except Exception:
        pass
    return {}

def check_click_auth(data, action):
    """
    Validates either direct Click MD5 signature (sign_string) or bridge secret.
    """
    # 1. Direct Click MD5 signature check
    sign_string = data.get("sign_string")
    if sign_string:
        click_trans_id = data.get("click_trans_id", "")
        service_id = data.get("service_id", getattr(settings, "CLICK_SERVICE_ID", "99657"))
        secret_key = os.getenv("CLICK_SECRET_KEY", getattr(settings, "CLICK_BRIDGE_SECRET", "wstore_secret_bridge_key"))
        merchant_trans_id = data.get("merchant_trans_id", "")
        amount = data.get("amount", "")
        sign_time = data.get("sign_time", "")

        # Format amount as clean string if float
        try:
            amount_str = f"{float(amount):.2f}".rstrip("0").rstrip(".") if "." in str(amount) else str(amount)
        except (ValueError, TypeError):
            amount_str = str(amount)

        raw_str = f"{click_trans_id}{service_id}{secret_key}{merchant_trans_id}{amount_str}{action}{sign_time}"
        calc_sign = hashlib.md5(raw_str.encode("utf-8")).hexdigest()

        # Also try raw amount without decimal formatting
        raw_str_alt = f"{click_trans_id}{service_id}{secret_key}{merchant_trans_id}{amount}{action}{sign_time}"
        calc_sign_alt = hashlib.md5(raw_str_alt.encode("utf-8")).hexdigest()

        if sign_string.lower() in (calc_sign.lower(), calc_sign_alt.lower()):
            return True

    # 2. Bridge secret fallback
    received_secret = data.get("secret")
    expected_secret = getattr(settings, "CLICK_BRIDGE_SECRET", "wstore_secret_bridge_key")
    if received_secret and expected_secret:
        return hmac.compare_digest(str(received_secret), str(expected_secret))

    return False

def check_bridge_secret(received_secret):
    expected_secret = getattr(settings, "CLICK_BRIDGE_SECRET", "wstore_secret_bridge_key")
    if not received_secret or not expected_secret:
        return False
    return hmac.compare_digest(str(received_secret), str(expected_secret))

def amounts_match(a, b):
    try:
        x = float(a)
        y = float(b)
        return abs(x - y) < 0.01
    except (TypeError, ValueError):
        return False
