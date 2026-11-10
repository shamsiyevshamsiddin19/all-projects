"""ErrorLog modeliga yozish uchun yordamchi."""

import logging
import re
import traceback

logger = logging.getLogger(__name__)

_SENSITIVE_ASSIGNMENT = re.compile(
    r"(?i)\b(secret|token|password|authorization|api[_-]?key|card[_-]?number)"
    r"\s*([=:])\s*([^\s,;&\[]+)"
)
_CARD_NUMBER = re.compile(r"(?<!\d)(?:\d[ -]?){15}\d(?!\d)")


def redact_sensitive(value: object) -> str:
    """Logga ketishi mumkin bo'lgan token va karta raqamlarini maskalaydi."""
    text = str(value)
    text = _CARD_NUMBER.sub("[CARD-REDACTED]", text)
    return _SENSITIVE_ASSIGNMENT.sub(r"\1\2[REDACTED]", text)


def log_error(exc, context=""):
    """
    Xatolikni `ErrorLog` jadvaliga yozadi.

    Model va admin paneli mavjud edi, lekin hech qayerdan chaqirilmagani
    uchun jadval doim bo'sh qolardi — ya'ni to'lov webhook'idagi xatolar
    izsiz yo'qolardi. Yozishning o'zi ham yiqilmasligi kerak, shuning uchun
    hamma narsa try ichida.
    """
    from .models import ErrorLog

    try:
        ErrorLog.objects.create(
            message=(redact_sensitive(exc) or exc.__class__.__name__)[:2000],
            stack=redact_sensitive(
                "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
            )[:10000],
            context=redact_sensitive(context)[:255],
        )
    except Exception:
        logger.exception("ErrorLog yozishning o'zi muvaffaqiyatsiz tugadi")
