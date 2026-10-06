import { NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { logError } from "@/lib/errorLog";
import { MIN_WITHDRAWAL_SOM } from "@/lib/click";

function cleanCard(v: unknown): string {
  return String(v ?? "").replace(/\s+/g, "");
}

// POST /api/seller/withdrawals — sotuvchi balansidan pul yechib olish so'rovi.
// Summasi darhol balansdan ushlab qolinadi (rad etilsa qaytariladi).
export async function POST(req: Request) {
  const session = await auth().catch(() => null);
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Tizimga kiring" }, { status: 401 });
  }

  const body = await req.json().catch(() => null);
  const amount = Number(body?.amount);
  const cardNumber = cleanCard(body?.cardNumber);

  if (!Number.isFinite(amount) || amount < MIN_WITHDRAWAL_SOM) {
    return NextResponse.json(
      { error: `Minimal summa ${MIN_WITHDRAWAL_SOM.toLocaleString("en-US").replace(/,/g, " ")} so'm` },
      { status: 400 },
    );
  }
  if (!/^\d{16}$/.test(cardNumber)) {
    return NextResponse.json(
      { error: "Karta raqami 16 xonali bo'lishi kerak" },
      { status: 400 },
    );
  }

  try {
    const result = await prisma.$transaction(async (tx) => {
      const user = await tx.user.findUnique({ where: { id: session.user.id } });
      if (!user || Number(user.balance) < amount) {
        throw new Error("INSUFFICIENT_BALANCE");
      }
      await tx.user.update({
        where: { id: session.user.id },
        data: { balance: { decrement: amount } },
      });
      return tx.withdrawal.create({
        data: { sellerId: session.user.id, amount, cardNumber },
      });
    });
    return NextResponse.json({ id: result.id });
  } catch (e) {
    if (e instanceof Error && e.message === "INSUFFICIENT_BALANCE") {
      return NextResponse.json({ error: "Balansingizda yetarli mablag' yo'q" }, { status: 400 });
    }
    await logError(e, "POST /api/seller/withdrawals");
    return NextResponse.json({ error: "Server xatosi" }, { status: 500 });
  }
}
