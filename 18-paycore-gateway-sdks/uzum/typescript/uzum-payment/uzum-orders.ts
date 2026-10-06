/**
 * =============================================================================
 *   SIZ FAQAT SHU FAYLNI TAHRIRLAYSIZ
 * =============================================================================
 *
 * Bu fayl Uzum Bank integratsiyasini SIZNING bazangiz bilan bog'laydi.
 * Qolgan fayllarga (uzum-methods.ts, uzum-auth.ts, uzum-config.ts,
 * uzum-errors.ts) tegish shart emas — ular o'zgarmaydi.
 *
 * `UzumOrdersAdapter` interfeysida IKKI GURUH metod bor:
 *
 *     BIZNES (siz yozasiz):
 *       findAccount(params)      -> buyurtmangizni toping
 *       onConfirmed(transaction) -> to'lov o'tgach mahsulotni bering
 *       onReversed(transaction)  -> bekor qilinganda (ixtiyoriy)
 *       canReverse(transaction)  -> tasdiqlangandan keyin bekor qilish
 *                                    mumkinmi (ixtiyoriy)
 *
 *     TRANZAKSIYA KUNDALIGI (Uzum Bank talab qiladi, demo tayyor turibdi):
 *       Har bir tranzaksiyani vaqti va holati bilan saqlab turish — Uzum
 *       Bank'ning protokol talabi (/status shuni so'raydi). Hozir bu yerda
 *       XOTIRADAGI NAMUNA turibdi — ISHLAB CHIQARISHGA YAROQSIZ (server
 *       qayta tushsa yo'qoladi). Prisma va xom SQL uchun namunalar fayl
 *       oxirida.
 * =============================================================================
 */

/** Tranzaksiya holati. Bu qiymatlarni Uzum Bank belgilagan — o'zgartirmang. */
export const UzumState = {
  CREATED: "CREATED", // yaratilgan, hali tasdiqlanmagan
  CONFIRMED: "CONFIRMED", // to'langan (mahsulot berilgan)
  REVERSED: "REVERSED", // bekor qilingan (to'lanmasdan turib YOKI qaytarilgan)
} as const;

export type UzumStateValue = (typeof UzumState)[keyof typeof UzumState];

/**
 * 30 daqiqa — shuncha vaqt ichida tasdiqlanmagan (/confirm kelmagan)
 * tranzaksiya "muvaffaqiyatsiz" hisoblanadi. Buni Uzum Bank alohida xabar
 * bermaydi — o'zimiz kuzatamiz (Payme'da 12 soat, xuddi shu tamoyilda).
 */
export const TRANSACTION_TIMEOUT_MS = 30 * 60 * 1000;

/** `findAccount()` qaytaradigan narsa — sizning buyurtmangiz haqida. */
export interface UzumAccount {
  /** Bazangizdagi buyurtma id'si. */
  id: string | number;
  /** Kutilayotgan summa TIYINDA (1 so'm = 100 tiyin). */
  amount: number;
  /** Buyurtma hali to'lov kutyaptimi? */
  payable: boolean;
  /** `onConfirmed()` ichida kerak bo'ladigan hamma narsa. */
  extra?: Record<string, unknown>;
}

/** Uzum Bank tranzaksiya yozuvi — protokol talab qiladigan kundalik yozuvi. */
export interface UzumTransaction {
  transId: string; // Uzum Bank bergan UUID
  ourId: string;
  params: Record<string, unknown>; // foydalanuvchi kiritgan hisob maydonlari
  amount: number;
  state: UzumStateValue;
  createTime: number;
  confirmTime: number;
  reverseTime: number;
  accountExtra?: Record<string, unknown>;
}

export interface UzumOrdersAdapter {
  // --- Biznes: siz o'zgartirasiz -------------------------------------------

  /** Uzum Bank yuborgan `params` maydonlari bo'yicha buyurtmani topadi. */
  findAccount(params: Record<string, unknown>): Promise<UzumAccount | null>;

  /**
   * To'lov tasdiqlangach BIR MARTA chaqiriladi. Mahsulotni shu yerda bering.
   *
   * DIQQAT: bu chaqirilganda pul ALLAQACHON yechilgan (Uzum Bank /confirm
   * dan oldin pulni yechadi). Xato bersa ham pul qaytarilmaydi.
   */
  onConfirmed(transaction: UzumTransaction): Promise<void>;

  /** Bekor qilinganda (yoki qaytarilganda) chaqiriladi. Ixtiyoriy. */
  onReversed(transaction: UzumTransaction): Promise<void>;

  /** Tasdiqlangan (CONFIRMED) tranzaksiyani bekor qilish mumkinmi? */
  canReverse(transaction: UzumTransaction): Promise<boolean>;

  // --- Tranzaksiya kundaligi: Uzum Bank talab qiladi -----------------------

