import { randomUUID } from "crypto";
import { promises as fs } from "fs";
import path from "path";

// Fayllar Cloudflare'da EMAS — shu serverning o'z diskida saqlanadi
// (UPLOAD_DIR, standart: <loyiha>/uploads). Bu papka `src` deploy jarayoniga
// kirmaydi — versiyalar orasida saqlanib qoladi.
const UPLOAD_DIR = process.env.UPLOAD_DIR || path.join(process.cwd(), "uploads");

function resolveSafe(fileKey: string): string {
  const base = path.resolve(UPLOAD_DIR);
  const full = path.resolve(base, fileKey);
  if (!full.startsWith(base + path.sep) && full !== base) {
    throw new Error("Noto'g'ri fayl yo'li");
  }
  return full;
}

/** Yangi, taxmin qilib bo'lmaydigan fileKey yaratadi (masalan "products/<userId>/<uuid>.zip"). */
export function newFileKey(prefix: string, ext = "zip"): string {
  return `${prefix}/${randomUUID()}.${ext}`;
}

/** Faylni diskka yozadi, kerakli papkalarni o'zi yaratadi. */
export async function saveFile(fileKey: string, buffer: Buffer): Promise<void> {
  const full = resolveSafe(fileKey);
  await fs.mkdir(path.dirname(full), { recursive: true });
  await fs.writeFile(full, buffer);
}

/** Faylni diskdan o'qiydi (topilmasa xato tashlaydi). */
export async function readStoredFile(fileKey: string): Promise<Buffer> {
  return fs.readFile(resolveSafe(fileKey));
}
