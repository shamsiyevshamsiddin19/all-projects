/**
 * =============================================================================
 *   SIZ FAQAT SHU FAYLNI TAHRIRLAYSIZ
 * =============================================================================
 *
 * Bu fayl Payme integratsiyasini SIZNING bazangiz bilan bog'laydi.
 * Qolgan fayllarga (payme-methods.ts, payme-auth.ts, payme-checkout.ts,
 * payme-config.ts, payme-errors.ts) tegish shart emas — ular o'zgarmaydi.
 *
 * `PaymeOrdersAdapter` interfeysida IKKI GURUH metod bor:
 *
 *     BIZNES (siz yozasiz):
 *       findAccount(account)     -> buyurtmangizni toping
 *       onPaid(transaction)      -> to'lov o'tgach mahsulotni bering
 *       onCancelled(transaction) -> bekor qilinganda (ixtiyoriy)
 *       canRefund(transaction)   -> to'langandan keyin bekor qilish mumkinmi
 *
 *     TRANZAKSIYA KUNDALIGI (Payme talab qiladi, demo tayyor turibdi):
 *       Payme protokoli CheckTransaction/GetStatement uchun har bir
 *       tranzaksiyani vaqti, holati va sababi bilan saqlab turishni talab
 *       qiladi. Hozir bu yerda XOTIRADAGI NAMUNA turibdi — ISHLAB
 *       CHIQARISHGA YAROQSIZ (server qayta tushsa yo'qoladi). Prisma va
 *       xom SQL uchun namunalar fayl oxirida.
 * =============================================================================
 */

/** Tranzaksiya holati. Bu qiymatlarni Payme belgilagan — o'zgartirmang. */
export const PaymeState = {
  PENDING: 1, // yaratilgan, hali to'lanmagan
  PAID: 2, // to'langan
  CANCELLED: -1, // bekor qilingan (to'lanmasdan turib)
  CANCELLED_AFTER_PAID: -2, // to'langandan keyin bekor qilingan (qaytarilgan)
} as const;

export type PaymeStateValue = (typeof PaymeState)[keyof typeof PaymeState];

/** Bekor qilish sabablari (Payme yuboradi, biz faqat saqlaymiz). */
export const PaymeReason = {
  RECEIVER_NOT_FOUND: 1,
  DEBIT_OPERATION_ERROR: 2,
  TRANSACTION_ERROR: 3,
  TIMEOUT: 4, // avtomatik bekor qilinganda BIZ shu sababni qo'yamiz
  REFUND: 5,
  UNKNOWN: 10,
} as const;

/** 12 soat — shuncha vaqt ichida to'lanmagan tranzaksiya avtomatik bekor bo'ladi. */
export const TRANSACTION_TIMEOUT_MS = 43_200_000;

/** `findAccount()` qaytaradigan narsa — sizning buyurtmangiz haqida. */
export interface PaymeAccount {
  /** Bazangizdagi buyurtma id'si. */
  id: string | number;
  /** Kutilayotgan summa TIYINDA (1 so'm = 100 tiyin). */
  amount: number;
  /** Buyurtma hali to'lov kutyaptimi? */
  payable: boolean;
  /** `onPaid()` ichida kerak bo'ladigan hamma narsa (userId, chatId...). */
  extra?: Record<string, unknown>;
}

/** Payme tranzaksiya yozuvi — protokol talab qiladigan kundalik yozuvi. */
export interface PaymeTransaction {
  paymeId: string;
  ourId: string;
  account: Record<string, unknown>;
  amount: number;
  state: PaymeStateValue;
  paymeTime: number;
  createTime: number;
  performTime: number;
  cancelTime: number;
  reason: number | null;
  accountExtra?: Record<string, unknown>;
}

export interface PaymeOrdersAdapter {
  // --- Biznes: siz o'zgartirasiz -------------------------------------------

  /** Payme yuborgan `account` maydonlari bo'yicha buyurtmani topadi. */
  findAccount(account: Record<string, unknown>): Promise<PaymeAccount | null>;

  /** To'lov tasdiqlangach BIR MARTA chaqiriladi. Mahsulotni shu yerda bering. */
  onPaid(transaction: PaymeTransaction): Promise<void>;

