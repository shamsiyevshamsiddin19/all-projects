/**
 * Uzum Bank Merchant API xato kodlari.
 *
 * Bu kodlarni Uzum Bank belgilagan (rasmiy hujjat: developer.uzumbank.uz,
 * "Коды ошибок" bo'limi) — o'zgartirmang.
 *
 * MUHIM: Uzum'da xato kodi SATR sifatida yuboriladi ("10007", raqam emas)
 * va javob HTTP 400 bilan qaytariladi (Click/Payme'da esa har doim 200).
 *
 * Bu faylga tegishingiz shart emas.
 */

export class UzumError extends Error {
  readonly code: string;

  constructor(code: string, message: string) {
    super(message);
    this.name = "UzumError";
    this.code = code;
  }

  toJSON(): { errorCode: string } {
    return { errorCode: this.code };
  }
}

// --- Umumiy xatolar (barcha webhook'larda) -----------------------------------

export const accessDenied = () => new UzumError("10001", "Access denied");

export const jsonParseError = () => new UzumError("10002", "JSON parsing error");

export const invalidOperation = () =>
  new UzumError("10003", "Invalid operation (method must be POST)");

export const requiredFieldMissing = () =>
  new UzumError("10005", "Required parameter is missing");

// --- /check va /create uchun ---------------------------------------------

export const invalidServiceId = () => new UzumError("10006", "Invalid serviceId");

export const accountNotFound = () =>
  new UzumError("10007", "Additional payment attribute not found");

export const alreadyPaid = () => new UzumError("10008", "Payment already paid");

export const alreadyCancelled = () => new UzumError("10009", "Payment cancelled");

// --- /create uchun ---------------------------------------------------------

/**
 * Shu `transId` bilan tranzaksiya allaqachon yaratilgan.
 *
 * DIQQAT: bu Click/Payme'dagidek "idempotent — bir xil natijani qaytar"
 * emas — Uzum Bank hujjati aniq shunday deydi: "Верните этот код при
 * повторном создании транзакции с тем же transId".
 */
export const transactionAlreadyCreated = () =>
  new UzumError("10010", "Transaction with this transId already created");

export const invalidAmount = () => new UzumError("10011", "Invalid amount");

export const amountTooLow = () => new UzumError("10012", "Amount is below the minimum");

export const amountTooHigh = () => new UzumError("10013", "Amount is above the maximum");

// --- /confirm, /reverse, /status uchun --------------------------------------

export const transactionNotFound = () => new UzumError("10014", "Transaction not found");

/** Bekor qilingan tranzaksiyani tasdiqlab (confirm) bo'lmaydi. */
export const transactionCancelled = () => new UzumError("10015", "Transaction is cancelled");

/**
 * Takroriy /confirm so'rovi — Uzum Bank hujjati bo'yicha bu ham XATO,
 * idempotent muvaffaqiyat emas (10010 bilan bir xil mantiq).
 */
export const transactionAlreadyConfirmed = () =>
  new UzumError("10016", "Transaction already confirmed");

export const unableToCancel = () =>
  new UzumError("10017", "Unable to cancel transaction in current state");

/** Takroriy /reverse so'rovi — xato qaytariladi (idempotent emas). */
export const transactionAlreadyCancelled = () =>
  new UzumError("10018", "Transaction already cancelled");

// --- Ichki xato ---------------------------------------------------------

export const internalError = () => new UzumError("99999", "Internal server error");
