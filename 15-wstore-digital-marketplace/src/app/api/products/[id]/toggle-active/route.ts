import { NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";

// POST /api/products/[id]/toggle-active — sotuvchi mahsulotni vaqtincha
// ko'rinishdan yashiradi (ACTIVE -> PAUSED) yoki qayta yoqadi (PAUSED -> ACTIVE).
// Moderatsiyaga qaytarilmaydi — REJECTED holatidan farqli.
export async function POST(
  _req: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const session = await auth().catch(() => null);
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Tizimga kiring" }, { status: 401 });
  }

  const { id } = await params;
  const existing = await prisma.product.findUnique({ where: { id } });
  const isOwner = existing?.sellerId === session.user.id;
  const isAdmin = session.user.role === "ADMIN";
  if (!existing || (!isOwner && !isAdmin)) {
    return NextResponse.json({ error: "Topilmadi" }, { status: 404 });
  }
  if (existing.status !== "ACTIVE" && existing.status !== "PAUSED") {
    return NextResponse.json(
      { error: "Faqat faol yoki to'xtatilgan mahsulot uchun" },
      { status: 400 },
    );
  }

  try {
    const next = existing.status === "ACTIVE" ? "PAUSED" : "ACTIVE";
    const product = await prisma.product.update({
      where: { id },
      data: { status: next },
    });
    return NextResponse.json({ status: product.status });
  } catch (e) {
    console.error("toggle-active error", e);
    return NextResponse.json({ error: "Server xatosi" }, { status: 500 });
  }
}
