/**
 * Payme Merchant API'ning 6 metodi va JSON-RPC dispatcher.
 *
 * Bu modul HECH QANDAY web-framework'ga bog'liq emas: kiruvchi so'rov
 * ma'lumotini oddiy obyekt sifatida oladi, javobni ham obyekt qilib
 * qaytaradi.
 *
 * Oqim (Click'dagi prepare/complete'dan farqli, Payme'da OLTITA metod bor):
 *
 *     CheckPerformTransaction — "bu to'lovni qabul qila olasanmi?"
 *     CreateTransaction       — Payme tranzaksiya ochadi (bizning "prepare"imiz)
 *     PerformTransaction      — pul yechildi, tasdiqla (bizning "complete"imiz)
 *     CancelTransaction       — to'lovni yoki tasdiqlangan to'lovni bekor qil
 *     CheckTransaction        — tranzaksiya holatini so'raydi
 *     GetStatement            — vaqt oralig'idagi tranzaksiyalar ro'yxati
 *
 * Bu faylga tegishingiz shart emas — bazangizga ulanish payme-orders.ts da.
 */

import { checkAuth } from "./payme-auth.js";
import { getConfig, type PaymeConfig } from "./payme-config.js";
import * as err from "./payme-errors.js";
import { PaymeError } from "./payme-errors.js";
import {
  orders as defaultOrders,
  PaymeState,
  TRANSACTION_TIMEOUT_MS,
  type PaymeOrdersAdapter,
  type PaymeTransaction,
} from "./payme-orders.js";

type Params = Record<string, unknown>;
type RpcResponse = { result?: unknown; error?: unknown; id: unknown };

// =============================================================================
//  1. CheckPerformTransaction — "bu to'lovni qabul qila olasanmi?"
// =============================================================================

async function checkPerformTransaction(
  params: Params,
  orders: PaymeOrdersAdapter,
): Promise<{ allow: true }> {
  const account = requireObject(params, "account");
  const amount = requireInt(params, "amount");

  const acc = await orders.findAccount(account);
  if (acc === null) throw err.orderNotFound();
  if (!acc.payable) throw err.orderNotPayable();
  if (amount !== acc.amount) throw err.invalidAmount();

  const existing = await orders.getActiveTransactionForAccount(account);
  if (existing !== null) throw err.transactionAlreadyExists();

  return { allow: true };
}

// =============================================================================
//  2. CreateTransaction — Payme tranzaksiya ochadi ("prepare")
// =============================================================================

async function createTransaction(params: Params, orders: PaymeOrdersAdapter) {
  const paymeId = requireString(params, "id");
  const paymeTime = requireInt(params, "time");
  const amount = requireInt(params, "amount");
  const account = requireObject(params, "account");

  const existing = await orders.getTransaction(paymeId);

  if (existing !== null) {
    if (existing.state !== PaymeState.PENDING) {
      throw err.unableToPerform();
    }
    if (isExpired(existing.paymeTime)) {
      await orders.markCancelled(paymeId, 4 /* TIMEOUT */);
      throw err.unableToPerform();
    }
    return createResult(existing);
  }

  // Yangi tranzaksiya — avval CheckPerformTransaction bilan bir xil
  // tekshiruvlarni bajaramiz.
  await checkPerformTransaction({ account, amount }, orders);

  const created = await orders.createTransaction(paymeId, paymeTime, amount, account);
  return createResult(created);
}

function createResult(tx: PaymeTransaction) {
  return { create_time: tx.createTime, transaction: tx.ourId, state: tx.state };
}

// =============================================================================
//  3. PerformTransaction — pul yechildi, tasdiqla ("complete")
// =============================================================================

