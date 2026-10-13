# 03 — API shartnomasi (FastAPI)

Barcha endpointlar `/api/v1` prefiksi ostida. Javoblar JSON. FastAPI OpenAPI sxemasidan
frontend uchun TypeScript tiplari generatsiya qilinadi (`openapi-typescript`).

---

## 1. Globus uchun ma'lumot

### `GET /api/v1/map/countries.geojson`

Globusga yuklanadigan yagona fayl: davlat chegaralari + kanal soni.

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "id": 860,
      "properties": {
        "m49": 860,
        "iso2": "UZ",
        "slug": "uzbekistan",
        "name_uz": "O'zbekiston",
        "name_en": "Uzbekistan",
        "radio_count": 42,
        "tv_count": 0
      },
      "geometry": { "type": "MultiPolygon", "coordinates": [] }
    }
  ]
}
```

**Optimizatsiya (muhim):**
- Geometriya `mapshaper` bilan soddalashtiriladi (110m darajasi)
- Keraksiz propertylar olib tashlanadi
- Brotli siqish bilan **~80–120 KB** bo'lishi kerak
- `Cache-Control: public, max-age=3600, stale-while-revalidate=86400`
- Geometriya o'zgarmaydi, faqat `*_count` o'zgaradi → build vaqtida statik generatsiya
  qilib, counterlarni alohida yengil endpointdan olish ham mumkin

### `GET /api/v1/map/counts`
Faqat raqamlar (geometriya yo'q) — choropleth'ni yangilash uchun, ~2 KB.

```json
{ "UZ": { "radio": 42, "tv": 0 }, "RU": { "radio": 1204, "tv": 0 } }
```

---

## 2. Davlatlar

### `GET /api/v1/countries`
Kanali bor davlatlar ro'yxati (SSR davlatlar ro'yxati va `sitemap.xml` uchun).

### `GET /api/v1/countries/{slug}`
```json
{
  "iso2": "UZ",
  "slug": "uzbekistan",
  "name_uz": "O'zbekiston",
  "flag_emoji": "🇺🇿",
  "centroid": [41.37, 64.58],
  "bbox": [55.9, 37.1, 73.1, 45.6],
  "radio_count": 42,
  "tv_count": 0,
  "top_tags": ["pop", "news", "folk"],
  "languages": ["uz", "ru"]
}
```

---

## 3. Kanallar

### `GET /api/v1/countries/{slug}/channels`

| Parametr | Qiymat | Izoh |
| :--- | :--- | :--- |
| `type` | `radio` \| `tv` | Default: `radio` |
| `sort` | `popular` \| `name` \| `bitrate` | Default: `popular` |
| `tag` | `pop`, `news`… | Janr filtri |
| `lang` | `uz`, `ru`… | Til filtri |
| `limit` / `cursor` | | Kursorli paginatsiya |

```json
{
  "items": [
    {
      "id": 1024,
      "slug": "uzbegim-taronasi",
      "name": "Uzbegim Taronasi",
      "logo_url": "https://cdn.../logo.png",
      "tags": ["pop", "folk"],
      "languages": ["uz"],
      "bitrate": 128,
      "score": 92,
      "stream": {
        "id": 5120,
        "kind": "mp3",
        "play_url": "/stream/5120?t=eyJhbGciOi..."
      }
    }
  ],
  "next_cursor": "MTAyNA==",
  "total": 42
}
```

### ⚠️ Nozik nuqta: API faqat *ishlaydigan* oqimni qaytaradi

So'rov `WHERE score > 20 AND is_archived = FALSE` sharti bilan ketadi va kanalning eng
yaxshi oqimini (`priority`, keyin `score DESC`) tanlab beradi. Frontend oqim tanlash
mantiqini bilmasligi kerak — u faqat `play_url` ni oladi.

Agar kanalning hech bir oqimi ishlamasa — kanal ro'yxatda **ko'rinmaydi**. Bu qattiq
qoida: foydalanuvchi ishlamaydigan kanalni ko'rmasligi kerak.

### `GET /api/v1/channels/{id}`
Bitta kanal + barcha oqimlari (zaxira havolalar bilan) + o'xshash kanallar.

---

## 4. Qidiruv

### `GET /api/v1/search?q=...`
`pg_trgm` bo'yicha kanal nomi + davlat nomi bo'yicha qidiruv. Natija guruhlangan:

```json
{
  "countries": [ { "slug": "uzbekistan", "name_uz": "O'zbekiston" } ],
  "channels":  [ { "id": 1024, "name": "Uzbegim Taronasi", "country_iso2": "UZ" } ]
}
```

Redis'da 5 daqiqa keshlanadi (so'rov matni kalit sifatida).

---

## 5. Ijro hodisasi

### `POST /api/v1/play`
```json
{ "stream_id": 5120 }
```

Javob:
```json
{
  "play_url": "/stream/5120?t=eyJhbGciOi...",
  "expires_in": 7200,
  "now_playing": null
}
```

Bu endpoint uch ishni bajaradi:
1. Redis'da ijro counterini oshiradi (`INCR play:5120:2026-10-13`)
2. Qisqa muddatli **imzolangan token** beradi (proxy shu tokenni tekshiradi)
3. Manba talabini bajaradi — radio-browser uchun ularning klik endpointini chaqiradi
   (bu ham jamiyatga hurmat, ham bizga ishlaydigan `url_resolved` ni beradi)

---

## 6. Oqim proxysi (FastAPI emas!)

### `GET /stream/{stream_id}?t={token}`

Bu **alohida servis** (nginx yoki Go). Qoidalar:

| Qoida | Nega |
| :--- | :--- |
| URL **parametr sifatida qabul qilinmaydi** | `?url=` qabul qilish = ochiq proxy + SSRF |
| Faqat `stream_id` → DB/Redis'dan URL olinadi | Faqat tasdiqlangan manzillar |
| Token imzolangan va 2 soatda tugaydi | Havolani boshqa saytga qo'yib bo'lmaydi |
| `Referer` / `Origin` tekshiriladi | Hotlinking'dan himoya |
| Private IP diapazonlari bloklanadi | SSRF himoyasining ikkinchi qatlami |
| IP bo'yicha rate limit (masalan 3 parallel oqim) | Resurs suiiste'molidan himoya |

Batafsil: [`06-tuzoqlar.md`](./06-tuzoqlar.md) → SSRF bo'limi.

---

## 7. Keshlash strategiyasi

| Endpoint | Kesh | TTL |
| :--- | :--- | :--- |
| `/map/countries.geojson` | CDN + brauzer | 1 soat / SWR 1 kun |
| `/map/counts` | Redis + CDN | 10 daqiqa |
| `/countries` | Redis | 1 soat |
| `/countries/{slug}/channels` | Redis | 5 daqiqa |
| `/search` | Redis | 5 daqiqa |
| `/play` | keshlanmaydi | — |
| `/stream/*` | keshlanmaydi (uzluksiz oqim) | — |

---

## 8. Xato formati

Barcha xatolar bir xil shaklda:

```json
{
  "error": {
    "code": "stream_unavailable",
    "message": "Bu oqim vaqtincha ishlamayapti",
    "detail": null
  }
}
```

Kodlar: `not_found`, `stream_unavailable`, `rate_limited`, `invalid_token`,
`geo_blocked`, `internal_error`.

Frontend `stream_unavailable` kelganda avtomatik **keyingi oqimga** (zaxira havolaga)
o'tadi, foydalanuvchiga xato ko'rsatishdan oldin.
