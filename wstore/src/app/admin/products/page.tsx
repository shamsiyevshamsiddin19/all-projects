import Link from "next/link";
import { Plus, Pencil } from "lucide-react";
import { prisma } from "@/lib/prisma";
import { StatusButtons, DeleteButton, CheckFileButton } from "@/components/admin/AdminActions";

export const dynamic = "force-dynamic";

const STATUS_CLASS: Record<string, string> = {
  DRAFT: "text-muted border-border-strong bg-surface-2",
  ACTIVE: "text-green-400 border-green-500/40 bg-green-500/10",
  PENDING: "text-gold border-gold/40 bg-gold/10",
  REJECTED: "text-red-400 border-red-500/40 bg-red-500/10",
  PAUSED: "text-muted border-border-strong bg-surface-2",
};

export default async function AdminProducts() {
  const products = await prisma.product.findMany({
    orderBy: { createdAt: "desc" },
    include: { seller: { select: { name: true, email: true } } },
  });

  return (
    <div>
      <div className="mb-5 flex items-center justify-between">
        <h1 className="text-lg font-semibold text-fg">
          Barcha mahsulotlar{" "}
          <span className="text-sm font-normal text-muted">
            ({products.length})
          </span>
        </h1>
        <Link
          href="/seller/new"
          className="flex items-center gap-2 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-accent-hover"
        >
          <Plus size={16} /> Yangi mahsulot
        </Link>
      </div>

      <div className="overflow-x-auto rounded-card border border-border">
        <table className="w-full min-w-[720px] text-sm">
          <thead>
            <tr className="border-b border-border bg-surface text-left text-xs uppercase text-muted">
              <th className="px-4 py-3 font-medium">Mahsulot</th>
              <th className="px-4 py-3 font-medium">Sotuvchi</th>
              <th className="px-4 py-3 font-medium">Narx</th>
              <th className="px-4 py-3 font-medium">Holat</th>
              <th className="px-4 py-3 font-medium">Amallar</th>
            </tr>
          </thead>
          <tbody>
            {products.map((p) => (
              <tr key={p.id} className="border-b border-border last:border-0">
                <td className="px-4 py-3">
                  <Link
                    href={`/product/${p.slug}`}
                    className="font-medium text-fg hover:text-accent"
                  >
                    {p.title}
                  </Link>
                </td>
                <td className="px-4 py-3 text-muted">
                  {p.seller.name ?? p.seller.email}
                </td>
                <td className="px-4 py-3 text-muted">${Number(p.price)}</td>
                <td className="px-4 py-3">
                  <span
                    className={`rounded border px-2 py-0.5 text-xs ${STATUS_CLASS[p.status] ?? ""}`}
                  >
                    {p.status}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap items-center gap-2">
                    <CheckFileButton productId={p.id} />
                    <StatusButtons productId={p.id} status={p.status} />
                    <Link
                      href={`/seller/${p.id}/edit`}
                      className="flex items-center gap-1 rounded-md border border-border-strong px-2.5 py-1 text-xs text-muted transition hover:border-accent hover:text-fg"
                    >
                      <Pencil size={13} />
                    </Link>
                    <DeleteButton productId={p.id} />
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