async function performTransaction(params: Params, orders: PaymeOrdersAdapter) {
  const paymeId = requireString(params, "id");

  const tx = await orders.getTransaction(paymeId);
  if (tx === null) throw err.transactionNotFound();

  if (tx.state === PaymeState.PAID) {
    // Takroriy callback — mahsulot allaqachon berilgan.
    return performResult(tx);
  }

  if (tx.state !== PaymeState.PENDING) {
    throw err.unableToPerform();
  }

  if (isExpired(tx.paymeTime)) {
    await orders.markCancelled(paymeId, 4 /* TIMEOUT */);
    throw err.unableToPerform();
  }

  const updated = await orders.markPerformed(paymeId);
  if (updated === null) {
    // Parallel so'rov bizdan oldin ulgurdi.
    const again = await orders.getTransaction(paymeId);
    return performResult(again ?? tx);
  }

  const account = await orders.findAccount(updated.account);
  updated.accountExtra = account?.extra ?? {};
  await safeCall(() => orders.onPaid(updated), "onPaid", updated);

  return performResult(updated);
}

function performResult(tx: PaymeTransaction) {
  return { transaction: tx.ourId, perform_time: tx.performTime, state: tx.state };
}

// =============================================================================
//  4. CancelTransaction — to'lovni (yoki tasdiqlangan to'lovni) bekor qiladi
// =============================================================================

async function cancelTransaction(params: Params, orders: PaymeOrdersAdapter) {
  const paymeId = requireString(params, "id");
  const reason = requireInt(params, "reason");

  const tx = await orders.getTransaction(paymeId);
  if (tx === null) throw err.transactionNotFound();

  if (tx.state === PaymeState.CANCELLED || tx.state === PaymeState.CANCELLED_AFTER_PAID) {
    // Idempotent — mavjud natijani qaytaramiz, sababni yangilamaymiz.
    return cancelResult(tx);
  }

  if (tx.state === PaymeState.PAID) {
    const account = await orders.findAccount(tx.account);
    tx.accountExtra = account?.extra ?? {};
    const allowed = await safeCallBool(() => orders.canRefund(tx), true);
    if (!allowed) throw err.unableToCancel();
  }

  const updated = await orders.markCancelled(paymeId, reason);
  if (updated === null) {
    const again = await orders.getTransaction(paymeId);
    return cancelResult(again ?? tx);
  }

  const account = await orders.findAccount(updated.account);
  updated.accountExtra = account?.extra ?? {};
  await safeCall(() => orders.onCancelled(updated), "onCancelled", updated);

  return cancelResult(updated);
}

function cancelResult(tx: PaymeTransaction) {
  return { transaction: tx.ourId, cancel_time: tx.cancelTime, state: tx.state };
}

// =============================================================================
//  5. CheckTransaction — tranzaksiya holatini so'raydi
// =============================================================================

async function checkTransaction(params: Params, orders: PaymeOrdersAdapter) {
  const paymeId = requireString(params, "id");

  const tx = await orders.getTransaction(paymeId);
  if (tx === null) throw err.transactionNotFound();

  return {
    create_time: tx.createTime,
    perform_time: tx.performTime,
    cancel_time: tx.cancelTime,
    transaction: tx.ourId,
    state: tx.state,
    reason: tx.reason,
  };
}

// =============================================================================
//  6. GetStatement — vaqt oralig'idagi tranzaksiyalar ro'yxati
// =============================================================================

async function getStatement(params: Params, orders: PaymeOrdersAdapter) {
  const fromMs = requireInt(params, "from");
  const toMs = requireInt(params, "to");

  const txs = await orders.listTransactions(fromMs, toMs);

  return {
    transactions: txs.map((tx) => ({
      id: tx.paymeId,
      time: tx.paymeTime,
      amount: tx.amount,
      account: tx.account,
      create_time: tx.createTime,
      perform_time: tx.performTime,
      cancel_time: tx.cancelTime,
      transaction: tx.ourId,
      state: tx.state,
      reason: tx.reason,
    })),
  };
}

// =============================================================================
//  JSON-RPC dispatcher — HTTP qatlami shu bitta funksiyani chaqiradi
// =============================================================================

type Handler = (params: Params, orders: PaymeOrdersAdapter) => Promise<unknown>;

