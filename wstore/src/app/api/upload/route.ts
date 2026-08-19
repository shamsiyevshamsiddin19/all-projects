import { NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { newFileKey, saveFile } from "@/lib/r2";
import { logError } from "@/lib/errorLog";
import { rateLimit, clientIp } from "@/lib/rateLimit";

const MAX_SIZE = 200 * 1024 * 1024; // 200MB

// POST /api/upload — sotuvchi mahsulot faylini (multipart/form-data, "file")
// to'g'ridan-to'g'ri serverga yuklaydi, diskka saqlaydi va fileKey qaytaradi.
export async function POST(req: Request) {
  const session = await auth().catch(() => null);
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Tizimga kiring" }, { status: 401 });
  }

  if (!rateLimit(`upload:${clientIp(req)}`, 15, 60_000)) {
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
    return NextResponse.json({ error: "Fayl 200MB dan katta" }, { status: 400 });
  }

  try {
    const fileKey = newFileKey(`products/${session.user.id}`);
    const buffer = Buffer.from(await file.arrayBuffer());
    await saveFile(fileKey, buffer);
    return NextResponse.json({ fileKey });
  } catch (e) {
    await logError(e, "POST /api/upload");
    return NextResponse.json({ error: "Server xatosi" }, { status: 500 });
  }
}