  /**
   * To'lov bekor qilinganda chaqiriladi. `transaction.state ===
   * PaymeState.CANCELLED_AFTER_PAID` bo'lsa — bu QAYTARISH.
   */
  onCancelled(transaction: PaymeTransaction): Promise<void>;

  /** To'langan tranzaksiyani bekor qilish (qaytarish) mumkinmi? */
  canRefund(transaction: PaymeTransaction): Promise<boolean>;

  // --- Tranzaksiya kundaligi: Payme talab qiladi ---------------------------

  getTransaction(paymeId: string): Promise<PaymeTransaction | null>;

  /** Shu hisob uchun hali bekor qilinmagan tranzaksiya bormi? */
  getActiveTransactionForAccount(
    account: Record<string, unknown>,
  ): Promise<PaymeTransaction | null>;

  /**
   * Yangi tranzaksiya yozuvini yaratadi (state=PENDING).
   *
   * `createTime` sizning serveringizning HOZIRGI vaqti bo'lishi kerak —
   * Payme yuborgan `paymeTime` esa faqat 12-soatlik muddatni hisoblash
   * uchun saqlanadi.
   */
  createTransaction(
    paymeId: string,
    paymeTime: number,
    amount: number,
    account: Record<string, unknown>,
  ): Promise<PaymeTransaction>;

  /**
   * Tranzaksiyani "to'langan" qiladi (PENDING -> PAID).
   *
   * Faqat HAQIQATAN o'tkazgan chaqiruv yozuvni qaytaradi — aks holda
   * `null`. Bu — takroriy so'rovda `onPaid()` qayta chaqirilmasligi uchun
   * MUHIM. Bazangizda atomar `UPDATE ... WHERE state=1` bilan qiling.
   */
  markPerformed(paymeId: string): Promise<PaymeTransaction | null>;

  /**
   * Tranzaksiyani bekor qiladi (PENDING -> CANCELLED yoki PAID ->
   * CANCELLED_AFTER_PAID). Allaqachon bekor qilingan bo'lsa `null`.
   */
  markCancelled(paymeId: string, reason: number): Promise<PaymeTransaction | null>;

  /** `createTime` bo'yicha [fromMs, toMs] oralig'idagi tranzaksiyalar. */
  listTransactions(fromMs: number, toMs: number): Promise<PaymeTransaction[]>;
}

// =============================================================================
//   NAMUNA — xotirada saqlaydigan adapter.
//   O'z bazangizga o'tganingizda butun shu blokni almashtiring.
// =============================================================================

interface DemoOrder {
  id: string;
  amountTiyin: number;
  status: "pending" | "paid" | "cancelled";
  product: string;
}

const demoOrders = new Map<string, DemoOrder>();
const demoTransactions = new Map<string, PaymeTransaction>();

