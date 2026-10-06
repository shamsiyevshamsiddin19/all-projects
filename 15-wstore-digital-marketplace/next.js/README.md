# wstore.uz

Raqamli mahsulotlar marketi — tayyor kod loyihalari, botlar, saytlar, ilovalar va kod bloklarini sotish platformasi.

## Texnologiyalar

- **Next.js 15** (App Router) + React 19 + TypeScript
- **TailwindCSS** — dark tema (marketpleys uslubi)
- **Prisma ORM** + **PostgreSQL**
- **Auth.js (NextAuth v5)** — Google OAuth, avtomatik ro'yxatdan o'tish

## Ishga tushirish

```bash
# 1. Paketlarni o'rnatish
npm install

# 2. Muhit sozlamalari
cp .env.example .env
#   - DATABASE_URL      (PostgreSQL connection string)
#   - AUTH_SECRET       (npx auth secret)
#   - AUTH_GOOGLE_ID / AUTH_GOOGLE_SECRET  (Google Cloud Console)

# 3. Prisma client generatsiyasi
npm run db:generate

# 4. (Baza tayyor bo'lsa) sxemani yuklash + seed
npm run db:push
npm run db:seed

# 5. Dev server
npm run dev
```

> Katalog sahifasi namunaviy ma'lumot (`src/lib/mock-data.ts`) bilan ishlaydi —
> ya'ni bazasiz ham `npm run dev` ochiladi. Auth va real mahsulotlar uchun
> PostgreSQL + Google kalitlari kerak.

## Google OAuth sozlash

1. https://console.cloud.google.com → **APIs & Services → Credentials**
2. **Create OAuth client ID** → Application type: **Web application**
3. Authorized redirect URI:
   `http://localhost:3000/api/auth/callback/google`
4. Client ID / Secret ni `.env` ga qo'ying.

Birinchi kirishdayoq foydalanuvchi **avtomatik** yaratiladi (PrismaAdapter).

## Struktura

```
src/
├─ app/
│  ├─ page.tsx                 # Katalog (filter + grid)
│  ├─ login/                   # Google bilan kirish
│  ├─ product/[slug]/          # Mahsulot sahifasi
│  ├─ dashboard/               # Xaridor kabineti
│  ├─ seller/                  # Sotuvchi paneli
│  └─ api/auth/[...nextauth]/  # Auth.js
├─ components/                 # Navbar, Catalog, FilterSidebar, ProductCard
└─ lib/                        # prisma, auth, mock-data, types
prisma/schema.prisma          # DB modellari
```

## Bajarilgan funksiyalar

- [x] Katalog: dark UI, filter (narx/kategoriya/texnologiya), saralash
- [x] Google OAuth + avtomatik ro'yxatdan o'tish (Auth.js)
- [x] Iconlar: `lucide-react` (emoji o'rniga)
- [x] Katalog bazadan (`getProducts`, mock fallback bilan)
- [x] To'lov: Payme / Click / Uzum havola generatsiyasi + webhook'lar
      (`/api/checkout`, `/api/payment/payme`, `/api/payment/click`)
- [x] Cloudflare R2 — kod .zip saqlash + xavfsiz yuklab olish (`/api/download/[token]`)
- [x] Sotuvchi paneli: mahsulot qo'shish formasi + statistika + moderatsiya (PENDING)

## To'lov oqimi

1. Xaridor mahsulot sahifasida provayder (Payme/Click/Uzum) tanlab "Sotib olish" bosadi
2. `/api/checkout` — `Order` (PENDING) yaratadi, to'lov havolasini qaytaradi
3. Xaridor to'lovni amalga oshiradi → provayder **webhook** yuboradi
4. Webhook `Order.status = PAID` qiladi va `downloadToken` faollashadi
5. Kabinetda yuklab olish tugmasi → `/api/download/<token>` → R2 dan 10 daqiqalik havola

> ⚠️ Webhook'larda **signature tekshiruvi** (Payme: `PAYME_KEY`, Click: MD5 `sign_string`)
> ishlab chiqarishdan oldin to'ldirilishi shart — kod ichida `TODO` bilan belgilangan.

## Deploy (Vercel + Neon)

1. **Baza** — [neon.tech](https://neon.tech) yoki [railway.app](https://railway.app) da PostgreSQL yarating, `DATABASE_URL` ni oling.
2. **Repo** — GitHub'ga yuklang.
3. **Vercel** — [vercel.com](https://vercel.com) da import qiling, Environment Variables ga `.env` dagi barcha kalitlarni qo'ying (`APP_URL` ni real domenga sozlang).
4. **Google OAuth** — redirect URI ga qo'shing: `https://wstore.uz/api/auth/callback/google`
5. **Webhook URL'lari** — Payme/Click kabinetida:
   - Payme: `https://wstore.uz/api/payment/payme`
   - Click: `https://wstore.uz/api/payment/click`
6. Deploy'dan so'ng migratsiya: `npx prisma migrate deploy` va `npm run db:seed`.