  getTransaction(transId: string): Promise<UzumTransaction | null>;

  /** Shu hisob uchun hali bekor qilinmagan tranzaksiya bormi? */
  getActiveTransactionForAccount(
    params: Record<string, unknown>,
  ): Promise<UzumTransaction | null>;

  /** Yangi tranzaksiya yozuvini yaratadi (state=CREATED). */
  createTransaction(
    transId: string,
    amount: number,
    params: Record<string, unknown>,
  ): Promise<UzumTransaction>;

  /**
   * Tranzaksiyani "tasdiqlangan" qiladi (CREATED -> CONFIRMED).
   *
   * Faqat HAQIQATAN o'tkazgan chaqiruv yozuvni qaytaradi — aks holda
   * `null`. Bazangizda atomar `UPDATE ... WHERE state='CREATED'` bilan
   * qiling.
   */
  markConfirmed(transId: string): Promise<UzumTransaction | null>;

  /**
   * Tranzaksiyani bekor qiladi (CREATED yoki CONFIRMED -> REVERSED).
   * Allaqachon REVERSED bo'lsa `null`.
   */
  markReversed(transId: string): Promise<UzumTransaction | null>;
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
const demoTransactions = new Map<string, UzumTransaction>();

export const orders: UzumOrdersAdapter = {
  async findAccount(params) {
    const orderId = params.account;
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

  async onConfirmed(transaction) {
    const orderId = transaction.params.account;
    const order = demoOrders.get(String(orderId));
    if (order) order.status = "paid";

    console.log("[uzum] TASDIQLANDI", {
      orderId,
      amountTiyin: transaction.amount,
      transId: transaction.transId,
    });
  },

  async onReversed(transaction) {
    const orderId = transaction.params.account;
    const order = demoOrders.get(String(orderId));
    if (order) order.status = "cancelled";

    console.log("[uzum] BEKOR QILINDI", { orderId, transId: transaction.transId });
  },

  async canReverse() {
    return true;
  },

  async getTransaction(transId) {
    return demoTransactions.get(transId) ?? null;
  },

  async getActiveTransactionForAccount(params) {
    const orderId = params.account;
    for (const tx of demoTransactions.values()) {
      if (
        tx.params.account === orderId &&
        (tx.state === UzumState.CREATED || tx.state === UzumState.CONFIRMED)
      ) {
        return tx;
      }
    }
    return null;
  },

  async createTransaction(transId, amount, params) {
    const tx: UzumTransaction = {
      transId,
      ourId: transId,
      params,
      amount,
      state: UzumState.CREATED,
      createTime: Date.now(),
      confirmTime: 0,
      reverseTime: 0,
    };
    demoTransactions.set(transId, tx);
    return tx;
  },

  async markConfirmed(transId) {
    const tx = demoTransactions.get(transId);
    if (!tx || tx.state !== UzumState.CREATED) return null;

    tx.state = UzumState.CONFIRMED;
    tx.confirmTime = Date.now();
    return tx;
  },

  async markReversed(transId) {
    const tx = demoTransactions.get(transId);
    if (!tx || tx.state === UzumState.REVERSED) return null;

    tx.state = UzumState.REVERSED;
    tx.reverseTime = Date.now();
    return tx;
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
//   export const orders: UzumOrdersAdapter = {
//     async findAccount(params) {
//       const o = await prisma.order.findUnique({ where: { id: String(params.account) } });
//       if (!o) return null;
//       return {
//         id: o.id,
//         amount: o.priceTiyin,             // bazada TIYINDA saqlang
//         payable: o.status === "PENDING",
//         extra: { userId: o.userId },
//       };
//     },
//
//     async onConfirmed(tx) {
//       await prisma.order.update({
//         where: { id: String(tx.params.account) },
//         data: { status: "PAID" },
//       });
//     },
//
//     async onReversed(tx) {
//       await prisma.order.update({
//         where: { id: String(tx.params.account) },
//         data: { status: "CANCELLED" },
//       });
//     },
//
//     async canReverse() { return true; },
//
//     async getTransaction(transId) {
//       const t = await prisma.uzumTransaction.findUnique({ where: { transId } });
//       return t ? mapRow(t) : null;
//     },
//
//     async markConfirmed(transId) {
//       // updateMany + where.state — ATOMAR. `update` emas!
//       const { count } = await prisma.uzumTransaction.updateMany({
//         where: { transId, state: "CREATED" },
//         data: { state: "CONFIRMED", confirmTime: Date.now() },
//       });
//       if (count === 0) return null;
//       return this.getTransaction(transId);
//     },
//
//     // ... markReversed, createTransaction, getActiveTransactionForAccount
//     // — xuddi shu naqsh bilan.
//   };
//
// =============================================================================
