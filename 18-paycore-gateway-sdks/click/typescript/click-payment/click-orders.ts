/**
 * =============================================================================
 *   SIZ FAQAT SHU FAYLNI TAHRIRLAYSIZ
 * =============================================================================
 *
 * Bu fayl Click integratsiyasini SIZNING bazangiz bilan bog'laydi.
 * Qolgan fayllarga (click-prepare.ts, click-complete.ts, click-signature.ts,
 * click-config.ts) tegish shart emas — ular o'zgarmaydi.
 *
 * Click integratsiyasi sizning tizimingiz haqida atigi 5 narsani bilishi kerak
 * — quyidagi `ClickOrdersAdapter` interfeysi. TypeScript ularni to'g'ri
 * yozganingizni o'zi tekshirib beradi.
 *
 *     BAZA:
 *       1. findOrder(merchantTransId)          -> buyurtmani toping
 *       2. markPaid(order, clickTransId)       -> "to'landi" deb belgilang
 *       3. markCancelled(order, clickTransId)  -> "bekor qilindi" deb belgilang
 *
 *     HODISALAR:
 *       4. onPaid(order)      -> to'lov o'tgach mahsulotni bering
 *       5. onCancelled(order) -> to'lov bekor bo'lganda (ixtiyoriy)
 *
 * Hozir bu yerda XOTIRADAGI NAMUNA turibdi — klon qilib darrov sinab
 * ko'rishingiz uchun. U server qayta ishga tushsa yo'qoladi va bir nechta
 * instansiyada ishlamaydi, ya'ni ISHLAB CHIQARISHGA YAROQSIZ.
 *
 * Prisma, Drizzle va xom SQL (pg) uchun tayyor namunalar shu faylning
 * oxirida (izohda) berilgan — nusxa olib qo'yavering.
 * =============================================================================
 */

/** Buyurtmaning holati. Bazangizda boshqacha nomlangan bo'lsa, findOrder ichida shu uchtasiga o'giring. */
export type ClickOrderStatus = "pending" | "paid" | "cancelled";

export interface ClickOrder {
  /**
   * Bazangizdagi raqamli id. Aynan shu qiymat Click'ga `merchant_prepare_id`
   * bo'lib ketadi va complete'da qaytib keladi.
   */
  id: number;

  /**
   * To'lov havolasida `transaction_param` bo'lib ketadigan satr
   * (masalan "ORD42"). Bazangizda UNIKAL bo'lishi SHART.
   */
  merchantTransId: string;

  /**
   * Kutilayotgan summa (so'mda). Click yuborgan summa shu bilan
   * solishtiriladi — mos kelmasa to'lov rad etiladi.
   *
   * Prisma `Decimal` qaytarsa — `Number(ct.amount)` qiling.
   */
  amount: number;

  status: ClickOrderStatus;

  /**
   * Sizga kerak bo'ladigan ixtiyoriy ma'lumot (userId, chatId, productId...).
   * Click bu bilan ishlamaydi — u faqat onPaid() ichida sizga kerak bo'ladi.
   */
  extra?: Record<string, unknown>;
}

export interface ClickOrdersAdapter {
  /** Buyurtmani `merchantTransId` bo'yicha topadi. Topilmasa null. */
  findOrder(merchantTransId: string): Promise<ClickOrder | null>;

  /**
   * Buyurtmani "to'langan" deb belgilaydi.
   *
   * ┌───────────────────────────────────────────────────────────────────────┐
   * │  DIQQAT — BU YERDA XATO QILISH OSON:                                  │
   * │                                                                       │
   * │  Faqat SHU chaqiruv holatni pending -> paid o'tkazgan bo'lsa `true`   │
   * │  qaytaring. Allaqachon to'langan bo'lsa `false` qaytaring.            │
   * │                                                                       │
   * │  Nega? Click javobni ololmasa complete'ni QAYTA yuboradi (ba'zan bir  │
   * │  vaqtda). `true` qaytgan chaqiruvda onPaid() ishlaydi. Agar har safar │
   * │  `true` qaytarsangiz — mahsulot ikki marta beriladi.                  │
   * │                                                                       │
   * │  "Node bir oqimli-ku, poyga bo'lmaydi" deb o'ylamang: Vercel/PM2/k8s  │
   * │  da bir nechta instansiya parallel ishlaydi va `await` orasida boshqa │
   * │  so'rov kirib keladi. Shartni BAZANING O'ZIGA qo'ying:                │
   * │      UPDATE ... SET status='paid' WHERE id=? AND status='pending'     │
   * │  va o'zgargan qatorlar sonini qaytaring.                              │
   * └───────────────────────────────────────────────────────────────────────┘
   */
  markPaid(order: ClickOrder, clickTransId: string): Promise<boolean>;

