import Link from "next/link";
import { ArrowLeft, Wallet, Clock, CheckCircle2, XCircle } from "lucide-react";
import Navbar from "@/components/Navbar";
import WithdrawalForm from "@/components/WithdrawalForm";
import { auth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { MIN_WITHDRAWAL_SOM } from "@/lib/click";

const STATUS_META: Record<string, { label: string; className: string; icon: typeof Clock }> = {
  PENDING: { label: "Kutilmoqda", className: "text-gold border-gold/40 bg-gold/10", icon: Clock },
  PAID: { label: "To'landi", className: "text-green-400 border-green-500/40 bg-green-500/10", icon: CheckCircle2 },
  REJECTED: { label: "Rad etildi", className: "text-red-400 border-red-500/40 bg-red-500/10", icon: XCircle },
};

function maskCard(card: string): string {
  return card.length >= 4 ? `**** **** **** ${card.slice(-4)}` : card;
}

export default async function SellerBalancePage() {
  const session = await auth().catch(() => null);
  if (!session?.user?.id) {
    return (
      <>
        <Navbar />
        <main className="mx-auto max-w-[700px] px-6 py-10 text-center">
          <p className="text-muted">
            Ko&apos;rish uchun{" "}
            <Link href="/login" className="text-accent">
              tizimga kiring
            </Link>
            .
          </p>
        </main>
      </>
    );
  }

  const [user, withdrawals] = await Promise.all([
    prisma.user.findUnique({ where: { id: session.user.id }, select: { balance: true } }),
    prisma.withdrawal.findMany({
      where: { sellerId: session.user.id },
      orderBy: { createdAt: "desc" },
    }),
  ]);

  const balance = Number(user?.balance ?? 0);
  const fmt = (n: number) => n.toLocaleString("en-US").replace(/,/g, " ");

  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-[700px] px-6 py-10">
        <Link
          href="/seller"
          className="inline-flex items-center gap-1.5 text-sm text-muted hover:text-accent"
        >
          <ArrowLeft size={15} /> Sotuvchi paneliga qaytish
        </Link>

        <h1 className="mb-6 mt-4 text-2xl font-bold text-fg">Balans</h1>

        <div className="flex items-center gap-4 rounded-card border border-border bg-surface p-5">
          <div className="flex h-12 w-12 items-center justify-center rounded-lg border border-border-strong bg-surface-2 text-accent">
            <Wallet size={22} />
          </div>
          <div>
            <div className="text-2xl font-bold text-fg">{fmt(balance)} so&apos;m</div>
            <div className="text-sm text-muted">Yechib olish uchun mavjud</div>
          </div>
        </div>

        <div className="mt-6 rounded-card border border-border bg-surface p-5">
          <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-muted">
            Pul yechib olish
          </h2>
          <WithdrawalForm balance={balance} minAmount={MIN_WITHDRAWAL_SOM} />
        </div>

        <div className="mt-8">
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted">
            So&apos;rovlar tarixi
          </h2>
          {withdrawals.length === 0 ? (
            <p className="rounded-card border border-dashed border-border p-8 text-center text-sm text-muted">
              Hozircha so&apos;rov yo&apos;q.
            </p>
          ) : (
            <div className="flex flex-col gap-2">
              {withdrawals.map((w) => {
                const meta = STATUS_META[w.status];
                const Icon = meta.icon;
                return (
                  <div
                    key={w.id}
                    className="flex items-center justify-between rounded-card border border-border bg-surface px-4 py-3"
                  >
                    <div>
                      <div className="text-sm font-medium text-fg">
                        {fmt(Number(w.amount))} so&apos;m
                      </div>
                      <div className="text-xs text-muted">
                        {maskCard(w.cardNumber)} ·{" "}
                        {new Date(w.createdAt).toLocaleDateString("uz-UZ")}
                      </div>
                    </div>
                    <span
                      className={`flex items-center gap-1 rounded border px-2 py-0.5 text-xs ${meta.className}`}
                    >
                      <Icon size={12} /> {meta.label}
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </main>
    </>
  );
}
