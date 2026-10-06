import { NextResponse } from "next/server";
import { readStoredFile } from "@/lib/r2";
import { logError } from "@/lib/errorLog";
import path from "path";

export async function GET(
  req: Request,
  { params }: { params: Promise<{ path: string[] }> },
) {
  try {
    const { path: p } = await params;
    const fileKey = p.join("/");

    // Fayl xavfsizligini r2.ts dagi readStoredFile tekshiradi
    const buffer = await readStoredFile(fileKey);

    const ext = path.extname(fileKey).toLowerCase();
    let contentType = "application/octet-stream";
    if (ext === ".jpg" || ext === ".jpeg") contentType = "image/jpeg";
    else if (ext === ".png") contentType = "image/png";
    else if (ext === ".webp") contentType = "image/webp";
    else if (ext === ".svg") contentType = "image/svg+xml";

    return new NextResponse(buffer as any, {
      headers: {
        "Content-Type": contentType,
        "Cache-Control": "public, max-age=86400, immutable",
      },
    });
  } catch (e) {
    // topilmasa 404
    return new NextResponse("Not Found", { status: 404 });
  }
}
