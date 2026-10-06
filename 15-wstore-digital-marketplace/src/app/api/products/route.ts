import { NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { logError } from "@/lib/errorLog";
import { rateLimit, clientIp } from "@/lib/rateLimit";

function slugify(s: string): string {
  return s
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, "")
    .trim()
    .replace(/\s+/g, "-")
    .slice(0, 60);
}

// POST /api/products — yangi mahsulot qo'shish (kirish talab qilinadi).
export async function POST(req: Request) {
  const session = await auth().catch(() => null);
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Tizimga kiring" }, { status: 401 });
  }

  if (!rateLimit(`products-create:${clientIp(req)}`, 10, 60_000)) {
    return NextResponse.json(
      { error: "Juda ko'p so'rov. Birozdan so'ng qayta urinib ko'ring." },
      { status: 429 },
    );
  }

  const body = await req.json().catch(() => null);
  if (!body?.title || !body?.price || !body?.categorySlug) {
    return NextResponse.json(
      { error: "title, price va categorySlug majburiy" },
      { status: 400 },
    );
  }
  // Admin qo'lda mahsulot qo'shsa fayl talab qilinmaydi (masalan namuna sifatida),
  // lekin oddiy sotuvchi fayl yuklamasdan mahsulot qo'sha olmaydi — xaridor
  // to'lov qilib hech narsa ololmaydigan holat shu bilan oldini olinadi.
  if (session.user.role !== "ADMIN" && !body.fileKey) {
    return NextResponse.json(
      { error: "Mahsulot faylini (.zip) yuklashingiz kerak" },
      { status: 400 },
    );
  }

  try {
    const category = await prisma.category.findUnique({
      where: { slug: body.categorySlug },
    });
    if (!category) {
      return NextResponse.json(
        { error: "Bunday kategoriya yo'q" },
        { status: 400 },
      );
    }

    const baseSlug = slugify(body.title);
    const slug = `${baseSlug}-${Math.random().toString(36).slice(2, 6)}`;

    const product = await prisma.product.create({
      data: {
        title: body.title,
        slug,
        description: body.description ?? "",
        price: Number(body.price),
        categoryId: category.id,
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
        screenshots: Array.isArray(body.screenshots) ? body.screenshots : [],
        fileKey: body.fileKey ?? `products/${slug}.zip`, // faqat admin yo'lida ishlatiladi (fayl talab qilinmaydi)
        demoUrl: body.demoUrl ?? null,
        subcategory: category.slug === "website" ? (body.subcategory ?? null) : null,
        telegramUsername: body.telegramUsername
          ? String(body.telegramUsername).replace(/^@/, "")
          : null,
        sellerId: session.user.id,
        // Admin qo'shsa — to'g'ridan ACTIVE. Sotuvchi qo'shsa — DRAFT
        // (5000 so'm e'lon to'lovi kutilmoqda; to'langach PENDING moderatsiyaga).
        status: session.user.role === "ADMIN" ? "ACTIVE" : "DRAFT",
      },
    });

    return NextResponse.json({ id: product.id, slug: product.slug });
  } catch (e) {
    await logError(e, "POST /api/products");
    return NextResponse.json(
      { error: "Baza ulanmagan yoki xatolik" },
      { status: 503 },
    );
  }
}
