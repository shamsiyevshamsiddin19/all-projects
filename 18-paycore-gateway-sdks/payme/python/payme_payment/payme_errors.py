"""Payme JSON-RPC xato kodlari.

Bu kodlarni Payme belgilagan — o'zgartirmang. Manba: rasmiy hujjat
(developer.help.paycom.uz) va Payme ekotizimidagi ko'plab implementatsiyalar
bir xil qiymatlarni ishlatadi.
"""

from __future__ import annotations


class PaymeError(RuntimeError):
    """JSON-RPC xatosi sifatida Payme'ga qaytariladigan xato.

    `data` — qaysi maydon sabab bo'lganini ko'rsatadi (masalan "order",
    "amount", "transaction") — bu Payme javobidagi `error.data` maydoniga
    tushadi.
    """

    def __init__(self, code: int, message: str, data: str | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.data = data

    def to_dict(self) -> dict:
        err: dict = {"code": self.code, "message": self.message}
        if self.data is not None:
            err["data"] = self.data
        return err


# --- Umumiy JSON-RPC xatolari -------------------------------------------------

def json_parse_error() -> PaymeError:
    return PaymeError(-32700, "JSON parsing exception", "json")


def required_field_missing(field: str = "field") -> PaymeError:
    return PaymeError(-32600, "Required field not found", field)


def method_not_found() -> PaymeError:
    return PaymeError(-32601, "Method not found", "method")


def unauthorized() -> PaymeError:
    return PaymeError(-32504, "Unauthorized request", "authorization")


def internal_error() -> PaymeError:
    return PaymeError(-32400, "Internal system error", None)


# --- Merchant API xatolari ------------------------------------------------

def invalid_amount() -> PaymeError:
    return PaymeError(-31001, "Invalid amount", "amount")


def transaction_not_found() -> PaymeError:
    return PaymeError(-31003, "Transaction not found", "transaction")


def unable_to_cancel() -> PaymeError:
    """Order allaqachon yakunlangan (mahsulot berilgan) — bekor qilib bo'lmaydi."""
    return PaymeError(-31007, "Unable to cancel transaction", "transaction")


def unable_to_perform() -> PaymeError:
    """Holat nomos: allaqachon yakunlangan/bekor qilingan yoki muddati o'tgan."""
    return PaymeError(-31008, "Unable to complete operation", "transaction")


def order_not_found() -> PaymeError:
    return PaymeError(-31050, "Order not found", "order")


def order_not_payable() -> PaymeError:
    """Order allaqachon to'langan yoki bekor qilingan — yangi to'lov bo'lmaydi."""
    return PaymeError(-31099, "Invoice already paid or cancelled", "order")


def transaction_already_exists() -> PaymeError:
    """Shu order uchun allaqachon boshqa (faol) tranzaksiya bor."""
    return PaymeError(-31099, "Transaction already exists", "transaction")
