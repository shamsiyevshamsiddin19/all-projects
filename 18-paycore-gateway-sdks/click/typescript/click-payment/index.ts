/**
 * Click (my.click.uz) to'lov integratsiyasi.
 *
 * @example
 * import { paymentUrl, handlePrepare, handleComplete } from "@/click-payment";
 *
 * // 1) To'lov havolasi
 * const url = paymentUrl("ORD42", 5000);
 *
 * // 2) Endpoint'laringizda
 * const javob = await handlePrepare(data);   // JSON qilib qaytaring
 * const javob = await handleComplete(data);
 *
 * Bazangizga ulanish `click-orders.ts` da — faqat shu faylni tahrirlaysiz.
 */

export {
  getConfig,
  setConfig,
  paymentUrl,
  formatAmount,
  ClickConfigError,
  type ClickConfig,
} from "./click-config.js";

export { ClickError, errorNote, type ClickErrorCode } from "./click-errors.js";

export {
  orders,
  demoCreateOrder,
  demoReset,
  type ClickOrder,
  type ClickOrderStatus,
  type ClickOrdersAdapter,
} from "./click-orders.js";

export {
  handlePrepare,
  PREPARE_REQUIRED_FIELDS,
  type ClickPrepareResponse,
} from "./click-prepare.js";

export {
  handleComplete,
  COMPLETE_REQUIRED_FIELDS,
  type ClickCompleteResponse,
} from "./click-complete.js";

export {
  buildSignString,
  makeSign,
  signsEqual,
  checkSign,
  ACTION_PREPARE,
  ACTION_COMPLETE,
  type SignParts,
} from "./click-signature.js";

export {
  readRequestData,
  clickLog,
  amountsMatch,
  type ClickRequestData,
} from "./click-utils.js";
