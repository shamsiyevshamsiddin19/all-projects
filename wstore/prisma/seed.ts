import { PrismaClient } from "@prisma/client";
import { PRODUCTS } from "../src/lib/mock-data";

const prisma = new PrismaClient();

async function main() {
  // 1) Kategoriyalar
  const categories = [
    { name: "Botlar", slug: "bot", icon: "bot" },
    { name: "Saytlar", slug: "website", icon: "globe" },
    { name: "Ilovalar", slug: "app", icon: "smartphone" },
    { name: "Kod bloklari", slug: "code", icon: "puzzle" },
    { name: "UI kitlar", slug: "uikit", icon: "palette" },
  ];

  for (const c of categories) {
    await prisma.category.upsert({
      where: { slug: c.slug },
      update: {},
      create: c,
    });
  }

  // 2) Namunaviy sotuvchi
  const seller = await prisma.user.upsert({
    where: { email: "seller@wstore.uz" },
    update: {},
    create: {
      email: "seller@wstore.uz",
      name: "wstore demo",
      role: "SELLER",
    },
  });

  // 3) Mahsulotlar (mock-data'dan bazaga)
  for (const p of PRODUCTS) {
    const category = await prisma.category.findUnique({
      where: { slug: p.category },
    });
    if (!category) continue;

    await prisma.product.upsert({
      where: { slug: p.slug },
      update: {},
      create: {
        title: p.title,
        slug: p.slug,
        description: `${p.title} — to'liq manba kodi bilan.`,
        price: p.price,
        categoryId: category.id,
        subcategory: p.subcategory ?? null,
        techStack: p.techStack,
        features: [],
        coverImage: p.coverImage,
        screenshots: [],
        fileKey: `products/${p.slug}.zip`,
        rating: p.rating,
        salesCount: p.salesCount,
        sellerId: seller.id,
        status: "ACTIVE",
      },
    });
  }

  console.log(
    `✅ Seed tugadi: ${categories.length} kategoriya, ${PRODUCTS.length} mahsulot`,
  );
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