const METHODS: Record<string, Handler> = {
  CheckPerformTransaction: checkPerformTransaction,
  CreateTransaction: createTransaction,
  PerformTransaction: performTransaction,
  CancelTransaction: cancelTransaction,
  CheckTransaction: checkTransaction,
  GetStatement: getStatement,
};

/**
 * Payme'dan kelgan JSON-RPC so'rovini to'liq qayta ishlaydi.
 *
 * `body` — so'rov JSON'i (`{ method, params, id }`).
 * `authorizationHeader` — HTTP `Authorization` sarlavhasi (Basic ...).
 *
 * Har doim `{ result: ... }` yoki `{ error: {...} }` obyekt qaytaradi — bu
 * javobni HTTP 200 bilan qaytaring (Payme boshqa statusni "-32400" deb
 * tushunadi).
 */
export async function handleRequest(
  body: unknown,
  authorizationHeader: string | null | undefined,
  config: PaymeConfig = getConfig(),
  orders: PaymeOrdersAdapter = defaultOrders,
): Promise<RpcResponse> {
  const requestId =
    body && typeof body === "object" && "id" in body
      ? (body as Record<string, unknown>).id
      : null;

  try {
    if (!checkAuth(authorizationHeader, config)) {
      throw err.unauthorized();
    }

    if (!body || typeof body !== "object") {
      throw err.jsonParseError();
    }

    const b = body as Record<string, unknown>;
    const method = b.method;
    if (!method || typeof method !== "string") {
      throw err.requiredFieldMissing("method");
    }

    const handler = METHODS[method];
    if (!handler) throw err.methodNotFound();

    const params =
      b.params && typeof b.params === "object" ? (b.params as Params) : {};

    const result = await handler(params, orders);
    return { result, id: requestId };
  } catch (e) {
    if (e instanceof PaymeError) {
      return { error: e.toJSON(), id: requestId };
    }
    throw e;
  }
}

// --- Ichki yordamchilar -------------------------------------------------------

function isExpired(paymeTime: number): boolean {
  return Date.now() - paymeTime > TRANSACTION_TIMEOUT_MS;
}

function requireObject(params: Params, key: string): Record<string, unknown> {
  const value = params[key];
  if (!value || typeof value !== "object") throw err.requiredFieldMissing(key);
  return value as Record<string, unknown>;
}

function requireString(params: Params, key: string): string {
  const value = params[key];
  if (!value || typeof value !== "string") throw err.requiredFieldMissing(key);
  return value;
}

function requireInt(params: Params, key: string): number {
  const value = params[key];
  if (value === undefined || value === null || typeof value === "boolean") {
    throw err.requiredFieldMissing(key);
  }
  const n = Number(value);
  if (!Number.isFinite(n)) throw err.requiredFieldMissing(key);
  return Math.trunc(n);
}

/**
 * Hodisa funksiyasini chaqiradi; xato bo'lsa loglaydi, javobni buzmaydi.
 *
 * Bu nuqtaga yetganda pul allaqachon yechilgan/qaytarilgan. Xato bo'lsa ham
 * Payme'ga muvaffaqiyat javobi ketadi — holat bazada o'zgargan, faqat
 * callback ishlamay qolgan. Buni logdan kuzatib, qo'lda hal qilasiz.
 */
async function safeCall(
  fn: () => Promise<void>,
  name: string,
  tx: PaymeTransaction,
): Promise<void> {
  try {
    await fn();
  } catch (e) {
    console.error(
      `[payme] ${name}() xatosi (paymeId=${tx.paymeId}) — holat bazada o'zgargan, qo'lda tekshiring`,
      e,
    );
  }
}

async function safeCallBool(fn: () => Promise<boolean>, fallback: boolean): Promise<boolean> {
  try {
    return await fn();
  } catch (e) {
    console.error(`[payme] canRefund() xatosi — standart qiymat (${fallback}) ishlatiladi`, e);
    return fallback;
  }
}
