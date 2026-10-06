import Link from "next/link";
import { prisma } from "@/lib/prisma";
import { ReportStatusButton } from "@/components/admin/AdminActions";

export const dynamic = "force-dynamic";

const STATUS_CLASS: Record<string, string> = {
  OPEN: "text-gold border-gold/40 bg-gold/10",
  RESOLVED: "text-green-400 border-green-500/40 bg-green-500/10",
};

export default async function AdminReports() {
  const reports = await prisma.report.findMany({
    orderBy: [{ status: "asc" }, { createdAt: "desc" }],
    include: {
      product: { select: { title: true, slug: true } },
      reporter: { select: { name: true, email: true } },
    },
  });

  return (
    <div>
      <h1 className="mb-5 text-lg font-semibold text-fg">
        Shikoyatlar{" "}
        <span className="text-sm font-normal text-muted">({reports.length})</span>
      </h1>

      {reports.length === 0 ? (
        <p className="rounded-card border border-dashed border-border p-8 text-center text-sm text-muted">
          Hozircha shikoyat yo&apos;q.
        </p>
      ) : (
        <div className="flex flex-col gap-3">
          {reports.map((r) => (
            <div
              key={r.id}
              className="flex flex-col gap-2 rounded-card border border-border bg-surface p-4"
            >
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div>
                  <Link
                    href={`/product/${r.product.slug}`}
                    className="text-sm font-medium text-fg hover:text-accent"
                  >
                    {r.product.title}
                  </Link>
                  <div className="text-xs text-muted">
                    {r.reporter.name ?? r.reporter.email} ·{" "}
                    {new Date(r.createdAt).toLocaleDateString("uz-UZ")}
                  </div>
                </div>
                <span
                  className={`rounded border px-2 py-0.5 text-xs ${STATUS_CLASS[r.status] ?? ""}`}
                >
                  {r.status}
                </span>
              </div>
              <p className="text-sm text-fg/90">{r.reason}</p>
              {r.comment && <p className="text-sm text-muted">{r.comment}</p>}
              <div>
                <ReportStatusButton reportId={r.id} status={r.status} />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
