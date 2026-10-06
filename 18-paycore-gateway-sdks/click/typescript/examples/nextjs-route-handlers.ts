/**
 * Next.js (App Router) ga ulash.
 *
 * `click-payment/` papkasini loyihangizga ko'chiring (masalan `src/click-payment/`),
 * keyin ikkita route fayli yarating.
 *
 * ─────────────────────────────────────────────────────────────────────────────
 *  src/app/api/click/prepare/route.ts
 * ─────────────────────────────────────────────────────────────────────────────
 *
 *     import { NextResponse } from "next/server";
 *     import { handlePrepare, readRequestData } from "@/click-payment";
 *
 *     // MAJBURIY: imzo md5 bilan hisoblanadi, md5 esa `node:crypto` da.
 *     // Edge runtime'da Web Crypto md5 ni qo'llab-quvvatlamaydi.
 *     export const runtime = "nodejs";
 *
 *     // To'lov callback'i hech qachon keshlanmasin.
 *     export const dynamic = "force-dynamic";
 *
 *     export async function POST(req: Request) {
 *       const data = await readRequestData(req);
 *       return NextResponse.json(await handlePrepare(data));
 *     }
 *
 * ─────────────────────────────────────────────────────────────────────────────
 *  src/app/api/click/complete/route.ts
 * ─────────────────────────────────────────────────────────────────────────────
 *
 *     import { NextResponse } from "next/server";
 *     import { handleComplete, readRequestData } from "@/click-payment";
 *
 *     export const runtime = "nodejs";
 *     export const dynamic = "force-dynamic";
 *
 *     export async function POST(req: Request) {
 *       const data = await readRequestData(req);
 *       return NextResponse.json(await handleComplete(data));
 *     }
 *
 * ─────────────────────────────────────────────────────────────────────────────
 *  DIQQAT — middleware
 * ─────────────────────────────────────────────────────────────────────────────
 *
 * So'rov Click SERVERIDAN keladi — u login qila olmaydi va cookie yubormaydi.
 * `middleware.ts` da auth tekshiruvi bo'lsa, `/api/click/*` ni istisno qiling:
 *
 *     export const config = {
 *       matcher: ["/((?!api/click|_next/static|_next/image).*)"],
 *     };
 *
 * Aks holda Click 307/401 oladi va to'lovlar ishlamaydi.
 *
 * ─────────────────────────────────────────────────────────────────────────────
 *  Click kabinetiga yoziladigan manzillar
 * ─────────────────────────────────────────────────────────────────────────────
 *
 *     Prepare URL:   https://sizning-domen.uz/api/click/prepare
 *     Complete URL:  https://sizning-domen.uz/api/click/complete
 */

// --- To'lov havolasini yasash (Server Action yoki route ichida) --------------

import { paymentUrl } from "../click-payment/index.js";

/**
 * Namuna: buyurtma yaratib, Click havolasini qaytaradi.
 *
 * Haqiqiy loyihada `prisma.order.create(...)` bilan buyurtma ochasiz va
 * unga unikal `merchantTransId` berasiz.
 */
export async function createCheckoutUrl(orderId: number, priceSom: number) {
  // merchantTransId unikal bo'lishi SHART. Prefiks bir nechta to'lov turini
  // ajratish uchun qulay: ORD42 — xarid, SUB7 — obuna.
  const merchantTransId = `ORD${orderId}`;

  // await prisma.order.update({
  //   where: { id: orderId },
  //   data: { merchantTransId },
  // });

  return paymentUrl(merchantTransId, priceSom);
}
