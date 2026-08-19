import { NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { logError } from "@/lib/errorLog";
import { rateLimit, clientIp } from "@/lib/rateLimit";

// POST /api/reports — xaridor mahsulot/sotuvchi ustidan shikoyat qiladi.
export async function POST(req: Request) {
  const session = await auth().catch(() => null);
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Tizimga kiring" }, { status: 401 });
  }

  if (!rateLimit(`reports:${clientIp(req)}`, 10, 60_000)) {
    return NextResponse.json(
      { error: "Juda ko'p so'rov. Birozdan so'ng qayta urinib ko'ring." },
      { status: 429 },
    );
  }

  const body = await req.json().catch(() => null);
  if (!body?.productId || !body?.reason) {
    return NextResponse.json(
      { error: "productId va reason majburiy" },
      { status: 400 },
    );
  }

  try {
    await prisma.report.create({
      data: {
        productId: String(body.productId),
        reporterId: session.user.id,
        reason: String(body.reason).slice(0, 120),
        comment: body.comment ? String(body.comment).slice(0, 1000) : null,
      },
    });
    return NextResponse.json({ ok: true });
  } catch (e) {
    await logError(e, "POST /api/reports");
    return NextResponse.json({ error: "Server xatosi" }, { status: 500 });
  }
}
