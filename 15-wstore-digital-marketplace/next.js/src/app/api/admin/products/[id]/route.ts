import { NextResponse } from "next/server";
import { requireAdmin } from "@/lib/admin";
import { prisma } from "@/lib/prisma";

// DELETE /api/admin/products/[id] — mahsulotni butunlay o'chirish (admin).
export async function DELETE(
  _req: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const admin = await requireAdmin();
  if (!admin) {
    return NextResponse.json({ error: "Ruxsat yo'q" }, { status: 403 });
  }

  const { id } = await params;
  try {
    // Bog'liq yozuvlarni avval tozalaymiz (FK).
    await prisma.$transaction([
      prisma.review.deleteMany({ where: { productId: id } }),
      prisma.wishlist.deleteMany({ where: { productId: id } }),
      prisma.report.deleteMany({ where: { productId: id } }),
      prisma.clickTransaction.deleteMany({ where: { productId: id } }),
      prisma.order.deleteMany({ where: { productId: id } }),
      prisma.product.delete({ where: { id } }),
    ]);
    return NextResponse.json({ ok: true });
  } catch (e) {
    console.error("admin delete error", e);
    return NextResponse.json({ error: "Server xatosi" }, { status: 500 });
  }
}