  /** Buyurtmani "bekor qilingan" deb belgilaydi (faqat u hali pending bo'lsa). */
  markCancelled(order: ClickOrder, clickTransId: string): Promise<void>;

  /**
   * To'lov tasdiqlangach BIR MARTA chaqiriladi. Mahsulotni shu yerda bering.
   *
   * Ikki muhim eslatma:
   *
   *  1. Bu yerda UZOQ ish qilmang — Click javobni kutib turadi va kechiksangiz
   *     so'rovni qayta yuboradi. Og'ir ishni navbatga qo'ying.
   *
   *  2. Bu funksiya xato bersa, to'lov baribir "paid" bo'lib qoladi (pul
   *     yechilgan-ku) va xato logga yoziladi. Click'ga xato qaytarish foyda
   *     bermaydi: u qayta urganda buyurtma allaqachon "paid" bo'lgani uchun
   *     bu funksiya qayta ishlamaydi. Shuning uchun loglarni kuzatib boring.
   */
  onPaid(order: ClickOrder): Promise<void>;

  /** To'lov bekor qilinganda chaqiriladi (ixtiyoriy — bo'sh qoldirsangiz ham bo'ladi). */
  onCancelled(order: ClickOrder): Promise<void>;
}

// =============================================================================
//   NAMUNA — xotirada saqlaydigan adapter.
//   O'z bazangizga o'tganingizda butun shu blokni almashtiring.
// =============================================================================

interface DemoRow {
  id: number;
  merchantTransId: string;
  amount: number;
  status: ClickOrderStatus;
  clickTransId: string | null;
  paidAt: Date | null;
  extra: Record<string, unknown>;
}

const demoRows = new Map<string, DemoRow>();
let demoNextId = 1;

export const orders: ClickOrdersAdapter = {
  async findOrder(merchantTransId: string): Promise<ClickOrder | null> {
    const row = demoRows.get(merchantTransId);
    if (!row) return null;

    return {
      id: row.id,
      merchantTransId: row.merchantTransId,
      amount: row.amount,
      status: row.status,
      extra: row.extra,
    };
  },

  async markPaid(order: ClickOrder, clickTransId: string): Promise<boolean> {
    const row = demoRows.get(order.merchantTransId);

    // Namunada baza yo'q, shuning uchun shartni shu yerda tekshiramiz.
    // HAQIQIY bazada buni SQL'ning o'ziga qo'ying (yuqoridagi izohga qarang).
    if (!row || row.status !== "pending") return false;

    row.status = "paid";
    row.clickTransId = clickTransId;
    row.paidAt = new Date();

    return true;
  },

  async markCancelled(order: ClickOrder, clickTransId: string): Promise<void> {
    const row = demoRows.get(order.merchantTransId);
    if (!row || row.status !== "pending") return;

    row.status = "cancelled";
    row.clickTransId = clickTransId;
    row.paidAt = null;
  },

  async onPaid(order: ClickOrder): Promise<void> {
    console.log("[click] TO'LANDI", {
      merchantTransId: order.merchantTransId,
      amount: order.amount,
      extra: order.extra,
    });
  },

  async onCancelled(order: ClickOrder): Promise<void> {
    console.log("[click] BEKOR QILINDI", {
      merchantTransId: order.merchantTransId,
    });
  },
};

