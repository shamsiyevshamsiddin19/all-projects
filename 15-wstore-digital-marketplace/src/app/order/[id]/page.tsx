import Link from "next/link";
import { notFound, redirect } from "next/navigation";
import { CheckCircle2, Clock, XCircle, ArrowLeft, Download } from "lucide-react";
import Navbar from "@/components/Navbar";
import OrderStatusPoll from "@/components/OrderStatusPoll";
import { auth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";

export default async function OrderPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const session = await auth().catch(() => null);
  if (!session?.user?.id) redirect("/login");

  const order = await prisma.order
    .findUnique({ where: { id }, include: { product: true } })
    .catch(() => null);

  if (!order || order.buyerId !== session.user.id) notFound();

  const isPaid = order.status === "PAID";
  const isPending = order.status === "PENDING";
  const isFailed = order.status === "FAILED" || order.status === "REFUNDED";

  return (
    <>
      <Navbar />
      <OrderStatusPoll pending={isPending} />
      <main className="mx-auto max-w-[600px] px-6 py-12">
        <Link
          href={`/product/${order.product.slug}`}
          className="inline-flex items-center gap-1.5 text-sm text-muted hover:text-accent"
        >
          <ArrowLeft size={15} /> Mahsulotga qaytish
        </Link>

        <div className="mt-6 flex flex-col items-center gap-4 rounded-card border border-border bg-surface p-8 text-center">
          {isPaid && (
            <>
              <CheckCircle2 size={48} className="text-green-400" />
              <h1 className="text-xl font-bold text-fg">
                To&apos;lov qabul qilindi
              </h1>
              <p className="text-sm text-muted">{order.product.title}</p>
              {order.downloadToken && (
                <a
                  href={`/api/download/${order.downloadToken}`}
                  className="mt-2 flex items-center gap-2 rounded-lg bg-accent px-6 py-3 font-medium text-white transition hover:bg-accent-hover"
                >
                  <Download size={16} /> Yuklab olish
                </a>
              )}
            </>
          )}

          {isPending && (
            <>
              <Clock size={48} className="animate-pulse text-gold" />
              <h1 className="text-xl font-bold text-fg">
                To&apos;lov kutilmoqda
              </h1>
              <p className="text-sm text-muted">
                Click orqali to&apos;lovni tasdiqlang. Bu sahifa avtomatik
                yangilanadi.
              </p>
            </>
          )}

          {isFailed && (
            <>
              <XCircle size={48} className="text-red-400" />
              <h1 className="text-xl font-bold text-fg">
                To&apos;lov amalga oshmadi
              </h1>
              <p className="text-sm text-muted">
                Qayta urinib ko&apos;ring yoki mahsulot sahifasiga qayting.
              </p>
            </>
          )}
        </div>
      </main>
    </>
  );
}
