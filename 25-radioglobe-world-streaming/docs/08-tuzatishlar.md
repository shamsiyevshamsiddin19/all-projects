# 08 — Tuzatilgan muammolar ro'yxati (audit natijasi)

2026-10-13 da jonli saytda va lokal kodda o'tkazilgan auditda topilgan 45 ta
muammo va ularning holati. Har bir band kod bilan tasdiqlangan.

---

## 🔴 A. Xavfsizlik

| # | Muammo | Holat | Qayerda |
| :-- | :--- | :--- | :--- |
| A1 | Production sirlari ochiq repoda (`PROXY_SECRET_KEY`, DB paroli) | ✅ | `infra/docker-compose.yml` endi faqat `${VAR}` o'qiydi, qiymatlar `infra/.env` da |
| A2 | Postgres (5432) va Redis (6379) portlari tashqariga ochiq, Redis parolsiz | ✅ | portlar `expose` ga o'tkazildi, Redis'ga `requirepass`, api/web `127.0.0.1` ga bog'landi |
| A3 | CORS `allow_origins=["*"]` + `allow_credentials=True` | ✅ | `settings.ALLOWED_ORIGINS`, `allow_credentials=False`, `"*"` validator bilan taqiqlandi |
| A4 | SSRF: redirect qayta tekshirilmasdi, faqat bitta IPv4 resolve qilinardi | ✅ | redirect zanjiri qo'lda kuzatiladi, har qadam tekshiriladi; `getaddrinfo` bilan barcha IP |
| A5 | Proxy ochiq relay: Referer tekshiruvi va limit yo'q | ✅ | Origin/Referer tekshiruvi, IP bo'yicha parallel oqim va `/play` rate limiti |
| A6 | Xavfsizlik header'lari umuman yo'q | ✅ | FastAPI middleware + `infra/nginx.conf` (HSTS, CSP, X-Frame-Options, nosniff) |
| A7 | Kodda zaxira secret — `.env` bo'lmasa jim ishlab ketardi | ✅ | productionda kalitsiz ishga tushmaydi (fail-closed) |
| A8 | `/health` ichki xato matnlarini oshkor qilardi | ✅ | faqat `ok`/`error`, tafsilot logga |

## 🔴 B. Ishlamayotgan funksiyalar

| # | Muammo | Holat | Izoh |
| :-- | :--- | :--- | :--- |
| B1 | Bosh sahifada "JAMI SEKTORLAR: 0" — build xatosi jim yutilgan | ✅ | `api.ts` xatoni logga yozadi; `revalidate=600`; deploydan keyin `/api/revalidate` |
| B2 | Globus choropleth o'lik (barcha `radio_count: 0`) | ✅ | globus API'dan jonli hisoblagich oladi |
| B3 | `/map/countries.geojson` ishlatilmasdi va `m49` bo'yicha bog'lanmasdi | ✅ | frontend shu endpointni o'qiydi, GeoJSON'da `m49` bor |
| B4 | Globusda 177 davlat, bazada 40 → 137 tasi 404 berardi | ✅ | bazada 252 davlat, barcha sahifalar 200 |
| B5 | GeoJSON'da `slug` yo'q, click handler nomdan yasardi | ✅ | `slug` GeoJSON ichida |
| B6 | Worker konteyneri ishga tushmasdi (`ModuleNotFoundError`) | ✅ | build konteksti `apps` ga o'zgartirildi + `scheduler.py` |
| B7 | Health checker navbati `last_ok_at` bo'yicha — o'lik oqimlar abadiy aylanardi | ✅ | `next_check_at` + exponential backoff |
| B8 | Ingest faqat qo'shardi: yangilash va arxivlash yo'q | ✅ | UUID bo'yicha UPSERT, arxivlash, 14 732 stansiya |
| B9 | `robots.txt` va `sitemap.xml` yo'q | ✅ | `app/robots.ts`, `app/sitemap.ts` (243 URL) |
| B10 | Bosh sahifada `<h1>` yo'q, SSR'da bitta ham `/radio/` havolasi yo'q | ✅ | 1 ta `<h1>`, 240 ta havola, canonical, JSON-LD |

## 🟠 C. Arxitektura

