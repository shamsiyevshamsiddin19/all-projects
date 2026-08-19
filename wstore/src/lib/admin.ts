import { auth } from "@/lib/auth";

export interface AdminSession {
  userId: string;
}

// Joriy sessiya ADMIN rolimi? API route'larda ishlatiladi.
// null qaytsa — ruxsat yo'q (chaqiruvchi 401/403 beradi).
export async function requireAdmin(): Promise<AdminSession | null> {
  const session = await auth().catch(() => null);
  if (!session?.user?.id) return null;
  if (session.user.role !== "ADMIN") return null;
  return { userId: session.user.id };
}
