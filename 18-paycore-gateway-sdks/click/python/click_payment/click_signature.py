"""Click imzosi (sign_string) — qurish va tekshirish.

Click har bir so'rovni md5 imzo bilan yuboradi. Formula prepare va complete'da
ozgina farq qiladi:

    prepare  (action=0):
        md5(click_trans_id + service_id + secret_key + merchant_trans_id
            + amount + action + sign_time)

    complete (action=1):
        md5(click_trans_id + service_id + secret_key + merchant_trans_id
            + merchant_prepare_id + amount + action + sign_time)

Yagona farq — complete'da merchant_trans_id bilan amount orasiga
merchant_prepare_id qo'shiladi.

Bu faylga tegishingiz shart emas.
"""

from __future__ import annotations

import hashlib
import hmac
from typing import Any, Mapping

ACTION_PREPARE = "0"
ACTION_COMPLETE = "1"


def build_sign_string(
    *,
    click_trans_id: str,
    service_id: str,
    secret_key: str,
    merchant_trans_id: str,
    amount: str,
    action: str,
    sign_time: str,
    merchant_prepare_id: str = "",
) -> str:
    """Imzolanadigan xom satrni yig'adi (hali md5 qilinmagan)."""
    parts = [
        str(click_trans_id),
        str(service_id),
        str(secret_key),
        str(merchant_trans_id),
    ]

    if str(action) == ACTION_COMPLETE:
        parts.append(str(merchant_prepare_id))

    parts.append(str(amount))
    parts.append(str(action))
    parts.append(str(sign_time))

    return "".join(parts)


def make_sign(**kwargs: str) -> str:
    """sign_string ni hisoblaydi (md5, kichik harfli hex)."""
    return hashlib.md5(build_sign_string(**kwargs).encode("utf-8")).hexdigest()


def signs_equal(received: str, expected: str) -> bool:
    """Ikki imzoni vaqt bo'yicha barqaror (timing-safe) solishtiradi.

    Oddiy `==` imzoni belgima-belgi topib olish hujumiga yo'l ochadi.
    """
    received = str(received or "").strip().lower()
    expected = str(expected or "").strip().lower()
    if not received or not expected:
        return False
    return hmac.compare_digest(received, expected)


def check_sign(data: Mapping[str, Any], action: str, config) -> bool:
    """Click so'rovining imzosini tekshiradi.

    `action` SO'ROVDAN OLINMAYDI — qaysi endpoint chaqirilgan bo'lsa,
    o'shanikini ("0" yoki "1") beramiz. Aks holda hujumchi prepare uchun
    olingan imzoni complete so'roviga qo'yib yuborishi mumkin bo'lardi.

    MUHIM: `amount` imzoga Click YUBORGAN XOM SATR holida kiradi. Click
    "5000.00" yuborsa, uni float'ga o'girib qaytadan satrga aylantirsangiz
    "5000.0" bo'lib qoladi va imzo mos kelmaydi. Shuning uchun bu yerda
    qiymatlar o'zgartirilmasdan uzatiladi.
    """
    service_id = str(data.get("service_id", ""))
    if not service_id or not signs_equal(service_id, config.service_id):
        return False

    expected = make_sign(
        click_trans_id=str(data.get("click_trans_id", "")),
        service_id=service_id,
        secret_key=config.secret_key,
        merchant_trans_id=str(data.get("merchant_trans_id", "")),
        amount=str(data.get("amount", "")),
        action=action,
        sign_time=str(data.get("sign_time", "")),
        merchant_prepare_id=str(data.get("merchant_prepare_id", "")),
    )
    return signs_equal(str(data.get("sign_string", "")), expected)
