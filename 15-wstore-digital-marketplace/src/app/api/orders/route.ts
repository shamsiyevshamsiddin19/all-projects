import { NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { logError } from "@/lib/errorLog";
import { rateLimit, clientIp } from "@/lib/rateLimit";
import {
  CLICK_PREFIX_PURCHASE,
  buildClickPaymentUrl,
  usdToSom,
} from "@/lib/click";

const APP_URL = process.env.APP_URL || "https://wstore.uz";

// POST /api/orders — mahsulotni onlayn (Click) sotib olishni boshlaydi.
// Body: { productId }. Javob: { url } — Click to'lov sahifasiga yo'naltirish.
export async function POST(req: Request) {
  const session = await auth().catch(() => null);
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Tizimga kiring" }, { status: 401 });
  }

  if (!rateLimit(`orders:${clientIp(req)}`, 20, 60_000)) {
    return NextResponse.json(
      { error: "Juda ko'p so'rov. Birozdan so'ng qayta urinib ko'ring." },
      { status: 429 },
    );
  }

  const body = await req.json().catch(() => null);
  const productId = body?.productId as string | undefined;
  if (!productId) {
    return NextResponse.json({ error: "productId majburiy" }, { status: 400 });
  }

  const product = await prisma.product.findUnique({ where: { id: productId } });
  if (!product || product.status !== "ACTIVE") {
    return NextResponse.json({ error: "Mahsulot topilmadi" }, { status: 404 });
  }
  if (product.sellerId === session.user.id) {
    return NextResponse.json(
      { error: "O'z mahsulotingizni sotib ololmaysiz" },
      { status: 400 },
    );
  }

  try {
    const amountSom = usdToSom(Number(product.price));

    const order = await prisma.order.create({
      data: {
        buyerId: session.user.id,
        productId: product.id,
        amount: amountSom,
        status: "PENDING",
        provider: "click",
      },
    });

    const ct = await prisma.clickTransaction.create({
      data: {
        kind: "PURCHASE",
        orderId: order.id,
        amount: amountSom,
        status: "PENDING",
      },
    });
    const merchantTransId = `${CLICK_PREFIX_PURCHASE}${ct.id}`;
    await prisma.clickTransaction.update({
      where: { id: ct.id },
      data: { merchantTransId },
    });

    const returnUrl = `${APP_URL}/order/${order.id}`;
    const url = buildClickPaymentUrl(merchantTransId, amountSom, returnUrl);

    return NextResponse.json({ url, orderId: order.id });
  } catch (e) {
    await logError(e, "POST /api/orders");
    return NextResponse.json({ error: "Server xatosi" }, { status: 500 });
  }
}
