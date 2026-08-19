import { prisma } from "@/lib/prisma";
import { WithdrawalActions } from "@/components/admin/AdminActions";

export const dynamic = "force-dynamic";

const STATUS_CLASS: Record<string, string> = {
  PENDING: "text-gold border-gold/40 bg-gold/10",
  PAID: "text-green-400 border-green-500/40 bg-green-500/10",
  REJECTED: "text-red-400 border-red-500/40 bg-red-500/10",
};

function fmt(n: number): string {
  return n.toLocaleString("en-US").replace(/,/g, " ");
}

export default async function AdminWithdrawals() {
  const withdrawals = await prisma.withdrawal.findMany({
    orderBy: [{ status: "asc" }, { createdAt: "desc" }],
    include: { seller: { select: { name: true, email: true } } },
  });

  return (
    <div>
      <h1 className="mb-5 text-lg font-semibold text-fg">
        Pul yechib olish so&apos;rovlari{" "}
        <span className="text-sm font-normal text-muted">({withdrawals.length})</span>
      </h1>

      {withdrawals.length === 0 ? (
        <p className="rounded-card border border-dashed border-border p-8 text-center text-sm text-muted">
          Hozircha so&apos;rov yo&apos;q.
        </p>
      ) : (
        <div className="overflow-x-auto rounded-card border border-border">
          <table className="w-full min-w-[720px] text-sm">
            <thead>
              <tr className="border-b border-border bg-surface text-left text-xs uppercase text-muted">
                <th className="px-4 py-3 font-medium">Sotuvchi</th>
                <th className="px-4 py-3 font-medium">Summa</th>
                <th className="px-4 py-3 font-medium">Karta</th>
                <th className="px-4 py-3 font-medium">Sana</th>
                <th className="px-4 py-3 font-medium">Holat</th>
                <th className="px-4 py-3 font-medium">Amallar</th>
              </tr>
            </thead>
            <tbody>
              {withdrawals.map((w) => (
                <tr key={w.id} className="border-b border-border last:border-0">
                  <td className="px-4 py-3 text-fg">
                    {w.seller.name ?? w.seller.email}
                  </td>
                  <td className="px-4 py-3 text-fg">{fmt(Number(w.amount))} so&apos;m</td>
                  <td className="px-4 py-3 font-mono text-muted">{w.cardNumber}</td>
                  <td className="px-4 py-3 text-muted">
                    {new Date(w.createdAt).toLocaleDateString("uz-UZ")}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`rounded border px-2 py-0.5 text-xs ${STATUS_CLASS[w.status] ?? ""}`}
                    >
                      {w.status}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {w.status === "PENDING" && <WithdrawalActions withdrawalId={w.id} />}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
