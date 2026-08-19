"""Click to'lov — URL generatsiya va imzo (sign) tekshirish.

Ko'prik (myxvest PHP) BITTA Click xizmatini bir nechta bot uchun ulashadi.
merchant_trans_id prefiks orqali bot aniqlanadi:
    MUST<payment_id>   — buyurtma yoki balans to'lovi (shu botniki)
Bot o'z tomonida md5 sign_string ni qayta tekshiradi (subtitr bilan bir xil
secret_key, lekin har bot o'z bazasini yangilaydi).
"""
from __future__ import annotations
import hashlib
from config import settings


def merchant_id(payment_id: int) -> str:
    """Payment id dan Click merchant_trans_id yasaydi: MUST<id>."""
    return f"{settings.click_tx_prefix}{payment_id}"


def make_click_url(merchant_trans_id: str, amount: int) -> str:
    """Click to'lov havolasini yaratadi."""
    base = "https://my.click.uz/services/pay"
    params = (
        f"?service_id={settings.click_service_id}"
        f"&merchant_id={settings.click_merchant_id}"
        f"&merchant_user_id={settings.click_merchant_user_id}"
        f"&amount={amount}"
        f"&transaction_param={merchant_trans_id}"
        f"&return_url={settings.click_return_url}"
    )
    return base + params


def _md5(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def prepare_sign(p: dict) -> str:
    return _md5(
        f"{p.get('click_trans_id','')}{p.get('service_id','')}"
        f"{settings.click_secret_key}{p.get('merchant_trans_id','')}"
        f"{p.get('amount','')}{p.get('action','')}{p.get('sign_time','')}"
    )


def complete_sign(p: dict) -> str:
    return _md5(
        f"{p.get('click_trans_id','')}{p.get('service_id','')}"
        f"{settings.click_secret_key}{p.get('merchant_trans_id','')}"
        f"{p.get('merchant_prepare_id','')}{p.get('amount','')}"
        f"{p.get('action','')}{p.get('sign_time','')}"
    )


def parse_payment_id(mtid: str) -> int | None:
    """MUST<id> dan payment id ni chiqaradi."""
    mtid = (mtid or "").strip()
    prefix = settings.click_tx_prefix
    if mtid.startswith(prefix):
        digits = mtid[len(prefix):]
        return int(digits) if digits.isdigit() else None
    return None
