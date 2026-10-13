# 01 — Tizim arxitekturasi

## 1. G'oya

Foydalanuvchi saytga kiradi → ekranda aylanuvchi 3D globus turadi → biror davlatni bosadi
→ yon panelda o'sha davlatning radiostansiyalari (keyinchalik TV kanallari) chiqadi →
bosib darhol tinglaydi. Pleyer sahifalar orasida yurganda ham to'xtamaydi.

## 2. Asosiy tushuncha: biz kontent saqlamaymiz

Bu loyihada video/audio fayllar **bizda saqlanmaydi**. Biz **havolalar katalogi**ni
qilamiz: kanal nomi, logo, davlati, tili, janri va oqim (stream) URL manzili.

Shundan kelib chiqib loyihaning eng qiyin qismi backend emas:

> **Eng qiyin qism — oqim manbalarining sifati va ularni brauzerda ijro etish.**

Butun arxitektura shu muammo atrofida qurilgan. Batafsil: [`06-tuzoqlar.md`](./06-tuzoqlar.md).

---

## 3. Komponentlar diagrammasi

```
┌──────────────────────────────────────────────────────────────┐
│  Next.js 15 (App Router)                                     │
│                                                              │
│  ┌────────────────────┐   ┌──────────────────────────────┐   │
│  │  MapLibre globus   │   │  Davlat / stansiya paneli    │   │
│  │  (client-only)     │   │  (SSR — SEO uchun)           │   │
│  └────────────────────┘   └──────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  Doimiy pleyer bari — root layoutda, unmount bo'lmaydi│    │
│  └──────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
        │ /api (katalog)                    │ /stream (audio)
        ▼                                   ▼
┌───────────────────────┐          ┌──────────────────────────┐
│  FastAPI              │          │  Audio Proxy             │
│  — katalog & qidiruv  │          │  (nginx yoki Go)         │
│  — davlat statistika  │          │  — imzolangan token      │
│  — play hodisasi      │          │  — stream_id bo'yicha    │
│  — sitemap manbasi    │          │  — SSRF himoyasi         │
└───────────────────────┘          └──────────────────────────┘
        │              │                        │
        ▼              ▼                        │ upstream
┌───────────────┐  ┌────────┐                   ▼
│ PostgreSQL 16 │  │ Redis  │          (stansiyaning o'z serveri)
└───────────────┘  └────────┘
        ▲
        │
┌───────────────────────────────────────┐
│  Worker (asyncio)                     │
│  — radio-browser sync (kunlik)        │
│  — health checker (backoff bilan)     │
│  — popularity agregatsiyasi           │
└───────────────────────────────────────┘
```

---

## 4. Har bir komponentning mas'uliyati

### 4.1 Next.js (frontend)
- Globus, davlat paneli, qidiruv, doimiy pleyer
- **SSR/ISR sahifalar** — `/radio/[country]`, `/radio/[country]/[station]` (SEO yuragi)
- `sitemap.xml` va `robots.txt` generatsiyasi
- Globus `dynamic(..., { ssr: false })` bilan yuklanadi — WebGL serverda ishlamaydi

Batafsil: [`04-frontend.md`](./04-frontend.md)

### 4.2 FastAPI (boshqaruv qatlami)
- Katalog o'qish: davlatlar, kanallar, qidiruv, filtrlar
- Globus uchun GeoJSON (kanal soni bilan birga)
- `POST /play` — ijro hodisasi: Redis counter + `url_resolved` qaytarish
- Imzolangan proxy token berish

**Muhim:** FastAPI **oqim trafigini o'tkazmaydi**. Faqat JSON.

### 4.3 Audio Proxy (alohida servis)
Bu eng muhim arxitektura qarori. Nega FastAPI ichida emas:

1. **Izolyatsiya** — 500 parallel audio oqim FastAPI worker'larini egallab qo'ymaydi,
   API latensiyasi oqim trafigidan ta'sirlanmaydi.
2. **Almashtirilishi** — keyinroq nginx → Go → Cloudflare Worker ga ko'chirish mumkin,
   backendga tegmasdan.
3. **Mas'uliyat ajratilishi** — biri ma'lumot beradi, ikkinchisi baytlarni oqizadi.

Vazifasi: HTTP→HTTPS ko'tarish, CORS header qo'shish, ICY metadata o'qish (2-bosqich).

