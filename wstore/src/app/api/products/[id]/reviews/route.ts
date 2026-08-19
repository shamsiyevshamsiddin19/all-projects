import { NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";

// GET /api/products/[id]/reviews — ommaviy izohlar ro'yxati.
export async function GET(
  _req: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  try {
    const reviews = await prisma.review.findMany({
      where: { productId: id },
      orderBy: { createdAt: "desc" },
      include: { user: { select: { name: true, image: true } } },
    });
    return NextResponse.json(
      reviews.map((r) => ({
        id: r.id,
        rating: r.rating,
        comment: r.comment,
        userName: r.user.name,
        userImage: r.user.image,
        createdAt: r.createdAt,
      })),
    );
  } catch {
    return NextResponse.json([]);
  }
}

// POST /api/products/[id]/reviews — izoh qoldirish/yangilash (Google kirish shart).
export async function POST(
  req: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const session = await auth().catch(() => null);
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Tizimga kiring" }, { status: 401 });
  }

  const { id } = await params;
  const body = await req.json().catch(() => null);
  const rating = Math.round(Number(body?.rating));
  const comment = String(body?.comment ?? "").trim();

  if (!rating || rating < 1 || rating > 5) {
    return NextResponse.json({ error: "Reyting 1-5 bo'lishi kerak" }, { status: 400 });
  }
  if (comment.length < 2) {
    return NextResponse.json({ error: "Izoh juda qisqa" }, { status: 400 });
  }

  try {
    const product = await prisma.product.findUnique({ where: { id } });
    if (!product) {
      return NextResponse.json({ error: "Mahsulot topilmadi" }, { status: 404 });
    }

    await prisma.review.upsert({
      where: { productId_userId: { productId: id, userId: session.user.id } },
      update: { rating, comment },
      create: { productId: id, userId: session.user.id, rating, comment },
    });

    // Mahsulot reytingini qayta hisoblaymiz (o'rtacha).
    const agg = await prisma.review.aggregate({
      where: { productId: id },
      _avg: { rating: true },
    });
    await prisma.product.update({
      where: { id },
      data: { rating: agg._avg.rating ?? 0 },
    });

    return NextResponse.json({ ok: true });
  } catch (e) {
    console.error("review error", e);
    return NextResponse.json({ error: "Server xatosi" }, { status: 500 });
  }
}
