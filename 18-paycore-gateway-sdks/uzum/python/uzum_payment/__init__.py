"""Uzum Bank Merchant API integratsiyasi.

Click/Payme'dan farqli — Uzum Bank'da to'lov havolasi (checkout URL) YO'Q.
Foydalanuvchi Uzum Bank ilovasida xizmatingizni `service_id` orqali topadi
va TO'LOVNI O'SHA YERDA BOSHLAYDI. Sizning serveringiz faqat 5 ta webhook'ni
qabul qiladi:

    from uzum_payment import handle_check, handle_create, handle_confirm, \\
        handle_reverse, handle_status

    status_code, body = handle_check(request_data, auth_header)
    # status_code (200 yoki 400) va body (dict) ni JSON qilib qaytaring

Bazangizga ulanish `uzum_orders.py` da — faqat shu faylni tahrirlaysiz.
"""

from .uzum_config import ConfigError, UzumConfig, get_config, set_config
from .uzum_errors import UzumError
from .uzum_methods import (
    handle_check,
    handle_confirm,
    handle_create,
    handle_reverse,
    handle_status,
)
from .uzum_orders import (
    STATE_CONFIRMED,
    STATE_CREATED,
    STATE_REVERSED,
    UzumAccount,
    UzumTransaction,
)

__version__ = "1.0.0"

__all__ = [
    "UzumConfig",
    "ConfigError",
    "get_config",
    "set_config",
    "UzumError",
    "handle_check",
    "handle_create",
    "handle_confirm",
    "handle_reverse",
    "handle_status",
    "UzumAccount",
    "UzumTransaction",
    "STATE_CREATED",
    "STATE_CONFIRMED",
    "STATE_REVERSED",
]
