import { NextResponse } from "next/server";
import { requireAdmin } from "@/lib/admin";
import { prisma } from "@/lib/prisma";
import { logError } from "@/lib/errorLog";

const ALLOWED = ["PAID", "REJECTED"] as const;

// POST /api/admin/withdrawals/[id] — admin so'rovni bajaradi (karta orqali
// qo'lda to'lagandan keyin PAID belgilaydi) yoki rad etadi (mablag' qaytadi).
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
  const status = body?.status as (typeof ALLOWED)[number] | undefined;
  if (!status || !ALLOWED.includes(status)) {
    return NextResponse.json({ error: "Noto'g'ri status" }, { status: 400 });
  }

  try {
    const w = await prisma.withdrawal.findUnique({ where: { id } });
    if (!w || w.status !== "PENDING") {
      return NextResponse.json({ error: "Topilmadi yoki allaqachon hal qilingan" }, { status: 400 });
    }

    await prisma.$transaction(async (tx) => {
      await tx.withdrawal.update({
        where: { id },
        data: { status, paidAt: status === "PAID" ? new Date() : null },
      });
      if (status === "REJECTED") {
        // Rad etilsa — ushlab qolingan mablag' balansga qaytadi.
        await tx.user.update({
          where: { id: w.sellerId },
          data: { balance: { increment: w.amount } },
        });
      }
    });

    return NextResponse.json({ ok: true });
  } catch (e) {
    await logError(e, "POST /api/admin/withdrawals/[id]");
    return NextResponse.json({ error: "Server xatosi" }, { status: 500 });
  }
}
