# 04 — Frontend: Next.js 15 + MapLibre globus

## 1. Nega MapLibre GL v5, Globe.gl emas?

| Mezon | MapLibre GL v5 | Globe.gl (three.js) |
| :--- | :--- | :--- |
| 3D globus | ✅ `globe` projection | ✅ asosiy funksiyasi |
| Globus → tekis xarita o'tishi | ✅ zoomda avtomatik, silliq | ❌ yo'q |
| Davlat polygon hover/click | ✅ `feature-state` + `queryRenderedFeatures` | ✅ `onPolygonClick` |
| Choropleth (data-driven rang) | ✅ ifoda (expression) bilan | ⚠️ qo'lda |
| Basemap / API key | ❌ kerak emas (faqat GeoJSON) | ❌ kerak emas |
| Zoom-to-country animatsiya | ✅ `fitBounds` tayyor | ⚠️ qo'lda yozish |
| Vizual "kosmik" effekt | ⚠️ oddiyroq | ✅ chiroyliroq (extrusion, glow) |

**Tanlov: MapLibre GL v5.** Sabab — bizning UX "globus → davlat → kanallar" zoom
harakatiga tayanadi, MapLibre'da bu tayyor. Globe.gl chiroyliroq, lekin zoom-to-country,
labellar va chegara holatlarini qo'lda yozish kerak bo'ladi.

**Basemap olinmaydi:** faqat `countries.geojson` fill + line layer + atmosfera.
Natijada tile server, API key va oylik to'lov yo'q, globus esa "ma'lumot globusi"
ko'rinishini oladi — bizning maqsadga aynan mos.

---

## 2. ⚠️ Eng katta ziddiyat: globus SEOga qarshi ishlaydi

Siz SEO uchun Next.js tanladingiz, lekin **WebGL canvas Google uchun mutlaqo bo'sh**.
Bu ikki qaror bir-biriga qarshi. Ziddiyat arxitektura darajasida hal qilinadi:

### 2.1 Globus — navigatsiyaning yagona yo'li bo'lmasin
Globus ostida/yonida **haqiqiy HTML havolalar** ro'yxati turadi:

```html
<!-- SSR'da, HTMLda, Google ko'radi -->
<nav aria-label="Davlatlar">
  <a href="/radio/uzbekistan">🇺🇿 O'zbekiston <span>42</span></a>
  <a href="/radio/russia">🇷🇺 Rossiya <span>1204</span></a>
</nav>
```

Google shu havolalar orqali yuradi, odam globus orqali. Ikkisi bir xil URL ga olib boradi.

### 2.2 SEO kontenti alohida sahifalarda
- `/radio/[country]` — davlat sahifasi, to'liq SSR, kanallar ro'yxati HTMLda
- `/radio/[country]/[station]` — stansiya sahifasi
- `JSON-LD` strukturali ma'lumot (`RadioStation`, `BroadcastService`)
- `sitemap.xml` — DBdan generatsiya (davlatlar + barcha stansiyalar)
- Har sahifada bitta `<h1>`, to'g'ri `<h2>/<h3>` ierarxiyasi, rasmlar uchun `alt`

### 2.3 LCP ni canvas buzmasin
Globus `dynamic(() => import('@/components/Globe'), { ssr: false })` bilan yuklanadi.
Birinchi bo'yoqda **matn** turadi (sarlavha + davlatlar ro'yxati), canvas keyin keladi.

> Aks holda Core Web Vitals pasayadi va SEO'dan yo'qotganingiz globusdan olganingizdan
> ko'p bo'ladi.

### 2.4 WebGL fallback majburiy
Arzon Androidda WebGL yoki sekin, yoki yo'q. Fallback shartlari:
- WebGL mavjud emas
- `prefers-reduced-motion: reduce`
- Ekran kengligi < 640px (mobil UX uchun globus noqulay)

Fallback — tekis qidiruvli davlatlar ro'yxati (yoki yengil SVG xarita). **Va aynan shu
fallback SEO versiyasi bo'ladi** — bitta yechim ikki muammoni hal qiladi.

---

## 3. ⚠️ Ikkinchi hayotiy qaror: pleyer hech qachon unmount bo'lmaydi

Radio sayti uchun bu eng muhim texnik talab:

> Foydalanuvchi Braziliya radiosini tinglab turib Yaponiyani bossa — **musiqa
> to'xtamasligi kerak.**

Buni keyin qo'shish og'riqli refactor. Boshidan shunday qurish kerak:

```
app/layout.tsx                     ← root layout
├── <GlobeShell>                   ← globus, navigatsiyada qayta yuklanmaydi
│   └── {children}                 ← faqat yon panel o'zgaradi
└── <PlayerBar />                  ← bitta <audio>, DOM'da doimiy
```

