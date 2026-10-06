import { PrismaClient } from '@prisma/client';
const prisma = new PrismaClient();
async function main() {
  const seller = await prisma.user.findFirst({ where: { role: 'SELLER' } });
  if (!seller) return;
  const categories = await prisma.category.findMany();
  for (let i = 26; i <= 100; i++) {
    const c = categories[i % categories.length];
    await prisma.product.upsert({
      where: { slug: `extra-project-${i}` },
      update: {},
      create: {
        title: `Qo'shimcha loyiha ${i}`,
        slug: `extra-project-${i}`,
        description: `Bu sinov uchun qo'shilgan ${i}-loyiha.`,
        price: 15 + i,
        categoryId: c.id,
        techStack: ['React', 'Node.js', 'PostgreSQL'].slice(0, (i % 3) + 1),
        coverImage: 'https://images.unsplash.com/photo-1498050108023-c5249f4df085?auto=format&fit=crop&w=600&q=80',
        fileKey: 'products/dummy.zip',
        rating: 4.0 + (i % 10) / 10,
        salesCount: i * 5,
        sellerId: seller.id,
        status: 'ACTIVE',
      }
    });
  }
  console.log('75 ta yangi loyiha qoshildi! Jami mahsulotlar endi 100 ta atrofida.');
}
main().finally(() => prisma.$disconnect());
