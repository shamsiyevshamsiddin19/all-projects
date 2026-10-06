import { prisma } from "@/lib/prisma";

// Kutilmagan server xatoliklarini o'z bazasiga yozadi (Sentry kabi tashqi
// xizmat shart emas). Bu funksiya hech qachon exception tashlamaydi —
// xatolikni faqat console'ga yozib qo'ya qoladi.
export async function logError(err: unknown, context: string): Promise<void> {
  try {
    const message = err instanceof Error ? err.message : String(err);
    const stack = err instanceof Error ? err.stack : undefined;
    await prisma.errorLog.create({
      data: { message: message.slice(0, 2000), stack: stack?.slice(0, 5000), context },
    });
  } catch (e) {
    console.error("logError xato yozib bo'lmadi:", e);
  }
  console.error(`[${context}]`, err);
}
