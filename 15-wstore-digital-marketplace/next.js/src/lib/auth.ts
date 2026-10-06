import NextAuth from "next-auth";
import Google from "next-auth/providers/google";
import { PrismaAdapter } from "@auth/prisma-adapter";
import { prisma } from "@/lib/prisma";

// Auth.js v5 (NextAuth) — Google orqali kirish + AVTOMATIK ro'yxatdan o'tish.
// PrismaAdapter birinchi kirishdayoq User yozuvini o'zi yaratadi —
// alohida "registratsiya" formasi kerak emas.
export const { handlers, auth, signIn, signOut } = NextAuth({
  adapter: PrismaAdapter(prisma),
  session: { strategy: "database" },
  // nginx orqasida (TLS proxy) ishlaydi — bu bo'lmasa pkceCodeVerifier/cookie
  // xatolari chiqadi (akkaunt almashtirganda "Server error" shu sabab edi).
  trustHost: true,
  providers: [
    Google({
      clientId: process.env.AUTH_GOOGLE_ID,
      clientSecret: process.env.AUTH_GOOGLE_SECRET,
      allowDangerousEmailAccountLinking: true,
      // har kirishda akkaunt tanlash oynasi (akkauntni almashtirish uchun)
      authorization: { params: { prompt: "select_account" } },
    }),
  ],
  pages: {
    signIn: "/login",
  },
  callbacks: {
    // sessiyaga foydalanuvchi id va rolini qo'shamiz
    async session({ session, user }) {
      if (session.user) {
        session.user.id = user.id;
        session.user.role = (user as { role?: string }).role ?? "BUYER";
      }
      return session;
    },
  },
});
