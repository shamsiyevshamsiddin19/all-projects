import { Package, Clock, Users, Wallet } from "lucide-react";
import { prisma } from "@/lib/prisma";
import ModerationQueue from "@/components/admin/ModerationQueue";

export const dynamic = "force-dynamic";

export default async function AdminHome() {
  const [productCount, pendingCount, userCount, paidAgg, pending] =
    await Promise.all([
      prisma.product.count(),
      prisma.product.count({ where: { status: "PENDING" } }),
      prisma.user.count(),
      prisma.clickTransaction.aggregate({
        where: { status: "PAID" },
        _sum: { amount: true },
      }),
      prisma.product.findMany({
        where: { status: "PENDING" },
        orderBy: { createdAt: "asc" },
        include: { seller: { select: { name: true, email: true } } },
      }),
    ]);

  const revenue = Number(paidAgg._sum.amount ?? 0);

  const stats = [
    { label: "Mahsulotlar", value: productCount, icon: Package },
    { label: "Moderatsiyada", value: pendingCount, icon: Clock },
    { label: "Foydalanuvchilar", value: userCount, icon: Users },
    {
      label: "To'lovlar (so'm)",
      value: revenue.toLocaleString("en-US").replace(/,/g, " "),
      icon: Wallet,
    },
  ];

  return (
    <div className="flex flex-col gap-8">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((s) => (
          <div
            key={s.label}
            className="flex items-center gap-4 rounded-card border border-border bg-surface p-5"
          >
            <div className="flex h-11 w-11 items-center justify-center rounded-lg border border-border-strong bg-surface-2 text-accent">
              <s.icon size={20} />
            </div>
            <div>
              <div className="text-2xl font-bold text-fg">{s.value}</div>
              <div className="text-sm text-muted">{s.label}</div>
            </div>
          </div>
        ))}
      </div>

      <section>
        <h2 className="mb-4 text-lg font-semibold text-fg">
          Moderatsiya navbati
          <span className="ml-2 text-sm font-normal text-muted">
            (5000 so&apos;m to&apos;langan, tasdiq kutayotgan loyihalar)
          </span>
        </h2>

        {pending.length === 0 ? (
          <p className="rounded-card border border-dashed border-border p-8 text-center text-sm text-muted">
            Moderatsiyada loyiha yo&apos;q.
          </p>
        ) : (
          <ModerationQueue
            products={pending.map((p) => ({
              id: p.id,
              title: p.title,
              price: Number(p.price),
              coverImage: p.coverImage,
              status: p.status,
              sellerLabel: p.seller.name ?? p.seller.email,
            }))}
          />
        )}
      </section>
    </div>
  );
}
