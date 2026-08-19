import { NextResponse } from "next/server";
import { requireAdmin } from "@/lib/admin";
import { prisma } from "@/lib/prisma";
import { readStoredFile } from "@/lib/r2";

// GET /api/admin/products/[id]/file — moderatsiyadan oldin admin faylni
// diskdan to'g'ridan-to'g'ri tekshirib ko'radi (yangi tabda ochish uchun).
export async function GET(
  _req: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const admin = await requireAdmin();
  if (!admin) {
    return NextResponse.json({ error: "Ruxsat yo'q" }, { status: 403 });
  }

  const { id } = await params;
  const product = await prisma.product.findUnique({ where: { id } });
  if (!product) {
    return NextResponse.json({ error: "Topilmadi" }, { status: 404 });
  }

  try {
    const buffer = await readStoredFile(product.fileKey);
    return new NextResponse(new Uint8Array(buffer), {
      headers: {
        "Content-Type": "application/zip",
        "Content-Disposition": `attachment; filename="${product.slug}.zip"`,
      },
    });
  } catch (e) {
    console.error("admin file check error", e);
    return NextResponse.json(
      { error: "Fayl topilmadi (sotuvchi hali yuklamagan bo'lishi mumkin)" },
      { status: 404 },
    );
  }
}
