import { prisma } from "@/lib/prisma";

export const dynamic = "force-dynamic";

export default async function AdminErrors() {
  const errors = await prisma.errorLog.findMany({
    orderBy: { createdAt: "desc" },
    take: 100,
  });

  return (
    <div>
      <h1 className="mb-5 text-lg font-semibold text-fg">
        Server xatoliklari{" "}
        <span className="text-sm font-normal text-muted">(so&apos;nggi {errors.length})</span>
      </h1>

      {errors.length === 0 ? (
        <p className="rounded-card border border-dashed border-border p-8 text-center text-sm text-muted">
          Xatolik qayd etilmagan. 🎉
        </p>
      ) : (
        <div className="flex flex-col gap-2">
          {errors.map((e) => (
            <details
              key={e.id}
              className="rounded-card border border-border bg-surface p-4"
            >
              <summary className="flex cursor-pointer items-center justify-between gap-3 text-sm">
                <span className="truncate text-red-400">{e.message}</span>
                <span className="shrink-0 text-xs text-muted">
                  {e.context} · {new Date(e.createdAt).toLocaleString("uz-UZ")}
                </span>
              </summary>
              {e.stack && (
                <pre className="mt-3 max-h-64 overflow-auto whitespace-pre-wrap break-all rounded-lg bg-bg p-3 text-xs text-muted">
                  {e.stack}
                </pre>
              )}
            </details>
          ))}
        </div>
      )}
    </div>
  );
}
