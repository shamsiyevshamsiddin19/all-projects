/**
 * Uzum Bank Merchant API'ning 5 webhook'i.
 *
 * Bu modul HECH QANDAY web-framework'ga bog'liq emas: kiruvchi so'rov
 * ma'lumotini oddiy obyekt sifatida oladi, javobni `[httpStatus, body]`
 * juft qilib qaytaradi.
 *
 * Click/Payme'dan FARQI: Uzum Bank BESHTA ALOHIDA manzilga so'rov yuboradi
 * (bitta JSON-RPC endpoint emas) va xato holatida HTTP 400 kutadi (200 emas):
 *
 *     POST /check    — "bu to'lovni qabul qila olasanmi?" (pul yo'q hali)
 *     POST /create   — Uzum Bank tranzaksiya ochadi
 *     POST /confirm  — PUL ALLAQACHON YECHILGAN, mahsulotni ber
 *     POST /reverse  — to'lovni yoki tasdiqlangan to'lovni bekor qil
 *     POST /status   — tranzaksiya holatini so'raydi
 *
 * Bu faylga tegishingiz shart emas — bazangizga ulanish uzum-orders.ts da.
 */

import { checkAuth } from "./uzum-auth.js";
import { getConfig, type UzumConfig } from "./uzum-config.js";
import * as err from "./uzum-errors.js";
import { UzumError } from "./uzum-errors.js";
import {
  orders as defaultOrders,
  UzumState,
  TRANSACTION_TIMEOUT_MS,
  type UzumOrdersAdapter,
  type UzumTransaction,
} from "./uzum-orders.js";

type Data = Record<string, unknown>;
type Response = [number, Record<string, unknown>];

function nowMs(): number {
  return Date.now();
}

function isExpired(createTime: number): boolean {
  return nowMs() - createTime > TRANSACTION_TIMEOUT_MS;
}

function requireField(data: Data, key: string): unknown {
  const value = data[key];
  if (value === undefined || value === null || value === "") {
    throw err.requiredFieldMissing();
  }
  return value;
}

function requireServiceId(data: Data, config: UzumConfig): void {
  const raw = requireField(data, "serviceId");
  const serviceId = Number(raw);
  if (!Number.isFinite(serviceId) || serviceId !== config.serviceId) {
    throw err.invalidServiceId();
  }
}

// =============================================================================
//  1. /check — "bu to'lovni qabul qila olasanmi?"
// =============================================================================

export async function handleCheck(
  data: Data,
  authorizationHeader: string | null | undefined,
  config: UzumConfig = getConfig(),
  orders: UzumOrdersAdapter = defaultOrders,
): Promise<Response> {
  return wrap(async () => {
    if (!checkAuth(authorizationHeader, config)) throw err.accessDenied();

    requireServiceId(data, config);
    requireField(data, "timestamp");
    const params = requireField(data, "params");
    if (!params || typeof params !== "object") throw err.requiredFieldMissing();

    const account = await orders.findAccount(params as Data);
    if (account === null) throw err.accountNotFound();
    if (!account.payable) throw err.alreadyPaid();

    return {
      serviceId: config.serviceId,
      timestamp: nowMs(),
      status: "OK",
    };
  });
}

// =============================================================================
//  2. /create — Uzum Bank tranzaksiya ochadi
// =============================================================================