/**
 * Namuna uchun buyurtma yaratadi.
 *
 * O'z tizimingizda buyurtma allaqachon bazangizda bo'ladi — bu funksiya
 * kerak emas. Faqat `merchantTransId` ustunini qo'shib qo'ying.
 */
export async function demoCreateOrder(
  merchantTransId: string,
  amount: number,
  extra: Record<string, unknown> = {},
): Promise<ClickOrder> {
  const row: DemoRow = {
    id: demoNextId++,
    merchantTransId,
    amount,
    status: "pending",
    clickTransId: null,
    paidAt: null,
    extra,
  };

  demoRows.set(merchantTransId, row);

  return {
    id: row.id,
    merchantTransId: row.merchantTransId,
    amount: row.amount,
    status: row.status,
    extra: row.extra,
  };
}

/** Testlar uchun — namuna ma'lumotlarini tozalaydi. */
export function demoReset(): void {
  demoRows.clear();
  demoNextId = 1;
}

// =============================================================================
//   O'Z BAZANGIZ UCHUN NAMUNALAR — nusxa oling va yuqoridagi `orders`
//   obyekti o'rniga qo'ying.
// =============================================================================
//
// ─── Prisma ──────────────────────────────────────────────────────────────────
//
//   import { prisma } from "@/lib/prisma";
//
//   export const orders: ClickOrdersAdapter = {
//     async findOrder(merchantTransId) {
//       const o = await prisma.order.findUnique({ where: { merchantTransId } });
//       if (!o) return null;
//
//       // Bazangizdagi holatni bizning uchta holatga o'giring:
//       const statusMap: Record<string, ClickOrderStatus> = {
//         NEW: "pending",
//         PENDING: "pending",
//         PAID: "paid",
//         DELIVERED: "paid",     // allaqachon bajarilgan
//       };
//
//       return {
//         id: o.id,
//         merchantTransId: o.merchantTransId!,
//         amount: Number(o.amount),          // Prisma Decimal -> number
//         status: statusMap[o.status] ?? "cancelled",
//         extra: { userId: o.userId, productId: o.productId },
//       };
//     },
//
//     async markPaid(order, clickTransId) {
//       // updateMany + where.status — ATOMAR. `update` emas!
//       const { count } = await prisma.order.updateMany({
//         where: { id: order.id, status: "PENDING" },
//         data: { status: "PAID", clickTransId, paidAt: new Date() },
//       });
//       return count > 0;
//     },
//
//     async markCancelled(order, clickTransId) {
//       await prisma.order.updateMany({
//         where: { id: order.id, status: "PENDING" },
//         data: { status: "CANCELLED", clickTransId },
//       });
//     },
//
//     async onPaid(order) {
//       // Mahsulotni shu yerda bering. Bir nechta yozuvni o'zgartirsangiz
//       // tranzaksiyaga o'rang:
//       await prisma.$transaction(async (tx) => {
//         await tx.product.update({
//           where: { id: order.extra!.productId as string },
//           data: { salesCount: { increment: 1 } },
//         });
//       });
//     },
//
//     async onCancelled(order) {},
//   };
//
//
// ─── Drizzle ─────────────────────────────────────────────────────────────────
//
//   async markPaid(order, clickTransId) {
//     const result = await db
//       .update(ordersTable)
//       .set({ status: "paid", clickTransId, paidAt: new Date() })
//       .where(and(eq(ordersTable.id, order.id), eq(ordersTable.status, "pending")));
//
//     return (result.rowCount ?? 0) > 0;   // PostgreSQL
//     // MySQL/SQLite'da: result.rowsAffected > 0
//   }
//
//
// ─── Xom SQL (pg) ────────────────────────────────────────────────────────────
//
//   async markPaid(order, clickTransId) {
//     const res = await pool.query(
//       `UPDATE orders SET status='paid', click_trans_id=$1, paid_at=NOW()
//         WHERE id=$2 AND status='pending'`,
//       [clickTransId, order.id],
//     );
//     return (res.rowCount ?? 0) > 0;
//   }
//
// =============================================================================
