import Link from "next/link";
import { Package, ShoppingCart, Wallet, Plus, Pencil } from "lucide-react";
import Navbar from "@/components/Navbar";
import ListingPayButton from "@/components/ListingPayButton";
import DeleteProductButton, {
  ToggleActiveButton,
} from "@/components/SellerProductActions";
import { auth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";

export default async function SellerPage() {
  const session = await auth().catch(() => null);

  let products: { id: string; title: string; price: unknown; salesCount: number; status: string }[] = [];
  let balance = 0;
  if (session?.user?.id) {
    const [rows, user] = await Promise.all([
      prisma.product
        .findMany({
          where: { sellerId: session.user.id },
          orderBy: { createdAt: "desc" },
          select: { id: true, title: true, price: true, salesCount: true, status: true },
        })
        .catch(() => []),
      prisma.user
        .findUnique({ where: { id: session.user.id }, select: { balance: true } })
        .catch(() => null),
    ]);
    products = rows;
    balance = Number(user?.balance ?? 0);
  }

  const totalSales = products.reduce((s, p) => s + p.salesCount, 0);
  const revenue = products.reduce(
    (s, p) => s + Number(p.price) * p.salesCount,
    0,
  );

  const stats = [
    { label: "Mahsulotlar", value: String(products.length), icon: Package },
    { label: "Jami sotuv", value: String(totalSales), icon: ShoppingCart },
    { label: "Daromad", value: `$${revenue}`, icon: Wallet },
  ];

  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-[1100px] px-6 py-10">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-fg">Sotuvchi paneli</h1>
            <p className="mt-1 text-sm text-muted">
              Mahsulotlaringiz, sotuvlar va daromad.
            </p>
          </div>
          <Link
            href="/seller/new"
            className="flex items-center gap-2 rounded-lg bg-accent px-4 py-2.5 text-sm font-medium text-white hover:bg-accent-hover"
          >
            <Plus size={16} /> Yangi mahsulot
          </Link>
        </div>

        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
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
          <Link
            href="/seller/balance"
            className="flex items-center gap-4 rounded-card border border-accent/40 bg-accent/5 p-5 transition hover:border-accent"
          >
            <div className="flex h-11 w-11 items-center justify-center rounded-lg border border-accent/40 bg-accent/10 text-accent">
              <Wallet size={20} />
            </div>
            <div>
              <div className="text-2xl font-bold text-fg">
                {balance.toLocaleString("en-US").replace(/,/g, " ")}
              </div>
              <div className="text-sm text-accent">Balans (so&apos;m) →</div>
            </div>
          </Link>
        </div>

        <div className="mt-8">
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted">
            Mening mahsulotlarim
          </h2>
          {!session?.user ? (
            <EmptyBox>
              Panelni ko'rish uchun{" "}
              <Link href="/login" className="text-accent">
                tizimga kiring
              </Link>
              .
            </EmptyBox>
          ) : products.length === 0 ? (
            <EmptyBox>Hozircha mahsulot yo'q. Yangisini qo'shing.</EmptyBox>
          ) : (
            <div className="overflow-hidden rounded-card border border-border">
              {products.map((p) => (
                <div
                  key={p.id}
                  className="flex flex-col gap-2 border-b border-border bg-surface px-4 py-3 last:border-0 sm:flex-row sm:items-center sm:justify-between"
                >
                  <span className="text-sm text-fg">{p.title}</span>
                  <div className="flex flex-wrap items-center gap-3 text-sm text-muted">
                    <span>${Number(p.price)}</span>
                    <span>{p.salesCount} sotuv</span>
                    <StatusBadge status={p.status} />
                    {p.status === "DRAFT" ? (
                      <ListingPayButton productId={p.id} />
                    ) : (
                      <Link
                        href={`/seller/${p.id}/edit`}
                        className="flex items-center gap-1.5 rounded-lg border border-border-strong px-3 py-1.5 text-xs font-medium text-fg transition hover:border-accent"
                      >
                        <Pencil size={13} /> Tahrirlash
                      </Link>
                    )}
                    {(p.status === "ACTIVE" || p.status === "PAUSED") && (
                      <ToggleActiveButton productId={p.id} status={p.status} />
                    )}
                    <DeleteProductButton productId={p.id} />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </>
  );
}

function EmptyBox({ children }: { children: React.ReactNode }) {
  return (
    <div className="rounded-card border border-dashed border-border p-12 text-center text-muted">
      {children}
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, string> = {
    DRAFT: "text-muted border-border-strong bg-surface-2",
    ACTIVE: "text-green-400 border-green-500/40 bg-green-500/10",
    PENDING: "text-gold border-gold/40 bg-gold/10",
    REJECTED: "text-red-400 border-red-500/40 bg-red-500/10",
    PAUSED: "text-muted border-border-strong bg-surface-2",
  };
  return (
    <span
      className={`rounded border px-2 py-0.5 text-xs ${map[status] ?? "border-border text-muted"}`}
    >
      {status}
    </span>
  );
}
