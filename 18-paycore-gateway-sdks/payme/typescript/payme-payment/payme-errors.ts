/**
 * Payme JSON-RPC xato kodlari.
 *
 * Bu kodlarni Payme belgilagan — o'zgartirmang.
 *
 * Bu faylga tegishingiz shart emas.
 */

export class PaymeError extends Error {
  readonly code: number;
  readonly data: string | null;

  constructor(code: number, message: string, data: string | null = null) {
    super(message);
    this.name = "PaymeError";
    this.code = code;
    this.data = data;
  }

  toJSON(): { code: number; message: string; data?: string } {
    const err: { code: number; message: string; data?: string } = {
      code: this.code,
      message: this.message,
    };
    if (this.data !== null) err.data = this.data;
    return err;
  }
}

// --- Umumiy JSON-RPC xatolari -------------------------------------------------

export const jsonParseError = () => new PaymeError(-32700, "JSON parsing exception", "json");

export const requiredFieldMissing = (field = "field") =>
  new PaymeError(-32600, "Required field not found", field);

export const methodNotFound = () => new PaymeError(-32601, "Method not found", "method");

export const unauthorized = () => new PaymeError(-32504, "Unauthorized request", "authorization");

export const internalError = () => new PaymeError(-32400, "Internal system error", null);

// --- Merchant API xatolari ------------------------------------------------

export const invalidAmount = () => new PaymeError(-31001, "Invalid amount", "amount");

export const transactionNotFound = () =>
  new PaymeError(-31003, "Transaction not found", "transaction");

/** Order allaqachon yakunlangan (mahsulot berilgan) — bekor qilib bo'lmaydi. */
export const unableToCancel = () =>
  new PaymeError(-31007, "Unable to cancel transaction", "transaction");

/** Holat nomos: allaqachon yakunlangan/bekor qilingan yoki muddati o'tgan. */
export const unableToPerform = () =>
  new PaymeError(-31008, "Unable to complete operation", "transaction");

export const orderNotFound = () => new PaymeError(-31050, "Order not found", "order");

/** Order allaqachon to'langan yoki bekor qilingan — yangi to'lov bo'lmaydi. */
export const orderNotPayable = () =>
  new PaymeError(-31099, "Invoice already paid or cancelled", "order");

/** Shu order uchun allaqachon boshqa (faol) tranzaksiya bor. */
export const transactionAlreadyExists = () =>
  new PaymeError(-31099, "Transaction already exists", "transaction");
