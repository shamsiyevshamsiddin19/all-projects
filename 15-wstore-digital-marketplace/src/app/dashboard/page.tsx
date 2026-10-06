import Navbar from "@/components/Navbar";
import Price from "@/components/Price";
import ReferralCard from "@/components/ReferralCard";
import { auth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import Link from "next/link";
import { Download, Clock, XCircle, CheckCircle2 } from "lucide-react";
import { REFERRAL_BONUS_SOM } from "@/lib/click";

const APP_URL = process.env.APP_URL || "https://wstore.uz";

const STATUS_META: Record<
  string,
  { label: string; className: string; icon: typeof CheckCircle2 }
> = {
  PAID: {
    label: "To'landi",
    className: "text-green-400 border-green-500/40 bg-green-500/10",
    icon: CheckCircle2,
  },
  PENDING: {
    label: "Kutilmoqda",
    className: "text-gold border-gold/40 bg-gold/10",
    icon: Clock,
  },
  FAILED: {
    label: "Amalga oshmadi",
    className: "text-red-400 border-red-500/40 bg-red-500/10",
    icon: XCircle,
  },
  REFUNDED: {
    label: "Qaytarildi",
    className: "text-muted border-border-strong bg-surface-2",
    icon: XCircle,
  },
};

export default async function DashboardPage() {
  let session = null;
  try {
    session = await auth();
  } catch {
    session = null;
  }

  const [orders, referralUser] = session?.user?.id
    ? await Promise.all([
        prisma.order
          .findMany({
            where: { buyerId: session.user.id },
            orderBy: { createdAt: "desc" },
            include: { product: { select: { title: true, slug: true, price: true, coverImage: true } } },
          })
          .catch(() => []),
        prisma.user
          .findUnique({
            where: { id: session.user.id },
            select: {
              referralCode: true,
              _count: { select: { referrals: true } },
              referrals: { where: { referralBonusPaid: true }, select: { id: true } },
            },
          })
          .catch(() => null),
      ])
    : [[], null];

  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-[1100px] px-6 py-10">
        <h1 className="text-2xl font-bold text-fg">Kabinet</h1>

        {session?.user ? (
          <>
            <p className="mt-1 text-sm text-muted">
              Xush kelibsiz, {session.user.name}. Xaridlaringiz shu yerda.
            </p>

            {referralUser && (
              <div className="mt-6">
                <ReferralCard
                  link={`${APP_URL}/?ref=${referralUser.referralCode}`}
                  referralCount={referralUser._count.referrals}
                  bonusEarned={referralUser.referrals.length * REFERRAL_BONUS_SOM}
                />
              </div>
            )}

            {orders.length === 0 ? (
              <div className="mt-6 rounded-card border border-dashed border-border p-12 text-center text-muted">
                Hozircha xarid yo&apos;q. Katalogdan mahsulot tanlang.
              </div>
            ) : (
              <div className="mt-6 flex flex-col gap-3">
                {orders.map((o) => {
                  const meta = STATUS_META[o.status] ?? STATUS_META.PENDING;
                  const Icon = meta.icon;
                  return (
                    <div
                      key={o.id}
                      className="flex flex-col gap-3 rounded-card border border-border bg-surface p-4 sm:flex-row sm:items-center sm:justify-between"
                    >
                      <div className="flex items-center gap-3">
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img
                          src={o.product.coverImage}
                          alt=""
                          className="h-12 w-16 shrink-0 rounded-md border border-border object-cover"
                        />
                        <div>
                          <Link
                            href={`/product/${o.product.slug}`}
                            className="text-sm font-medium text-fg hover:text-accent"
                          >
                            {o.product.title}
                          </Link>
                          <div className="mt-0.5 flex items-center gap-2 text-xs text-muted">
                            <Price usd={Number(o.product.price)} />
                            <span>·</span>
                            <span>{new Date(o.createdAt).toLocaleDateString("uz-UZ")}</span>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span
                          className={`flex items-center gap-1 rounded border px-2 py-0.5 text-xs ${meta.className}`}
                        >
                          <Icon size={12} /> {meta.label}
                        </span>
                        {o.status === "PAID" && o.downloadToken && (
                          <a
                            href={`/api/download/${o.downloadToken}`}
                            className="flex items-center gap-1.5 rounded-lg bg-accent px-3 py-1.5 text-xs font-medium text-white transition hover:bg-accent-hover"
                          >
                            <Download size={13} /> Yuklab olish
                          </a>
                        )}
                        {o.status === "PENDING" && (
                          <Link
                            href={`/order/${o.id}`}
                            className="flex items-center gap-1.5 rounded-lg border border-border-strong px-3 py-1.5 text-xs font-medium text-fg transition hover:border-accent"
                          >
                            Ko&apos;rish
                          </Link>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </>
        ) : (
          <div className="mt-6 rounded-card border border-border bg-surface p-8 text-center">
            <p className="mb-4 text-muted">
              Kabinetni ko'rish uchun tizimga kiring.
            </p>
            <Link
              href="/login"
              className="inline-block rounded-lg bg-accent px-5 py-2.5 text-sm font-medium text-white hover:bg-accent-hover"
            >
              Google bilan kirish
            </Link>
          </div>
        )}
      </main>
    </>
  );
}
