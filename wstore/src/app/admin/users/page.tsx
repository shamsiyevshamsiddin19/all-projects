import { prisma } from "@/lib/prisma";
import { auth } from "@/lib/auth";
import { RoleSelect } from "@/components/admin/AdminActions";

export const dynamic = "force-dynamic";

export default async function AdminUsers() {
  const session = await auth().catch(() => null);
  const users = await prisma.user.findMany({
    orderBy: { createdAt: "asc" },
    select: {
      id: true,
      name: true,
      email: true,
      image: true,
      role: true,
      _count: { select: { products: true, orders: true } },
    },
  });

  return (
    <div>
      <h1 className="mb-5 text-lg font-semibold text-fg">
        Foydalanuvchilar{" "}
        <span className="text-sm font-normal text-muted">({users.length})</span>
      </h1>

      <div className="overflow-x-auto rounded-card border border-border">
        <table className="w-full min-w-[640px] text-sm">
          <thead>
            <tr className="border-b border-border bg-surface text-left text-xs uppercase text-muted">
              <th className="px-4 py-3 font-medium">Foydalanuvchi</th>
              <th className="px-4 py-3 font-medium">Email</th>
              <th className="px-4 py-3 font-medium">Mahsulot</th>
              <th className="px-4 py-3 font-medium">Buyurtma</th>
              <th className="px-4 py-3 font-medium">Rol</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id} className="border-b border-border last:border-0">
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    {u.image ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img
                        src={u.image}
                        alt=""
                        className="h-7 w-7 rounded-full object-cover"
                      />
                    ) : (
                      <span className="flex h-7 w-7 items-center justify-center rounded-full bg-surface-2 text-xs font-semibold text-muted">
                        {(u.name ?? u.email).charAt(0).toUpperCase()}
                      </span>
                    )}
                    <span className="text-fg">{u.name ?? "—"}</span>
                  </div>
                </td>
                <td className="px-4 py-3 text-muted">{u.email}</td>
                <td className="px-4 py-3 text-muted">{u._count.products}</td>
                <td className="px-4 py-3 text-muted">{u._count.orders}</td>
                <td className="px-4 py-3">
                  <RoleSelect
                    userId={u.id}
                    role={u.role}
                    disabled={u.id === session?.user?.id}
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