- Bitta `<audio>` elementi root layoutda, hech qachon unmount bo'lmaydi
- Holat **Zustand**'da: `currentStation`, `isPlaying`, `volume`, `history`
- Pastda doimiy pleyer bari (Spotify uslubida)
- **`MediaSession API`** — mobil lock-screenda stansiya nomi, logo, play/pause tugmalari
- `localStorage` — oxirgi tinglangan stansiya, ovoz balandligi, sevimlilar

### Navigatsiya naqshi
Globusda davlat bosilganda `router.push('/radio/uzbekistan')` chaqiriladi:
- URL o'zgaradi → **ulashiladigan va SEO'li**
- Globus layoutda bo'lgani uchun **qayta yuklanmaydi**, holatini saqlaydi
- Faqat yon panel server component sifatida qayta render bo'ladi
- To'g'ridan-to'g'ri shu URL ga kirilsa — to'liq SSR sahifa (Google uchun)

---

## 4. Loyiha tuzilmasi

```
apps/web/
├── app/
│   ├── layout.tsx                 GlobeShell + PlayerBar
│   ├── page.tsx                   bosh sahifa (globus + davlatlar ro'yxati)
│   ├── radio/
│   │   └── [country]/
│   │       ├── page.tsx           davlat sahifasi (SSR)
│   │       └── [station]/page.tsx stansiya sahifasi (SSR)
│   ├── sitemap.ts
│   └── robots.ts
├── components/
│   ├── globe/
│   │   ├── Globe.tsx              MapLibre init (client-only)
│   │   ├── useGlobeLayers.ts      fill/line/choropleth layerlari
│   │   └── GlobeFallback.tsx      WebGL yo'q bo'lganda
│   ├── player/
│   │   ├── PlayerBar.tsx
│   │   ├── useAudioEngine.ts      <audio> + hls.js boshqaruvi
│   │   └── mediaSession.ts
│   └── station/
│       ├── StationList.tsx
│       └── StationCard.tsx
├── stores/
│   └── player.ts                  Zustand
└── lib/
    ├── api.ts                     typed fetch wrapper
    └── seo.ts                     metadata + JSON-LD helperlari
```

---

## 5. Audio dvigatel (audio engine)

```
play(station)
  │
  ├─ POST /api/v1/play { stream_id }  →  play_url (imzolangan)
  │
  ├─ kind === 'hls'  →  hls.js bilan ulash
  ├─ aks holda       →  <audio src={play_url}>
  │
  ├─ xato (error / stalled / 30s timeout)
  │     └─ keyingi zaxira oqimga avtomatik o'tish
  │            └─ barchasi tugasa: "Bu stansiya vaqtincha ishlamayapti"
  │                   └─ backendga xabar beriladi (health checker uchun signal)
  └─ MediaSession metadata yangilanadi
```

**Nozik nuqtalar:**
- Ba'zi radiolar HLS'da (`.m3u8` audio) → `hls.js` **radio uchun ham** kerak, faqat TV emas
- Mobil brauzerlar foydalanuvchi harakatisiz audio ijro etmaydi (autoplay policy) —
  avtomatik ijro faqat `click` hodisasi ichida boshlanishi kerak
- Oqim uzilganda brauzer `error` bermasligi mumkin, faqat "qotib" qolishi mumkin →
  `stalled` / `waiting` hodisalariga 30 sekundlik timeout qo'yish shart
- Frontend `/api/v1/play` dan kelgan xatoni foydalanuvchiga **darhol ko'rsatmaydi** —
  avval barcha zaxira oqimlarni sinab ko'radi

---

## 6. Dizayn yo'nalishi

`MY_SCILL/preferences/websites.md` qoidalariga muvofiq:

- **Dark, "kosmik" mavzu** — globus kosmosda turgandek: fon `#05070d` → `#0a0f1c` gradient
- **Glassmorphism panel** — yon panel `backdrop-filter: blur(20px)`,
  `border: 1px solid rgba(255,255,255,0.08)`
- **Aksent** — har davlatning choropleth rangi: kanal soni ko'p bo'lsa quyuqroq neon
  (masalan `#38bdf8` → `#0ea5e9` → `#0369a1`)
- **Tipografiya** — Google Fonts: `Outfit` (sarlavhalar) + `Inter` (matn)
- **Mikro-animatsiyalar** — globus hover'da davlat yorishadi, panel o'ngdan silliq
  chiqadi, pleyer barida ijro ekvalayzer animatsiyasi
- **Responsive** — mobilda globus o'rniga fallback ro'yxat, pleyer bari pastda fixed
