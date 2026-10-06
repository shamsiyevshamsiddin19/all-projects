import crypto from "crypto";
import { prisma } from "@/lib/prisma";
import {
  clickBridgeSecret,
  parseClickTransactionId,
  amountAfterCommission,
  REFERRAL_BONUS_SOM,
} from "@/lib/click";

// myxvest PHP ko'prigidan (wstore_bridge.php) keladigan "tarjima qilingan" so'rov —
// baza_bridge.php bilan bir xil shakl. Haqiqiy Click imzosi ko'prikda tekshirilgan.
export interface BridgeBody {
  secret: string;
  merchant_trans_id: string;
  merchant_prepare_id: number;
  amount: number | string;
  click_trans_id: string;
  click_error: number;
}

export interface BridgeResult {
  error: number;
  prepare_id: number;
}

function amountsMatch(a: number | string, b: unknown): boolean {
  const x = typeof a === "string" ? parseFloat(a) : a;
  const y = Number(b);
  return Math.abs(x - y) < 0.01;
}

async function parseBody(req: Request): Promise<BridgeBody | null> {
  try {
    const body = await req.json();
    if (!body || typeof body !== "object") return null;
    return body as BridgeBody;
  } catch {
    return null;
  }
}

function checkSecret(body: BridgeBody): boolean {
  const expected = clickBridgeSecret();
  const received = String(body.secret || "");
  if (received.length !== expected.length) return false;
  return crypto.timingSafeEqual(Buffer.from(received), Buffer.from(expected));
}

export async function handleClickPrepare(req: Request): Promise<BridgeResult> {
  const body = await parseBody(req);
  if (!body || !checkSecret(body)) return { error: -1, prepare_id: 0 };

  const id = parseClickTransactionId(body.merchant_trans_id);
  if (!id) return { error: -5, prepare_id: 0 };

  const ct = await prisma.clickTransaction.findUnique({ where: { id } });
  if (!ct || ct.merchantTransId !== body.merchant_trans_id) {
    return { error: -5, prepare_id: 0 };
  }

  if (!amountsMatch(body.amount, ct.amount)) {
    return { error: -2, prepare_id: ct.id };
  }

  if (ct.status === "PAID") return { error: -4, prepare_id: ct.id };
  if (ct.status === "FAILED" || ct.status === "REFUNDED") {
    return { error: -9, prepare_id: ct.id };
  }

  return { error: 0, prepare_id: ct.id };
}

export async function handleClickComplete(req: Request): Promise<BridgeResult> {
  const body = await parseBody(req);
  if (!body || !checkSecret(body)) return { error: -1, prepare_id: 0 };

  const id = parseClickTransactionId(body.merchant_trans_id);
  if (!id) return { error: -5, prepare_id: 0 };

  const ct = await prisma.clickTransaction.findUnique({ where: { id } });
  if (!ct || ct.merchantTransId !== body.merchant_trans_id) {
    return { error: -5, prepare_id: 0 };
  }

  if (!amountsMatch(body.amount, ct.amount)) {
    return { error: -2, prepare_id: ct.id };
  }

  // Takroriy callback — muvaffaqiyatli deb javob beramiz, qayta ishlamaymiz.
  if (ct.status === "PAID") return { error: 0, prepare_id: ct.id };
  if (ct.status === "FAILED" || ct.status === "REFUNDED") {
    return { error: -9, prepare_id: ct.id };
  }

  const clickError = Number(body.click_error || 0);
  if (clickError !== 0) {
    await prisma.clickTransaction.update({
      where: { id: ct.id },
      data: { status: "FAILED", clickTransId: String(body.click_trans_id || "") },
    });
    return { error: -9, prepare_id: ct.id };
  }

  try {
    await prisma.$transaction(async (tx) => {
      await tx.clickTransaction.update({
        where: { id: ct.id },
        data: {
          status: "PAID",
          clickTransId: String(body.click_trans_id || ""),
          paidAt: new Date(),
        },
      });

      if (ct.kind === "PURCHASE" && ct.orderId) {
        const token = crypto.randomBytes(24).toString("hex");
        const order = await tx.order.update({
          where: { id: ct.orderId },
          data: { status: "PAID", provider: "click", downloadToken: token },
        });
        const product = await tx.product.update({
          where: { id: order.productId },
          data: { salesCount: { increment: 1 } },
        });
        // Sotuvchi balansiga (komissiyadan keyin) qo'shamiz — pul yechib
        // olish so'rovi uchun.
        const credit = amountAfterCommission(Number(ct.amount));
        await tx.user.update({
          where: { id: product.sellerId },
          data: { balance: { increment: credit } },
        });

        // Referal bonusi — xaridor kimdir orqali kelgan bo'lsa va hali
        // bonus to'lanmagan bo'lsa, taklif qilganga bir martalik bonus.
        const buyer = await tx.user.findUnique({ where: { id: order.buyerId } });
        if (buyer?.referredById && !buyer.referralBonusPaid) {
          await tx.user.update({
            where: { id: buyer.id },
            data: { referralBonusPaid: true },
          });
          await tx.user.update({
            where: { id: buyer.referredById },
            data: { balance: { increment: REFERRAL_BONUS_SOM } },
          });
        }
      }

      if (ct.kind === "LISTING" && ct.productId) {
        // faqat DRAFT holatidagi loyihani moderatsiyaga o'tkazamiz
        await tx.product.updateMany({
          where: { id: ct.productId, status: "DRAFT" },
          data: { status: "PENDING" },
        });
      }
    });
  } catch (e) {
    console.error("click complete transaction error", e);
    return { error: -1, prepare_id: 0 };
  }

  return { error: 0, prepare_id: ct.id };
}
