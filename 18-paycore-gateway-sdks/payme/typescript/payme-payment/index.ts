/**
 * Payme (checkout.paycom.uz / business.payme.uz) to'lov integratsiyasi.
 *
 * Click'dan farqi: bitta prepare/complete o'rniga OLTITA JSON-RPC metod va
 * imzo o'rniga HTTP Basic Auth ishlatiladi.
 *
 * @example
 * import { checkoutUrl, somToTiyin, handleRequest } from "@/payme-payment";
 *
 * // 1) To'lov havolasi
 * const url = checkoutUrl({ order_id: 42 }, somToTiyin(5000));
 *
 * // 2) Yagona endpoint
 * const response = await handleRequest(body, authorizationHeader);
 */

export { checkAuth } from "./payme-auth.js";
export { checkoutUrl, somToTiyin, type CheckoutOptions } from "./payme-checkout.js";
export {
  getConfig,
  setConfig,
  PaymeConfigError,
  type PaymeConfig,
} from "./payme-config.js";
export { PaymeError } from "./payme-errors.js";
export { handleRequest } from "./payme-methods.js";
export {
  orders,
  demoCreateOrder,
  demoReset,
  PaymeState,
  PaymeReason,
  TRANSACTION_TIMEOUT_MS,
  type PaymeAccount,
  type PaymeTransaction,
  type PaymeOrdersAdapter,
  type PaymeStateValue,
} from "./payme-orders.js";
