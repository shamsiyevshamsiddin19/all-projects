import { NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { newFileKey, saveFile } from "@/lib/r2";
import { logError } from "@/lib/errorLog";
import { rateLimit, clientIp } from "@/lib/rateLimit";

const MAX_SIZE = 5 * 1024 * 1024; // 5MB

export async function POST(req: Request) {
  const session = await auth().catch(() => null);
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Tizimga kiring" }, { status: 401 });
  }

  if (!rateLimit(`upload-image:${clientIp(req)}`, 30, 60_000)) {
    return NextResponse.json(
      { error: "Juda ko'p so'rov. Birozdan so'ng qayta urinib ko'ring." },
      { status: 429 },
    );
  }

  const fd = await req.formData().catch(() => null);
  const file = fd?.get("file");
  if (!file || !(file instanceof File)) {
    return NextResponse.json({ error: "Fayl topilmadi" }, { status: 400 });
  }
  if (file.size > MAX_SIZE) {
    return NextResponse.json({ error: "Fayl 5MB dan katta" }, { status: 400 });
  }

  const allowedTypes = ["image/jpeg", "image/png", "image/webp"];
  if (!allowedTypes.includes(file.type)) {
    return NextResponse.json({ error: "Faqat JPG, PNG, WEBP rasmlar ruxsat etiladi" }, { status: 400 });
  }

  const ext = file.name.split('.').pop()?.toLowerCase() || 'jpg';

  try {
    const fileKey = newFileKey(`images/${session.user.id}`, ext);
    const buffer = Buffer.from(await file.arrayBuffer());
    await saveFile(fileKey, buffer);
    return NextResponse.json({ url: `/api/images/${fileKey}` });
  } catch (e) {
    await logError(e, "POST /api/upload-image");
    return NextResponse.json({ error: "Server xatosi" }, { status: 500 });
  }
}
