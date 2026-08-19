import { NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";

// POST /api/wishlist/[productId] — sevimlilarga qo'shish.
export async function POST(
  _req: Request,
  { params }: { params: Promise<{ productId: string }> },
) {
  const session = await auth().catch(() => null);
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Tizimga kiring" }, { status: 401 });
  }
  const { productId } = await params;
  try {
    await prisma.wishlist.upsert({
      where: { userId_productId: { userId: session.user.id, productId } },
      create: { userId: session.user.id, productId },
      update: {},
    });
    return NextResponse.json({ wishlisted: true });
  } catch (e) {
    console.error("wishlist add error", e);
    return NextResponse.json({ error: "Server xatosi" }, { status: 500 });
  }
}

// DELETE /api/wishlist/[productId] — sevimlilardan olib tashlash.
export async function DELETE(
  _req: Request,
  { params }: { params: Promise<{ productId: string }> },
) {
  const session = await auth().catch(() => null);
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Tizimga kiring" }, { status: 401 });
  }
  const { productId } = await params;
  try {
    await prisma.wishlist
      .delete({
        where: { userId_productId: { userId: session.user.id, productId } },
      })
      .catch(() => null);
    return NextResponse.json({ wishlisted: false });
  } catch (e) {
    console.error("wishlist remove error", e);
    return NextResponse.json({ error: "Server xatosi" }, { status: 500 });
  }
}
