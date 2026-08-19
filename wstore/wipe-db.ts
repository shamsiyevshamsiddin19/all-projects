import { PrismaClient } from '@prisma/client';
const prisma = new PrismaClient();
async function main() {
  await prisma.wishlist.deleteMany();
  await prisma.review.deleteMany();
  await prisma.clickTransaction.deleteMany();
  await prisma.order.deleteMany();
  await prisma.report.deleteMany();
  const deleted = await prisma.product.deleteMany();
  console.log("Deleted count:", deleted.count);
  const remaining = await prisma.product.count();
  console.log("Remaining count:", remaining);
}
main().finally(() => prisma.$disconnect());
