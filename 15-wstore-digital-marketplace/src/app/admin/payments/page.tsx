import { prisma } from "@/lib/prisma";

export const dynamic = "force-dynamic";

const PAY_CLASS: Record<string, string> = {
  PAID: "text-green-400 border-green-500/40 bg-green-500/10",
  PENDING: "text-gold border-gold/40 bg-gold/10",
  FAILED: "text-red-400 border-red-500/40 bg-red-500/10",
  REFUNDED: "text-muted border-border-strong bg-surface-2",
};

function fmt(n: number): string {
  return n.toLocaleString("en-US").replace(/,/g, " ");
}

export default async function AdminPayments() {
  const txns = await prisma.clickTransaction.findMany({
    orderBy: { createdAt: "desc" },
    take: 100,
    include: {
      order: { include: { product: { select: { title: true } } } },
      product: { select: { title: true } },
    },
  });

  const totalPaid = txns
    .filter((t) => t.status === "PAID")
    .reduce((s, t) => s + Number(t.amount), 0);

  return (
    <div>
      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-lg font-semibold text-fg">
          Click to&apos;lovlari{" "}
          <span className="text-sm font-normal text-muted">({txns.length})</span>
        </h1>
        <span className="text-sm text-muted">
          Jami to&apos;langan:{" "}
          <span className="font-semibold text-fg">{fmt(totalPaid)} so&apos;m</span>
        </span>
      </div>

      <div className="overflow-x-auto rounded-card border border-border">
        <table className="w-full min-w-[720px] text-sm">
          <thead>
            <tr className="border-b border-border bg-surface text-left text-xs uppercase text-muted">
              <th className="px-4 py-3 font-medium">#</th>
              <th className="px-4 py-3 font-medium">Turi</th>
              <th className="px-4 py-3 font-medium">Nima uchun</th>
              <th className="px-4 py-3 font-medium">Summa</th>
              <th className="px-4 py-3 font-medium">Holat</th>
              <th className="px-4 py-3 font-medium">Sana</th>
            </tr>
          </thead>
          <tbody>
            {txns.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-muted">
                  Hozircha to&apos;lov yo&apos;q.
                </td>
              </tr>
            ) : (
              txns.map((t) => (
                <tr key={t.id} className="border-b border-border last:border-0">
                  <td className="px-4 py-3 text-muted">{t.merchantTransId ?? t.id}</td>
                  <td className="px-4 py-3">
                    <span className="rounded border border-border px-2 py-0.5 text-xs text-muted">
                      {t.kind === "PURCHASE" ? "Xarid" : "E'lon (5000)"}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-fg">
                    {t.order?.product?.title ?? t.product?.title ?? "—"}
                  </td>
                  <td className="px-4 py-3 text-muted">{fmt(Number(t.amount))} so&apos;m</td>
                  <td className="px-4 py-3">
                    <span
                      className={`rounded border px-2 py-0.5 text-xs ${PAY_CLASS[t.status] ?? ""}`}
                    >
                      {t.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-muted">
                    {t.createdAt.toISOString().slice(0, 16).replace("T", " ")}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
