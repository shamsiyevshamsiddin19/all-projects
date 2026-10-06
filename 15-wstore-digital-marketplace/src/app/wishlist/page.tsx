import Link from "next/link";
import { Heart } from "lucide-react";
import Navbar from "@/components/Navbar";
import ProductCard from "@/components/ProductCard";
import { auth } from "@/lib/auth";
import { getWishlistProducts } from "@/lib/products";

export default async function WishlistPage() {
  const session = await auth().catch(() => null);

  if (!session?.user) {
    return (
      <>
        <Navbar />
        <main className="mx-auto max-w-[1100px] px-6 py-10">
          <h1 className="text-2xl font-bold text-fg">Sevimlilar</h1>
          <div className="mt-6 rounded-card border border-border bg-surface p-8 text-center">
            <p className="mb-4 text-muted">
              Sevimlilarni ko&apos;rish uchun tizimga kiring.
            </p>
            <Link
              href="/login"
              className="inline-block rounded-lg bg-accent px-5 py-2.5 text-sm font-medium text-white hover:bg-accent-hover"
            >
              Google bilan kirish
            </Link>
          </div>
        </main>
      </>
    );
  }

  const products = await getWishlistProducts(session.user.id);
  const wishlistIds = products.map((p) => p.id);

  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-[1100px] px-6 py-10">
        <h1 className="flex items-center gap-2 text-2xl font-bold text-fg">
          <Heart size={22} className="fill-red-400 text-red-400" /> Sevimlilar
        </h1>
        <p className="mt-1 text-sm text-muted">
          Keyinroq ko&apos;rish uchun belgilagan mahsulotlaringiz.
        </p>

        {products.length === 0 ? (
          <div className="mt-6 rounded-card border border-dashed border-border p-12 text-center text-muted">
            Hozircha bo&apos;sh. Mahsulot ustidagi{" "}
            <Heart size={13} className="inline" /> belgisini bosing.
          </div>
        ) : (
          <div className="mt-6 grid grid-cols-2 gap-3 sm:gap-5 lg:grid-cols-3">
            {products.map((p) => (
              <ProductCard key={p.id} product={p} wishlisted loggedIn />
            ))}
          </div>
        )}
      </main>
    </>
  );
}
