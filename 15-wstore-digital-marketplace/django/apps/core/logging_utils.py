"""ErrorLog modeliga yozish uchun yordamchi."""
import logging
import traceback

logger = logging.getLogger(__name__)


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
            message=str(exc)[:2000] or exc.__class__.__name__,
            stack="".join(
                traceback.format_exception(type(exc), exc, exc.__traceback__)
            )[:10000],
            context=str(context)[:255],
        )
    except Exception:
        logger.exception("ErrorLog yozishning o'zi muvaffaqiyatsiz tugadi")
