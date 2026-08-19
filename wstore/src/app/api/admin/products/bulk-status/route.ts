import { NextResponse } from "next/server";
import { requireAdmin } from "@/lib/admin";
import { prisma } from "@/lib/prisma";
import { logError } from "@/lib/errorLog";

const ALLOWED = ["ACTIVE", "REJECTED", "PENDING", "DRAFT", "PAUSED"] as const;
type StatusVal = (typeof ALLOWED)[number];

// POST /api/admin/products/bulk-status — bir nechta mahsulotni birdan
// tasdiqlash/rad etish (admin).
export async function POST(req: Request) {
  const admin = await requireAdmin();
  if (!admin) {
    return NextResponse.json({ error: "Ruxsat yo'q" }, { status: 403 });
  }

  const body = await req.json().catch(() => null);
  const ids = Array.isArray(body?.ids) ? (body.ids as string[]) : [];
  const status = body?.status as StatusVal | undefined;
  if (ids.length === 0 || !status || !ALLOWED.includes(status)) {
    return NextResponse.json({ error: "Noto'g'ri so'rov" }, { status: 400 });
  }

  try {
    const result = await prisma.product.updateMany({
      where: { id: { in: ids } },
      data: { status },
    });
    return NextResponse.json({ ok: true, count: result.count });
  } catch (e) {
    await logError(e, "POST /api/admin/products/bulk-status");
    return NextResponse.json({ error: "Server xatosi" }, { status: 500 });
  }
}
