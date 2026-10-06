"""Uzum Bank Merchant API xato kodlari.

Bu kodlarni Uzum Bank belgilagan (rasmiy hujjat: developer.uzumbank.uz,
"Коды ошибок" bo'limi) — o'zgartirmang.

MUHIM: Uzum'da xato kodi SATR sifatida yuboriladi ("10007", raqam emas) va
javob HTTP 400 bilan qaytariladi (Click/Payme'da esa har doim HTTP 200).
"""

from __future__ import annotations


class UzumError(RuntimeError):
    """Uzum'ga HTTP 400 + JSON bilan qaytariladigan xato."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message

    def to_dict(self) -> dict:
        return {"errorCode": self.code}


# --- Umumiy xatolar (barcha webhook'larda) -----------------------------------

def access_denied() -> UzumError:
    return UzumError("10001", "Access denied")


def json_parse_error() -> UzumError:
    return UzumError("10002", "JSON parsing error")


def invalid_operation() -> UzumError:
    return UzumError("10003", "Invalid operation (method must be POST)")


def required_field_missing() -> UzumError:
    return UzumError("10005", "Required parameter is missing")


# --- /check va /create uchun ---------------------------------------------

def invalid_service_id() -> UzumError:
    return UzumError("10006", "Invalid serviceId")


def account_not_found() -> UzumError:
    return UzumError("10007", "Additional payment attribute not found")


def already_paid() -> UzumError:
    return UzumError("10008", "Payment already paid")


def already_cancelled() -> UzumError:
    return UzumError("10009", "Payment cancelled")


# --- /create uchun ---------------------------------------------------------

def transaction_already_created() -> UzumError:
    """Shu `transId` bilan tranzaksiya allaqachon yaratilgan.

    DIQQAT: bu Click/Payme'dagidek "idempotent — bir xil natijani qaytar"
    emas — Uzum hujjati aniq shunday deydi: "Верните этот код при повторном
    создании транзакции с тем же transId" (takroriy /create so'rovida shu
    xatoni qaytaring).
    """
    return UzumError("10010", "Transaction with this transId already created")


def invalid_amount() -> UzumError:
    return UzumError("10011", "Invalid amount")


def amount_too_low() -> UzumError:
    return UzumError("10012", "Amount is below the minimum")


def amount_too_high() -> UzumError:
    return UzumError("10013", "Amount is above the maximum")


# --- /confirm, /reverse, /status uchun --------------------------------------

def transaction_not_found() -> UzumError:
    return UzumError("10014", "Transaction not found")


def transaction_cancelled() -> UzumError:
    """Bekor qilingan tranzaksiyani tasdiqlab (confirm) bo'lmaydi."""
    return UzumError("10015", "Transaction is cancelled")


def transaction_already_confirmed() -> UzumError:
    """Takroriy /confirm so'rovi — Uzum hujjati bo'yicha bu ham XATO,
    idempotent muvaffaqiyat emas (10010 bilan bir xil mantiq)."""
    return UzumError("10016", "Transaction already confirmed")


def unable_to_cancel() -> UzumError:
    return UzumError("10017", "Unable to cancel transaction in current state")


def transaction_already_cancelled() -> UzumError:
    """Takroriy /reverse so'rovi — xato qaytariladi (idempotent emas)."""
    return UzumError("10018", "Transaction already cancelled")


# --- Ichki xato ---------------------------------------------------------

def internal_error() -> UzumError:
    return UzumError("99999", "Internal server error")
