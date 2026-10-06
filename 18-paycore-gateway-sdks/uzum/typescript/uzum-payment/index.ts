/**
 * Uzum Bank Merchant API integratsiyasi.
 *
 * Click/Payme'dan farqli — Uzum Bank'da to'lov havolasi (checkout URL) YO'Q.
 * Foydalanuvchi Uzum Bank ilovasida xizmatingizni `serviceId` orqali topadi
 * va TO'LOVNI O'SHA YERDA BOSHLAYDI. Sizning serveringiz faqat 5 ta
 * webhook'ni qabul qiladi.
 *
 * @example
 * import { handleCheck, handleCreate, handleConfirm, handleReverse, handleStatus }
 *   from "@/uzum-payment";
 *
 * const [status, body] = await handleCheck(requestData, authHeader);
 * // status (200 yoki 400) va body ni JSON qilib qaytaring
 */

export { checkAuth } from "./uzum-auth.js";
export { getConfig, setConfig, UzumConfigError, type UzumConfig } from "./uzum-config.js";
export { UzumError } from "./uzum-errors.js";
export {
  handleCheck,
  handleCreate,
  handleConfirm,
  handleReverse,
  handleStatus,
} from "./uzum-methods.js";
export {
  orders,
  demoCreateOrder,
  demoReset,
  UzumState,
  TRANSACTION_TIMEOUT_MS,
  type UzumAccount,
  type UzumTransaction,
  type UzumOrdersAdapter,
  type UzumStateValue,
} from "./uzum-orders.js";
