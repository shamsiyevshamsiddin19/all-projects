/**
 * Next.js (App Router) ga ulash.
 *
 * `uzum-payment/` papkasini loyihangizga ko'chiring (masalan
 * `src/uzum-payment/`), keyin BESHTA route fayli yarating.
 *
 * ─────────────────────────────────────────────────────────────────────────────
 *  src/app/api/uzum/check/route.ts
 * ─────────────────────────────────────────────────────────────────────────────
 *
 *     import { NextResponse } from "next/server";
 *     import { handleCheck } from "@/uzum-payment";
 *
 *     // MAJBURIY: Basic Auth tekshiruvi `node:crypto` bilan ishlaydi.
 *     export const runtime = "nodejs";
 *     export const dynamic = "force-dynamic";
 *
 *     export async function POST(req: Request) {
 *       const body = await req.json();
 *       const [status, result] = await handleCheck(body, req.headers.get("authorization"));
 *       return NextResponse.json(result, { status });
 *     }
 *
 * Xuddi shu shaklda:
 *     src/app/api/uzum/create/route.ts    -> handleCreate
 *     src/app/api/uzum/confirm/route.ts   -> handleConfirm
 *     src/app/api/uzum/reverse/route.ts   -> handleReverse
 *     src/app/api/uzum/status/route.ts    -> handleStatus
 *
 * ─────────────────────────────────────────────────────────────────────────────
 *  DIQQAT — middleware
 * ─────────────────────────────────────────────────────────────────────────────
 *
 * So'rovlar Uzum Bank SERVERIDAN keladi. `middleware.ts` da auth bo'lsa,
 * `/api/uzum/*` ni istisno qiling:
 *
 *     export const config = {
 *       matcher: ["/((?!api/uzum|_next/static|_next/image).*)"],
 *     };
 *
 * ─────────────────────────────────────────────────────────────────────────────
 *  Kabinetga yoziladigan bazaviy manzil
 * ─────────────────────────────────────────────────────────────────────────────
 *
 *     https://sizning-domen.uz/api/uzum
 *
 * DIQQAT: Uzum Bank'da Click/Payme'dagidek "to'lov havolasi" YO'Q.
 * Foydalanuvchi Uzum Bank ilovasida xizmatingizni `service_id` orqali
 * qidirib topadi va to'lovni O'SHA YERDA boshlaydi.
 */

export {};
