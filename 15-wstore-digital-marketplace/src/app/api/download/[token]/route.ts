import { NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { readStoredFile } from "@/lib/r2";

// GET /api/download/<token>
// Faqat: to'langan + shu foydalanuvchiga tegishli buyurtma bo'lsa,
// faylni serverning o'z diskidan to'g'ridan-to'g'ri javob sifatida beradi.
export async function GET(
  _req: Request,
  { params }: { params: Promise<{ token: string }> },
) {
  const { token } = await params;
  const session = await auth().catch(() => null);
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Tizimga kiring" }, { status: 401 });
  }

  try {
    const order = await prisma.order.findFirst({
      where: { downloadToken: token, buyerId: session.user.id },
      include: { product: true },
    });

    if (!order) {
      return NextResponse.json({ error: "Buyurtma topilmadi" }, { status: 404 });
    }
    if (order.status !== "PAID") {
      return NextResponse.json(
        { error: "Bu buyurtma hali to'lanmagan" },
        { status: 403 },
      );
    }

    const buffer = await readStoredFile(order.product.fileKey);
    return new NextResponse(new Uint8Array(buffer), {
      headers: {
        "Content-Type": "application/zip",
        "Content-Disposition": `attachment; filename="${order.product.slug}.zip"`,
      },
    });
  } catch (e) {
    console.error("download error", e);
    return NextResponse.json(
      { error: "Fayl topilmadi yoki server xatosi" },
      { status: 500 },
    );
  }
}