export const orders: PaymeOrdersAdapter = {
  async findAccount(account) {
    const orderId = account.order_id;
    if (orderId === undefined) return null;

    const order = demoOrders.get(String(orderId));
    if (!order) return null;

    return {
      id: order.id,
      amount: order.amountTiyin,
      payable: order.status === "pending",
      extra: { product: order.product },
    };
  },

  async onPaid(transaction) {
    const orderId = transaction.account.order_id;
    const order = demoOrders.get(String(orderId));
    if (order) order.status = "paid";

    console.log("[payme] TO'LANDI", {
      orderId,
      amountTiyin: transaction.amount,
      paymeId: transaction.paymeId,
    });
  },

  async onCancelled(transaction) {
    const orderId = transaction.account.order_id;
    const order = demoOrders.get(String(orderId));
    if (order) order.status = "cancelled";

    const isRefund = transaction.state === PaymeState.CANCELLED_AFTER_PAID;
    console.log(`[payme] BEKOR QILINDI${isRefund ? " (qaytarish)" : ""}`, {
      orderId,
      reason: transaction.reason,
    });
  },

  async canRefund() {
    return true;
  },

  async getTransaction(paymeId) {
    return demoTransactions.get(paymeId) ?? null;
  },

  async getActiveTransactionForAccount(account) {
    const orderId = account.order_id;
    for (const tx of demoTransactions.values()) {
      if (
        tx.account.order_id === orderId &&
        (tx.state === PaymeState.PENDING || tx.state === PaymeState.PAID)
      ) {
        return tx;
      }
    }
    return null;
  },

  async createTransaction(paymeId, paymeTime, amount, account) {
    const tx: PaymeTransaction = {
      paymeId,
      ourId: paymeId,
      account,
      amount,
      state: PaymeState.PENDING,
      paymeTime,
      createTime: Date.now(),
      performTime: 0,
      cancelTime: 0,
      reason: null,
    };
    demoTransactions.set(paymeId, tx);
    return tx;
  },

  async markPerformed(paymeId) {
    const tx = demoTransactions.get(paymeId);
    if (!tx || tx.state !== PaymeState.PENDING) return null;

    tx.state = PaymeState.PAID;
    tx.performTime = Date.now();
    return tx;
  },

  async markCancelled(paymeId, reason) {
    const tx = demoTransactions.get(paymeId);
    if (
      !tx ||
      tx.state === PaymeState.CANCELLED ||
      tx.state === PaymeState.CANCELLED_AFTER_PAID
    ) {
      return null;
    }

    tx.state = tx.state === PaymeState.PAID ? PaymeState.CANCELLED_AFTER_PAID : PaymeState.CANCELLED;
    tx.cancelTime = Date.now();
    tx.reason = reason;
    return tx;
  },

  async listTransactions(fromMs, toMs) {
    return [...demoTransactions.values()].filter(
      (tx) => tx.createTime >= fromMs && tx.createTime <= toMs,
    );
  },
};

/**
 * Namuna uchun buyurtma yaratadi.
 *
 * O'z tizimingizda buyurtma allaqachon bazangizda bo'ladi — bu funksiya
 * kerak emas.
 */
export function demoCreateOrder(orderId: string, amountTiyin: number, product = ""): void {
  demoOrders.set(orderId, { id: orderId, amountTiyin, status: "pending", product });
}

/** Testlar uchun — namuna ma'lumotlarini tozalaydi. */
export function demoReset(): void {
  demoOrders.clear();
  demoTransactions.clear();
}

// =============================================================================
//   O'Z BAZANGIZ UCHUN NAMUNALAR — nusxa oling va `orders` obyekti o'rniga
//   qo'ying.
// =============================================================================
//
// ─── Prisma ──────────────────────────────────────────────────────────────────
//
//   import { prisma } from "@/lib/prisma";
//
//   export const orders: PaymeOrdersAdapter = {
//     async findAccount(account) {
//       const o = await prisma.order.findUnique({ where: { id: String(account.order_id) } });
//       if (!o) return null;
//       return {
//         id: o.id,
//         amount: o.priceTiyin,             // bazada TIYINDA saqlang
//         payable: o.status === "PENDING",
//         extra: { userId: o.userId },
//       };
//     },
//
//     async onPaid(tx) {
//       await prisma.order.update({
//         where: { id: String(tx.account.order_id) },
//         data: { status: "PAID" },
//       });
//     },
//
//     async onCancelled(tx) {
//       await prisma.order.update({
//         where: { id: String(tx.account.order_id) },
//         data: { status: "CANCELLED" },
//       });
//     },
//
//     async canRefund() { return true; },
//
//     async getTransaction(paymeId) {
//       const t = await prisma.paymeTransaction.findUnique({ where: { paymeId } });
//       return t ? mapRow(t) : null;
//     },
//
//     async markPerformed(paymeId) {
//       // updateMany + where.state — ATOMAR. `update` emas!
//       const { count } = await prisma.paymeTransaction.updateMany({
//         where: { paymeId, state: 1 },
//         data: { state: 2, performTime: Date.now() },
//       });
//       if (count === 0) return null;
//       return this.getTransaction(paymeId);
//     },
//
//     // ... markCancelled, createTransaction, getActiveTransactionForAccount,
//     // listTransactions — xuddi shu naqsh bilan.
//   };
//
// =============================================================================
