/**
 * Next.js (App Router) ga ulash.
 *
 * `payme-payment/` papkasini loyihangizga ko'chiring (masalan
 * `src/payme-payment/`), keyin ikkita fayl yarating.
 *
 * ─────────────────────────────────────────────────────────────────────────────
 *  src/app/api/payme/route.ts
 * ─────────────────────────────────────────────────────────────────────────────
 *
 *     import { NextResponse } from "next/server";
 *     import { handleRequest } from "@/payme-payment";
 *
 *     // MAJBURIY: Basic Auth tekshiruvi `node:crypto` bilan ishlaydi.
 *     // Edge runtime'da timingSafeEqual yo'q.
 *     export const runtime = "nodejs";
 *     export const dynamic = "force-dynamic";
 *
 *     export async function POST(req: Request) {
 *       const body = await req.json();
 *       const authorization = req.headers.get("authorization");
 *       return NextResponse.json(await handleRequest(body, authorization));
 *     }
 *
 * Click'dan farqli — Payme'da IKKITA endpoint (prepare/complete) emas,
 * BITTA bor. Payme "method" maydoniga qarab qaysi amalni bajarishni o'zi
 * aytadi.
 *
 * ─────────────────────────────────────────────────────────────────────────────
 *  DIQQAT — middleware
 * ─────────────────────────────────────────────────────────────────────────────
 *
 * So'rov Payme SERVERIDAN keladi — u login qila olmaydi va cookie
 * yubormaydi. `middleware.ts` da auth tekshiruvi bo'lsa, `/api/payme` ni
 * istisno qiling:
 *
 *     export const config = {
 *       matcher: ["/((?!api/payme|_next/static|_next/image).*)"],
 *     };
 *
 * ─────────────────────────────────────────────────────────────────────────────
 *  Click kabinetiga yoziladigan manzil
 * ─────────────────────────────────────────────────────────────────────────────
 *
 *     https://sizning-domen.uz/api/payme
 */

// --- To'lov havolasini yasash (Server Action yoki route ichida) --------------

import { checkoutUrl, somToTiyin } from "../payme-payment/index.js";

/**
 * Namuna: buyurtma yaratib, Payme havolasini qaytaradi.
 */
export async function createCheckoutUrl(orderId: string, priceSom: number) {
  // await prisma.order.update({ where: { id: orderId }, data: { ... } });

  return checkoutUrl({ order_id: orderId }, somToTiyin(priceSom));
}
