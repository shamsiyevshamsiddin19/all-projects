import Navbar from "@/components/Navbar";
import Catalog from "@/components/Catalog";
import { getProducts } from "@/lib/products";
import { getWishlistIds } from "@/lib/wishlist";
import { auth } from "@/lib/auth";

export default async function HomePage() {
  const session = await auth().catch(() => null);
  const [products, wishlistIds] = await Promise.all([
    getProducts(),
    getWishlistIds(session?.user?.id),
  ]);
  const loggedIn = Boolean(session?.user);
  return (
    <>
      <Navbar />
      <main>
        <Catalog products={products} wishlistIds={wishlistIds} loggedIn={loggedIn} />
      </main>
    </>
  );
}
