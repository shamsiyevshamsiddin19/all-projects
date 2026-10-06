/**
 * Click xato kodlari.
 *
 * Bu kodlarni Click belgilagan — o'zgartirmang. Click javobdagi `error`
 * maydoniga qarab to'lovni davom ettiradi yoki to'xtatadi.
 *
 * Bu faylga tegishingiz shart emas.
 */

export const ClickError = {
  /** Muvaffaqiyat */
  SUCCESS: 0,
  /** Imzo (sign_string) yoki service_id mos kelmadi */
  SIGN_CHECK_FAILED: -1,
  /** So'rovdagi summa bazadagidan farq qiladi */
  INCORRECT_AMOUNT: -2,
  ACTION_NOT_FOUND: -3,
  /** To'lov allaqachon to'langan */
  ALREADY_PAID: -4,
  /** merchant_trans_id bo'yicha buyurtma topilmadi */
  USER_NOT_FOUND: -5,
  /** merchant_prepare_id mos kelmadi */
  TRANSACTION_NOT_FOUND: -6,
  FAILED_TO_UPDATE_USER: -7,
  /** So'rovda majburiy maydon yetishmayapti */
  BAD_REQUEST: -8,
  /** To'lov bekor qilingan */
  TRANSACTION_CANCELLED: -9,
} as const;

export type ClickErrorCode = (typeof ClickError)[keyof typeof ClickError];

const ERROR_NOTES: Record<number, string> = {
  [ClickError.SUCCESS]: "Success",
  [ClickError.SIGN_CHECK_FAILED]: "SIGN CHECK FAILED!",
  [ClickError.INCORRECT_AMOUNT]: "Incorrect parameter amount",
  [ClickError.ACTION_NOT_FOUND]: "Action not found",
  [ClickError.ALREADY_PAID]: "Already paid",
  [ClickError.USER_NOT_FOUND]: "User does not exist",
  [ClickError.TRANSACTION_NOT_FOUND]: "Transaction does not exist",
  [ClickError.FAILED_TO_UPDATE_USER]: "Failed to update user",
  [ClickError.BAD_REQUEST]: "Error in request from click",
  [ClickError.TRANSACTION_CANCELLED]: "Transaction cancelled",
};

export function errorNote(code: number): string {
  return ERROR_NOTES[code] ?? "Unknown error";
}
