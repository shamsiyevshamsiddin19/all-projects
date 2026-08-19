import { NextResponse } from "next/server";
import { requireAdmin } from "@/lib/admin";
import { prisma } from "@/lib/prisma";

const ALLOWED = ["ACTIVE", "REJECTED", "PENDING", "DRAFT", "PAUSED"] as const;
type StatusVal = (typeof ALLOWED)[number];

// POST /api/admin/products/[id]/status — mahsulot holatini o'zgartirish (admin).
export async function POST(
  req: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const admin = await requireAdmin();
  if (!admin) {
    return NextResponse.json({ error: "Ruxsat yo'q" }, { status: 403 });
  }

  const { id } = await params;
  const body = await req.json().catch(() => null);
  const status = body?.status as StatusVal | undefined;
  if (!status || !ALLOWED.includes(status)) {
    return NextResponse.json({ error: "Noto'g'ri status" }, { status: 400 });
  }

  try {
    await prisma.product.update({ where: { id }, data: { status } });
    return NextResponse.json({ ok: true, status });
  } catch (e) {
    console.error("admin status error", e);
    return NextResponse.json({ error: "Server xatosi" }, { status: 500 });
  }
}
