"""Click (my.click.uz) to'lov integratsiyasi.

Ishlatish:

    from click_payment import payment_url, handle_prepare, handle_complete

    # 1) To'lov havolasi
    url = payment_url("ORD42", 5000)

    # 2) Endpoint'laringizda
    handle_prepare(request_data)    # -> dict, JSON qilib qaytaring
    handle_complete(request_data)   # -> dict, JSON qilib qaytaring

Bazangizga ulanish `click_orders.py` da — faqat shu faylni tahrirlaysiz.
"""

from .click_complete import handle_complete
from .click_config import ClickConfig, ConfigError, get_config, payment_url, set_config
from .click_orders import (
    STATUS_CANCELLED,
    STATUS_PAID,
    STATUS_PENDING,
    Order,
)
from .click_prepare import handle_prepare

__version__ = "1.0.0"

__all__ = [
    "payment_url",
    "handle_prepare",
    "handle_complete",
    "Order",
    "STATUS_PENDING",
    "STATUS_PAID",
    "STATUS_CANCELLED",
    "ClickConfig",
    "ConfigError",
    "get_config",
    "set_config",
]
