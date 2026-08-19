import { redirect } from "next/navigation";

// Eski oqim (admin orqali qo'lda qo'shish) — endi sotuvchi o'zi /seller orqali
// loyiha qo'shadi. Eski havolalar/bookmark'lar buzilmasligi uchun redirect.
export default function LoyihaQoshishRedirect() {
  redirect("/seller");
}
