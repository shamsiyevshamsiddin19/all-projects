import { NextResponse } from "next/server";
import { requireAdmin } from "@/lib/admin";
import { prisma } from "@/lib/prisma";

const ALLOWED = ["BUYER", "SELLER", "ADMIN"] as const;
type RoleVal = (typeof ALLOWED)[number];

// POST /api/admin/users/[id]/role — foydalanuvchi rolini o'zgartirish (admin).
export async function POST(
  req: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const admin = await requireAdmin();
  if (!admin) {
    return NextResponse.json({ error: "Ruxsat yo'q" }, { status: 403 });
  }

  const { id } = await params;
  const body = await req.json().catch(() => null);
  const role = body?.role as RoleVal | undefined;
  if (!role || !ALLOWED.includes(role)) {
    return NextResponse.json({ error: "Noto'g'ri rol" }, { status: 400 });
  }

  // O'zining ADMIN rolini tortib olishdan himoya (o'zini bloklab qo'ymaslik uchun).
  if (id === admin.userId && role !== "ADMIN") {
    return NextResponse.json(
      { error: "O'z admin rolingizni o'zgartira olmaysiz" },
      { status: 400 },
    );
  }

  try {
    await prisma.user.update({ where: { id }, data: { role } });
    return NextResponse.json({ ok: true, role });
  } catch (e) {
    console.error("admin role error", e);
    return NextResponse.json({ error: "Server xatosi" }, { status: 500 });
  }
}
