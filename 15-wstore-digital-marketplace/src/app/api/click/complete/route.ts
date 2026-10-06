import { NextResponse } from "next/server";
import { handleClickComplete } from "@/lib/clickBridge";

// POST /api/click/complete — myxvest ko'prigidan (wstore_bridge.php) keladi.
export async function POST(req: Request) {
  const result = await handleClickComplete(req);
  return NextResponse.json(result);
}
