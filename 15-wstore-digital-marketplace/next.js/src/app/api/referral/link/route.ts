import { NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { logError } from "@/lib/errorLog";

// POST /api/referral/link — joriy foydalanuvchini taklif qilgan kishiga
// bog'laydi (faqat birinchi marta, o'zini o'zi taklif qila olmaydi).
export async function POST(req: Request) {
  const session = await auth().catch(() => null);
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Tizimga kiring" }, { status: 401 });
  }

  const body = await req.json().catch(() => null);
  const code = String(body?.code ?? "").trim();
  if (!code) {
    return NextResponse.json({ error: "code majburiy" }, { status: 400 });
  }

  try {
    const me = await prisma.user.findUnique({ where: { id: session.user.id } });
    if (!me || me.referredById) {
      return NextResponse.json({ linked: false });
    }

    const referrer = await prisma.user.findUnique({ where: { referralCode: code } });
    if (!referrer || referrer.id === me.id) {
      return NextResponse.json({ linked: false });
    }

    await prisma.user.update({
      where: { id: me.id },
      data: { referredById: referrer.id },
    });
    return NextResponse.json({ linked: true });
  } catch (e) {
    await logError(e, "POST /api/referral/link");
    return NextResponse.json({ error: "Server xatosi" }, { status: 500 });
  }
}
