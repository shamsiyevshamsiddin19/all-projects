import Link from "next/link";
import { notFound, redirect } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import Navbar from "@/components/Navbar";
import ProductForm from "@/app/seller/new/ProductForm";
import { auth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";

export default async function EditProductPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const session = await auth().catch(() => null);
  if (!session?.user?.id) redirect("/login");

  const product = await prisma.product
    .findUnique({ where: { id }, include: { category: true } })
    .catch(() => null);

  if (
    !product ||
    (product.sellerId !== session.user.id && session.user.role !== "ADMIN")
  )
    notFound();

  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-[1100px] px-6 py-10">
        <Link
          href="/seller"
          className="inline-flex items-center gap-1.5 text-sm text-muted hover:text-accent"
        >
          <ArrowLeft size={15} /> Sotuvchi paneliga qaytish
        </Link>
        <h1 className="mb-6 mt-4 text-2xl font-bold text-fg">
          Loyihani tahrirlash
        </h1>
        <ProductForm
          initial={{
            id: product.id,
            title: product.title,
            price: Number(product.price),
            categorySlug: product.category.slug,
            subcategory: product.subcategory,
            description: product.description,
            techStack: product.techStack,
            features: product.features,
            coverImage: product.coverImage,
            screenshots: product.screenshots,
            demoUrl: product.demoUrl,
            telegramUsername: product.telegramUsername,
            hasFile: Boolean(product.fileKey),
          }}
        />
      </main>
    </>
  );
}
