import { revalidatePath } from 'next/cache';
import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

/**
 * Deploydan keyin keshni majburan yangilash.
 *
 * Kerakligi: bosh sahifa ISR bilan generatsiya qilinadi, lekin `next build`
 * paytida API hali ishga tushmagan bo'ladi. Shu sababli birinchi build bo'sh
 * ro'yxat bilan chiqadi va navbatdagi revalidate'gacha (10 daqiqa) shunday
 * qoladi. Deploy skripti shu endpointni chaqirib, sahifani darhol yangilaydi.
 *
 * Chaqirish:
 *   curl -X POST -H "X-Revalidate-Secret: $REVALIDATE_SECRET" \
 *     "https://radio.shamsiyev.uz/api/revalidate"
 */
export async function POST(request: Request) {
  const secret = process.env.REVALIDATE_SECRET;
  if (!secret) {
    return NextResponse.json(
      { error: 'REVALIDATE_SECRET sozlanmagan' },
      { status: 503 },
    );
  }

  // Sir query stringda bo'lsa nginx access logiga tushadi. Maxsus header esa
  // URL/log tarixida ko'rinmaydi.
  const provided = request.headers.get('x-revalidate-secret');
  if (provided !== secret) {
    return NextResponse.json({ error: 'Ruxsat yo\'q' }, { status: 401 });
  }

  revalidatePath('/');
  revalidatePath('/sitemap.xml');

  return NextResponse.json({ revalidated: true, at: new Date().toISOString() });
}