export async function handleCreate(
  data: Data,
  authorizationHeader: string | null | undefined,
  config: UzumConfig = getConfig(),
  orders: UzumOrdersAdapter = defaultOrders,
): Promise<Response> {
  return wrap(async () => {
    if (!checkAuth(authorizationHeader, config)) throw err.accessDenied();

    requireServiceId(data, config);
    requireField(data, "timestamp");
    const transId = String(requireField(data, "transId"));
    const params = requireField(data, "params");
    const amountRaw = requireField(data, "amount");
    if (!params || typeof params !== "object") throw err.requiredFieldMissing();

    // DIQQAT: takroriy /create — Uzum Bank hujjati bo'yicha bu XATO,
    // Payme'dagidek "idempotent — bir xil natijani qaytar" emas.
    const existing = await orders.getTransaction(transId);
    if (existing !== null) throw err.transactionAlreadyCreated();

    const account = await orders.findAccount(params as Data);
    if (account === null) throw err.accountNotFound();
    if (!account.payable) throw err.alreadyPaid();

    const amount = Number(amountRaw);
    if (amount !== account.amount) throw err.invalidAmount();

    // Mudofaa uchun qo'shilgan (hujjatda so'zma-so'z yozilmagan): bitta
    // buyurtmaga ikkita PARALLEL faol tranzaksiya ochilmasin.
    const active = await orders.getActiveTransactionForAccount(params as Data);
    if (active !== null) throw err.alreadyPaid();

    const created = await orders.createTransaction(transId, amount, params as Data);

    return {
      serviceId: config.serviceId,
      transId: created.transId,
      status: UzumState.CREATED,
      transTime: created.createTime,
    };
  }, { transTime: true });
}

// =============================================================================
//  3. /confirm — PUL ALLAQACHON YECHILGAN, mahsulotni ber
// =============================================================================

export async function handleConfirm(
  data: Data,
  authorizationHeader: string | null | undefined,
  config: UzumConfig = getConfig(),
  orders: UzumOrdersAdapter = defaultOrders,
): Promise<Response> {
  return wrap(async () => {
    if (!checkAuth(authorizationHeader, config)) throw err.accessDenied();

    requireServiceId(data, config);
    requireField(data, "timestamp");
    const transId = String(requireField(data, "transId"));
    requireField(data, "paymentSource");
    requireField(data, "phone");

    const tx = await orders.getTransaction(transId);
    if (tx === null) throw err.transactionNotFound();

    if (tx.state === UzumState.REVERSED) throw err.transactionCancelled();

    if (tx.state === UzumState.CONFIRMED) {
      // Uzum Bank hujjati bo'yicha takroriy /confirm — XATO.
      throw err.transactionAlreadyConfirmed();
    }

    if (isExpired(tx.createTime)) {
      await orders.markReversed(transId);
      throw err.transactionCancelled();
    }

    const updated = await orders.markConfirmed(transId);
    if (updated === null) {
      const again = await orders.getTransaction(transId);
      if (again !== null && again.state === UzumState.CONFIRMED) {
        throw err.transactionAlreadyConfirmed();
      }
      throw err.internalError();
    }

    const account = await orders.findAccount(updated.params);
    updated.accountExtra = account?.extra ?? {};
    await safeCall(() => orders.onConfirmed(updated), "onConfirmed", updated);

    return {
      serviceId: config.serviceId,
      transId: updated.transId,
      status: UzumState.CONFIRMED,
      confirmTime: updated.confirmTime,
    };
  }, { confirmTime: true });
}

// =============================================================================
//  4. /reverse — to'lovni (yoki tasdiqlangan to'lovni) bekor qiladi
// =============================================================================

export async function handleReverse(
  data: Data,
  authorizationHeader: string | null | undefined,
  config: UzumConfig = getConfig(),
  orders: UzumOrdersAdapter = defaultOrders,
): Promise<Response> {
  return wrap(async () => {
    if (!checkAuth(authorizationHeader, config)) throw err.accessDenied();

    requireServiceId(data, config);
    requireField(data, "timestamp");
    const transId = String(requireField(data, "transId"));

    const tx = await orders.getTransaction(transId);
    if (tx === null) throw err.transactionNotFound();

    if (tx.state === UzumState.REVERSED) {
      // Uzum Bank hujjati bo'yicha takroriy /reverse — XATO.
      throw err.transactionAlreadyCancelled();
    }

    if (tx.state === UzumState.CONFIRMED) {
      const account = await orders.findAccount(tx.params);
      tx.accountExtra = account?.extra ?? {};
      const allowed = await safeCallBool(() => orders.canReverse(tx), true);
      if (!allowed) throw err.unableToCancel();
    }

    const updated = await orders.markReversed(transId);
    if (updated === null) throw err.transactionAlreadyCancelled();

    const account = await orders.findAccount(updated.params);
    updated.accountExtra = account?.extra ?? {};
    await safeCall(() => orders.onReversed(updated), "onReversed", updated);

    return {
      serviceId: config.serviceId,
      transId: updated.transId,
      status: UzumState.REVERSED,
      reverseTime: updated.reverseTime,
    };
  }, { reverseTime: true });
}