| # | Muammo | Holat | Izoh |
| :-- | :--- | :--- | :--- |
| C1 | Globus layoutda emas — navigatsiyada qayta yuklanadi | ⚠️ **Qisman** | Pleyer layoutda va **musiqa to'xtamaydi**. Globusning o'zi hamon qayta yuklanadi — buni to'liq hal qilish Next.js intercepting routes bilan alohida ish |
| C2 | Alembic yo'q, `create_all` ishlatilardi | ✅ | `alembic/` + `0001_initial_schema.py`, productionda `alembic upgrade head` |
| C3 | `stream_checks` partitsiyalanmagan | ✅ | oylik `RANGE` partitsiya + avtomatik yaratish/o'chirish |
| C4 | `JSON` ishlatilgan, GIN indeks yo'q | ✅ | `JSONB` + GIN indekslar |
| C5 | `pg_trgm` yo'q, qidiruv to'liq skan qilardi | ✅ | `pg_trgm` + `ix_channels_name_trgm` |
| C6 | Redis keshlash umuman yo'q | ✅ | `services/cache.py`, countries/map/detail keshlanadi |
| C7 | Repoda Caddyfile, serverda nginx | ✅ | `infra/nginx.conf` (production bilan mos) |
| C8 | Stansiya sahifasi yo'q | ✅ | `/stansiya/[station]` + `RadioStation` JSON-LD |

## 🟡 D. Unumdorlik

| # | Muammo | Holat |
| :-- | :--- | :--- |
| D1 | N+1 so'rov (50 kanal = 51 so'rov) | ✅ `selectinload` |
| D2 | `map.py` har so'rovda 200 KB faylni sinxron parse qilardi | ✅ xotirada bir marta |
| D3 | Davlat hisobi 250 ta `UPDATE` | ✅ bitta `GROUP BY` |
| D4 | Globus har kadrda `setCenter` (60 fps) | ✅ ~20 fps, vaqtga bog'liq, fon tabda to'xtaydi, foydalanuvchi tegsa pauza |
| D5 | `mousemove` da render bo'roni | ✅ kadrga bir marta (`requestAnimationFrame`) |
| D6 | `countries/{slug}` har so'rovda teglarni qayta hisoblardi | ✅ keshlanadi |

## 🟡 E. Pleyer

| # | Muammo | Holat | Izoh |
| :-- | :--- | :--- | :--- |
| E1 | `play()` fetch `.then()` ichida — mobil autoplay bloklardi | ✅ `audioEngine` singleton, ijro bosish hodisasining o'zida |
| E2 | Zaxira oqimga avtomatik o'tish yo'q | ✅ `fallback_streams` + `advanceToFallback()` |
| E3 | Stalled timeout yo'q | ✅ 30 soniya |
| E4 | `crossOrigin` yo'q — Web Audio ishlamasdi | ✅ `crossOrigin="anonymous"` |
| E5 | `AudioVisualizer` soxta (CSS animatsiya) | ✅ haqiqiy `AnalyserNode` spektri |
| E6 | `localStorage` try/catch'siz + hydration mismatch | ✅ `hydrate()` namunasi |
| E7 | Logolarning ~16% `http://` — bloklanardi | ✅ ingest http logoni saqlamaydi, `StationLogo` zaxira belgi ko'rsatadi |

## 🟢 F. Ma'lumot sifati

| # | Muammo | Holat | Natija |
| :-- | :--- | :--- | :--- |
| F1 | Katalog 227 stansiya / 19 davlat | ✅ | **14 732 stansiya / 240 davlat** |
| F2 | `name_uz` = `name_en` | ✅ | 203 davlat uchun o'zbekcha nom |
| F3 | `total` sahifa hajmini qaytarardi | ✅ | alohida `COUNT` |
| F4 | Sahifada ikki xil raqam | ✅ | yagona manba (`channels.total`) |
| F5 | `cursor` aslida `OFFSET` edi | ✅ | keyset paginatsiya |
| F6 | Yangi oqimda `score=95` (tekshirilmagan holda) | ✅ | `score=50`, health checker aniqlaydi |
| F7 | JSON-LD tipi noto'g'ri | ✅ | `CollectionPage` + `ItemList` + `RadioStation` |
| F8 | Tafsilotda `score` filtri yo'q | ✅ | qo'shildi |
| F9 | Faol oqimsiz kanal ro'yxatda qolardi | ✅ | `EXISTS` filtri bilan chiqarib tashlandi |

---

## Qolgan ish

**C1 (globus layoutda)** — yagona to'liq bajarilmagan band. Hozirgi holat:
pleyer root layoutda va sahifalar orasida yurganda **musiqa uzilmaydi** (bu
asosiy talab edi). Lekin globusning o'zi `/` sahifasida bo'lgani uchun
davlat sahifasidan qaytganda qaytadan yuklanadi.

To'liq yechim — Next.js **intercepting routes** (`app/@panel/(.)radio/[country]`):
globusdan bosilganda davlat paneli globus ustida ochiladi, to'g'ridan-to'g'ri
URL bilan kirilganda esa to'liq SSR sahifa qaytadi. Bu alohida, ehtiyotkorlik
talab qiladigan ish — ishlayotgan davlat sahifasini buzib qo'ymaslik kerak.