### 4.4 Worker (fon vazifalari)
- **Ingest** — radio-browser bilan kunlik sinxronizatsiya
- **Health checker** — loyihaning yuragi (pastda alohida bo'lim)
- **Agregatsiya** — Redis'dagi play counter'larni PostgreSQL ga quyish

### 4.5 PostgreSQL + Redis
- PostgreSQL — yagona haqiqat manbasi (katalog, health tarixi, statistika)
- Redis — katalog javoblari keshi, play counter, rate limit, qidiruv keshi

---

## 5. Health checker — loyihaning yuragi

Radio/TV kataloglarining asosiy muammosi: **havolalar o'ladi.** Agar foydalanuvchi uch
marta bosib hech biri ishlamasa — u qaytib kelmaydi. Shuning uchun sifat = health checker.

### Ishlash printsipi
1. Oqimga ulanishga harakat qiladi (timeout 5s), birinchi baytlarni oladi
2. Natijani `stream_checks` ga yozadi
3. `streams` jadvalidagi denormalizatsiya maydonlarini yangilaydi:
   `last_ok_at`, `fail_count`, `score`

### Jadval (exponential backoff)
| Holat | Tekshirish chastotasi |
| :--- | :--- |
| Mashhur + ishlayotgan | har 10–15 daqiqa |
| Oddiy + ishlayotgan | har 1–2 soat |
| 3 martadan ko'p xato | har 6 soat |
| 7 kundan ko'p o'lik | kunda 1 marta |
| 30 kundan ko'p o'lik | arxivga (`is_archived`), ko'rsatilmaydi |

### Eng muhim g'oya: tekshiruv paytida *imkoniyatlar*ni ham yozib olish

Har tekshirishda shularni ham aniqlab, DB ga yozib qo'yamiz:

- `is_https` — HTTPS'mi?
- `sends_cors` — `Access-Control-Allow-Origin` beradimi?
- `is_geo_blocked` — 403 qaytaradimi?
- `needs_proxy` — yuqoridagilardan hisoblanadi

Shu bilan **og'ir runtime muammosi oddiy katalog sifati masalasiga aylanadi**:
frontendga faqat haqiqatda ijro etiladigan oqimlar yuboriladi. Brauzerda "ishlamadi"
degan holat kamayadi.

### Texnik cheklov
~50 000 oqimni tekshirish — `asyncio` + `Semaphore(50)`, `httpx` bilan. Butun bazani
bir yurishda emas, navbat (queue) bo'yicha ulushlab tekshiriladi.

---

## 6. Monorepo tuzilmasi (kelgusi)

```
25-radioglobe-world-streaming/
├── apps/
│   ├── web/            Next.js 15 + TypeScript + Tailwind
│   ├── api/            FastAPI (routers, services, schemas, db)
│   └── worker/         ingest + health checker
├── packages/
│   └── shared-types/   OpenAPI'dan generatsiya qilingan TS tiplar
├── infra/
│   ├── docker-compose.yml
│   ├── Caddyfile
│   └── proxy/          nginx conf yoki Go servis
└── docs/               ← hozirgi hujjatlar
```

**Nozik nuqta:** `packages/shared-types` — FastAPI OpenAPI sxemasidan TypeScript tiplarini
avtomatik generatsiya qilish (`openapi-typescript`). Shu bilan backend javob formati
o'zgarsa frontend build vaqtida xato beradi, runtime'da emas.

---

## 7. Infratuzilma

Docker Compose: `web`, `api`, `worker`, `proxy`, `postgres`, `redis`, `caddy`.

Server: Oracle Cloud yoki AWS EC2 (`~/Documents/shamsiyev/secret-key/servers` ga qarang).

**Yagona o'sadigan xarajat — egress (chiquvchi trafik).** Hisob-kitob:
- 1 tinglovchi × 128 kbps ≈ **57 MB/soat** ≈ 1.4 GB / 10 soat
- 100 parallel tinglovchi ≈ **12.8 Mbps**
- Oyiga 100 parallel × 8 soat/kun ≈ **1.4 TB/oy**

Serverni tanlashdan oldin egress limitini aniq tekshirish kerak.

---

## 8. Kuzatuv (observability)

- **Sentry** — frontend va backend xatolari
- **Prometheus + Grafana** yoki oddiy `/metrics`
- **Asosiy mahsulot metrikasi:** `ijro boshlangan / bosilgan` nisbati (play success rate).
  Bu raqam pasaysa — katalog buzilgan, health checker ishlamayapti.
