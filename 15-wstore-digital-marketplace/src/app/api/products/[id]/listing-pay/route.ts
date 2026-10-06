import { NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import {
  CLICK_PREFIX_LISTING,
  LISTING_FEE_SOM,
  buildClickPaymentUrl,
} from "@/lib/click";

const APP_URL = process.env.APP_URL || "https://wstore.uz";

// POST /api/products/[id]/listing-pay — sotuvchi loyihasini e'lon qilish uchun
// 5000 so'm Click to'lovini boshlaydi. Faqat DRAFT holatidagi o'z loyihasi uchun.
export async function POST(
  _req: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const session = await auth().catch(() => null);
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Tizimga kiring" }, { status: 401 });
  }

  const { id } = await params;
  const product = await prisma.product.findUnique({ where: { id } });
  if (!product || product.sellerId !== session.user.id) {
    return NextResponse.json({ error: "Topilmadi" }, { status: 404 });
  }
  if (product.status !== "DRAFT") {
    return NextResponse.json(
      { error: "Bu loyiha uchun e'lon to'lovi kerak emas" },
      { status: 400 },
    );
  }

  try {
    const ct = await prisma.clickTransaction.create({
      data: {
        kind: "LISTING",
        productId: product.id,
        amount: LISTING_FEE_SOM,
        status: "PENDING",
      },
    });
    const merchantTransId = `${CLICK_PREFIX_LISTING}${ct.id}`;
    await prisma.clickTransaction.update({
      where: { id: ct.id },
      data: { merchantTransId },
    });

    const returnUrl = `${APP_URL}/seller`;
    const url = buildClickPaymentUrl(merchantTransId, LISTING_FEE_SOM, returnUrl);

    return NextResponse.json({ url });
  } catch (e) {
    console.error("listing-pay error", e);
    return NextResponse.json({ error: "Server xatosi" }, { status: 500 });
  }
}
