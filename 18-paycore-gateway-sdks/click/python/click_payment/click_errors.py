"""Click xato kodlari.

Bu kodlarni Click belgilagan — o'zgartirmang. Click javobdagi `error`
maydoniga qarab to'lovni davom ettiradi yoki to'xtatadi.
"""

from __future__ import annotations

# Muvaffaqiyat
SUCCESS = 0

# Imzo (sign_string) yoki service_id mos kelmadi
SIGN_CHECK_FAILED = -1

# So'rovdagi summa bazadagidan farq qiladi
INCORRECT_AMOUNT = -2

ACTION_NOT_FOUND = -3

# To'lov allaqachon to'langan
ALREADY_PAID = -4

# merchant_trans_id bo'yicha buyurtma topilmadi
USER_NOT_FOUND = -5

# merchant_prepare_id mos kelmadi
TRANSACTION_NOT_FOUND = -6

FAILED_TO_UPDATE_USER = -7

# So'rovda majburiy maydon yetishmayapti
BAD_REQUEST = -8

# To'lov bekor qilingan
TRANSACTION_CANCELLED = -9


ERROR_NOTES = {
    SUCCESS: "Success",
    SIGN_CHECK_FAILED: "SIGN CHECK FAILED!",
    INCORRECT_AMOUNT: "Incorrect parameter amount",
    ACTION_NOT_FOUND: "Action not found",
    ALREADY_PAID: "Already paid",
    USER_NOT_FOUND: "User does not exist",
    TRANSACTION_NOT_FOUND: "Transaction does not exist",
    FAILED_TO_UPDATE_USER: "Failed to update user",
    BAD_REQUEST: "Error in request from click",
    TRANSACTION_CANCELLED: "Transaction cancelled",
}


def error_note(code: int) -> str:
    return ERROR_NOTES.get(int(code), "Unknown error")