// =============================================================================
//  5. /status — tranzaksiya holatini so'raydi
// =============================================================================

export async function handleStatus(
  data: Data,
  authorizationHeader: string | null | undefined,
  config: UzumConfig = getConfig(),
  orders: UzumOrdersAdapter = defaultOrders,
): Promise<Response> {
  return wrap(async () => {
    if (!checkAuth(authorizationHeader, config)) throw err.accessDenied();

    requireServiceId(data, config);
    requireField(data, "timestamp");
    const transId = String(requireField(data, "transId"));

    let tx = await orders.getTransaction(transId);
    if (tx === null) throw err.transactionNotFound();

    // Uzum Bank /confirm javobsiz qolganda aynan shu /status orqali holatni
    // bilib oladi — shuning uchun bu yerda ham 30-daqiqalik muddatni
    // tekshiramiz.
    if (tx.state === UzumState.CREATED && isExpired(tx.createTime)) {
      const expired = await orders.markReversed(transId);
      if (expired !== null) tx = expired;
    }

    const result: Record<string, unknown> = {
      serviceId: config.serviceId,
      transId: tx.transId,
      status: tx.state,
      transTime: tx.createTime,
    };
    if (tx.confirmTime) result.confirmTime = tx.confirmTime;
    if (tx.reverseTime) result.reverseTime = tx.reverseTime;

    return result;
  });
}

// =============================================================================
//  Ichki yordamchilar
// =============================================================================

interface ExtraTimeFields {
  transTime?: boolean;
  confirmTime?: boolean;
  reverseTime?: boolean;
}

/**
 * Handler'ni chaqiradi va `[httpStatus, body]` juftini qaytaradi.
 *
 * Muvaffaqiyat -> [200, natija]. Xato -> [400, {errorCode, ...}], chunki
 * Uzum Bank ba'zi xato javoblarida ham transTime/confirmTime/reverseTime
 * maydonini kutadi.
 */
async function wrap(
  fn: () => Promise<Record<string, unknown>>,
  extra: ExtraTimeFields = {},
): Promise<Response> {
  try {
    return [200, await fn()];
  } catch (e) {
    if (e instanceof UzumError) {
      const body: Record<string, unknown> = { ...e.toJSON() };
      const now = nowMs();
      if (extra.transTime) body.transTime = now;
      if (extra.confirmTime) body.confirmTime = now;
      if (extra.reverseTime) body.reverseTime = now;
      return [400, body];
    }
    console.error("[uzum] kutilmagan xato", e);
    return [400, err.internalError().toJSON()];
  }
}

/**
 * Hodisa funksiyasini chaqiradi; xato bo'lsa loglaydi, javobni buzmaydi.
 *
 * Bu nuqtaga yetganda pul allaqachon yechilgan. Xato bo'lsa ham Uzum
 * Bank'ga muvaffaqiyat javobi ketadi — holat bazada o'zgargan, faqat
 * callback ishlamay qolgan. Logdan kuzatib, qo'lda hal qilasiz.
 */
async function safeCall(
  fn: () => Promise<void>,
  name: string,
  tx: UzumTransaction,
): Promise<void> {
  try {
    await fn();
  } catch (e) {
    console.error(
      `[uzum] ${name}() xatosi (transId=${tx.transId}) — holat bazada o'zgargan, qo'lda tekshiring`,
      e,
    );
  }
}

async function safeCallBool(fn: () => Promise<boolean>, fallback: boolean): Promise<boolean> {
  try {
    return await fn();
  } catch (e) {
    console.error(`[uzum] canReverse() xatosi — standart qiymat (${fallback}) ishlatiladi`, e);
    return fallback;
  }
}
