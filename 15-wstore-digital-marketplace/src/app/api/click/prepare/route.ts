import { NextResponse } from "next/server";
import { handleClickPrepare } from "@/lib/clickBridge";

// POST /api/click/prepare — myxvest ko'prigidan (wstore_bridge.php) keladi.
export async function POST(req: Request) {
  const result = await handleClickPrepare(req);
  return NextResponse.json(result);
}
