import { NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";

// GET /api/products/[id] — tahrirlash formasi uchun, faqat egasi.
export async function GET(
  _req: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const session = await auth().catch(() => null);
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Tizimga kiring" }, { status: 401 });
  }

  const { id } = await params;
  const product = await prisma.product.findUnique({
    where: { id },
    include: { category: true },
  });
  if (
    !product ||
    (product.sellerId !== session.user.id && session.user.role !== "ADMIN")
  ) {
    return NextResponse.json({ error: "Topilmadi" }, { status: 404 });
  }

  return NextResponse.json({
    id: product.id,
    title: product.title,
    slug: product.slug,
    description: product.description,
    price: Number(product.price),
    categorySlug: product.category.slug,
    subcategory: product.subcategory,
    techStack: product.techStack,
    features: product.features,
    coverImage: product.coverImage,
    screenshots: product.screenshots,
    demoUrl: product.demoUrl,
    telegramUsername: product.telegramUsername,
    status: product.status,
  });
}

// PATCH /api/products/[id] — sotuvchi o'z loyihasini tahrirlaydi.
export async function PATCH(
  req: Request,
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

  const body = await req.json().catch(() => null);
  if (!body?.title || !body?.price || !body?.categorySlug) {
    return NextResponse.json(
      { error: "title, price va categorySlug majburiy" },
      { status: 400 },
    );
  }

  try {
    const category = await prisma.category.findUnique({
      where: { slug: body.categorySlug },
    });
    if (!category) {
      return NextResponse.json({ error: "Bunday kategoriya yo'q" }, { status: 400 });
    }

    // Rad etilgan loyiha qayta tahrirlansa — moderatsiyaga qaytadi.
    // Boshqa holatlarda (DRAFT/PENDING/ACTIVE) holat o'zgarmaydi.
    const nextStatus = existing.status === "REJECTED" ? "PENDING" : existing.status;

    const product = await prisma.product.update({
      where: { id },
      data: {
        title: body.title,
        description: body.description ?? "",
        price: Number(body.price),
        categoryId: category.id,
        subcategory: category.slug === "website" ? (body.subcategory ?? null) : null,
        techStack: Array.isArray(body.techStack)
          ? body.techStack
          : String(body.techStack ?? "")
              .split(",")
              .map((t: string) => t.trim())
              .filter(Boolean),
        features: Array.isArray(body.features)
          ? body.features
          : String(body.features ?? "")
              .split("\n")
              .map((t: string) => t.trim())
              .filter(Boolean),
        coverImage: body.coverImage ?? "",
        ...(Array.isArray(body.screenshots) ? { screenshots: body.screenshots } : {}),
        demoUrl: body.demoUrl ?? null,
        telegramUsername: body.telegramUsername
          ? String(body.telegramUsername).replace(/^@/, "")
          : null,
        ...(body.fileKey ? { fileKey: String(body.fileKey) } : {}),
        status: nextStatus,
      },
    });

    return NextResponse.json({ id: product.id, slug: product.slug, status: product.status });
  } catch (e) {
    console.error("update product error", e);
    return NextResponse.json({ error: "Server xatosi" }, { status: 500 });
  }
}

// DELETE /api/products/[id] — sotuvchi o'z loyihasini butunlay o'chiradi.
export async function DELETE(
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
    console.error("delete product error", e);
    return NextResponse.json({ error: "Server xatosi" }, { status: 500 });
  }
}
