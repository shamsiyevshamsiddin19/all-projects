import Link from "next/link";
import Image from "next/image";
import { redirect } from "next/navigation";
import {
  LayoutDashboard,
  Package,
  Users,
  CreditCard,
  ArrowLeft,
  Flag,
  Banknote,
  AlertTriangle,
} from "lucide-react";
import { prisma } from "@/lib/prisma";
import { auth } from "@/lib/auth";

// Butun /admin ostidagi sahifalar shu yerda himoyalanadi.
export default async function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const session = await auth().catch(() => null);
  if (!session?.user) redirect("/login");
  if (session.user.role !== "ADMIN") redirect("/");

  const [openReports, pendingWithdrawals] = await Promise.all([
    prisma.report.count({ where: { status: "OPEN" } }).catch(() => 0),
    prisma.withdrawal.count({ where: { status: "PENDING" } }).catch(() => 0),
  ]);

  const nav = [
    { href: "/admin", label: "Boshqaruv", icon: LayoutDashboard },
    { href: "/admin/products", label: "Mahsulotlar", icon: Package },
    { href: "/admin/users", label: "Foydalanuvchilar", icon: Users },
    { href: "/admin/payments", label: "To'lovlar", icon: CreditCard },
    {
      href: "/admin/withdrawals",
      label: "Yechib olishlar",
      icon: Banknote,
      badge: pendingWithdrawals,
    },
    { href: "/admin/reports", label: "Shikoyatlar", icon: Flag, badge: openReports },
    { href: "/admin/errors", label: "Xatoliklar", icon: AlertTriangle },
  ];

  return (
    <div className="min-h-screen">
      <header className="border-b border-border bg-bg/80 backdrop-blur">
        <div className="mx-auto flex h-14 max-w-[1200px] items-center justify-between px-4 sm:px-6">
          <div className="flex items-center gap-2">
            <Image
              src="/logo-icon.png"
              alt="wstore.uz"
              width={32}
              height={32}
              className="h-8 w-8 object-contain"
            />
            <span className="font-semibold text-fg">Admin panel</span>
          </div>
          <Link
            href="/"
            className="flex items-center gap-1.5 text-sm text-muted hover:text-fg"
          >
            <ArrowLeft size={15} /> Saytga qaytish
          </Link>
        </div>
      </header>

      <div className="mx-auto max-w-[1200px] px-4 py-6 sm:px-6">
        <nav className="mb-6 flex gap-1 overflow-x-auto border-b border-border">
          {nav.map((n) => (
            <Link
              key={n.href}
              href={n.href}
              className="flex shrink-0 items-center gap-2 border-b-2 border-transparent px-4 py-2.5 text-sm text-muted transition hover:text-fg"
            >
              <n.icon size={15} />
              {n.label}
              {"badge" in n && n.badge ? (
                <span className="flex h-4 min-w-4 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-medium text-fg">
                  {n.badge}
                </span>
              ) : null}
            </Link>
          ))}
        </nav>
        {children}
      </div>
    </div>
  );
}
