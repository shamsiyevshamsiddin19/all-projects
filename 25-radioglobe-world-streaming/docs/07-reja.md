# 07 — Bosqichlar rejasi (Roadmap)

Har bosqichda **"tayyor" mezoni** aniq belgilangan. Mezon bajarilmasa keyingi bosqichga
o'tilmaydi — aks holda yarim ishlaydigan funksiyalar to'planib qoladi.

---

## 🟦 0-bosqich — Poydevor (1 hafta)

**Maqsad:** loyiha skeleti va ma'lumotlar bazasi ishlab turishi.

- [ ] Monorepo tuzilmasi (`apps/web`, `apps/api`, `apps/worker`, `infra/`)
- [ ] `docker-compose.yml` — postgres, redis, api, web
- [ ] FastAPI skeleti + health endpoint + OpenAPI
- [ ] Alembic migratsiyalari — `countries`, `channels`, `channel_countries`, `streams`
- [ ] `countries` jadvalini to'ldirish (ISO2 + ISO3 + **M49** + nomlar + centroid + bbox)
- [ ] Next.js 15 skeleti + Tailwind + typed API client

**Tayyor mezoni:** `docker compose up` → `/api/v1/countries` 195 davlatni qaytaradi.

---

## 🟩 1-bosqich — Radio MVP (2 hafta)

**Maqsad:** tirik mahsulot — globusdan davlat bosilib, radio tinglanadi.

### Backend
- [ ] radio-browser ingest (User-Agent, mirror DNS, normalizatsiya, UPSERT)
- [ ] `GET /map/countries.geojson` (mapshaper bilan soddalashtirilgan, ~100 KB)
- [ ] `GET /countries/{slug}/channels` (faqat ishlaydigan oqimlar)
- [ ] `POST /play` — Redis counter + imzolangan token + radio-browser klik qaytarish
- [ ] Audio proxy (nginx yoki Go) — SSRF himoyasi bilan

### Frontend
- [ ] MapLibre GL v5 globus + choropleth (kanal soni bo'yicha rang)
- [ ] Davlat bosilganda yon panel + `router.push` navigatsiya
- [ ] **Doimiy pleyer** (root layout + Zustand + MediaSession)
- [ ] WebGL fallback — davlatlar ro'yxati
- [ ] Zaxira oqimga avtomatik o'tish mantiqi

**Tayyor mezoni:**
1. Globusdan 10 tasodifiy davlat tanlanadi → har birida kamida 1 stansiya ishlaydi
2. Radio tinglab turib boshqa davlatga o'tilsa → **musiqa to'xtamaydi**
3. Mobil telefonda (Android Chrome + iOS Safari) ijro ishlaydi
4. Lighthouse: Performance ≥ 80, SEO ≥ 95

---

## 🟨 2-bosqich — Sifat va SEO (1.5 hafta)

**Maqsad:** katalogni ishonchli qilish va organik trafikni ochish.

- [ ] **Health checker** — exponential backoff, `score`, imkoniyatlarni aniqlash
      (`is_https`, `sends_cors`, `is_geo_blocked`)
- [ ] `stream_checks` partitioning + eski partitionlarni tozalash
- [ ] `/radio/[country]` va `/radio/[country]/[station]` to'liq SSR + JSON-LD
- [ ] `sitemap.xml` (DBdan generatsiya) + `robots.txt`
- [ ] Qidiruv (`pg_trgm`) — kanal va davlat bo'yicha
- [ ] Filtrlar — janr (tag), til, bitrate
- [ ] Sevimlilar (`localStorage`, auth'siz) + oxirgi tinglanganlar
- [ ] Sentry + asosiy metrika dashboardi (play success rate)
- [ ] `/dmca` sahifasi + shikoyat formasi

**Tayyor mezoni:**
1. **Play success rate ≥ 90%** (ijro boshlangan / bosilgan)
2. Google Search Console'da davlat sahifalari indekslangan
3. Arxivlangan (o'lik) oqimlar ro'yxatda ko'rinmaydi

---

## 🟧 3-bosqich — TV (2–3 hafta)

**Maqsad:** TV kanallarini qo'shish — **lekin faqat 2-bosqich mezonlari bajarilgandan keyin.**

- [ ] iptv-org ingest
- [ ] HLS proxy (manifest qayta yozish — segment URL'larini proxy orqali yo'naltirish)
- [ ] `hls.js` video pleyer + sifat tanlash
- [ ] Qattiq katalog filtri — faqat tekshirilgan, ishlaydigan, geo-bloklanmagan kanallar
- [ ] Bandwidth monitoringi + IP bo'yicha parallel oqim limiti
- [ ] HLS segment keshlash (bir kanalni N kishi ko'rsa — bitta upstream)

**Tayyor mezoni:** TV kanallarining play success rate ≥ 85%, egress xarajati nazoratda.

### ⚠️ Ogohlantirish
TV bosqichi radiodan ~30 barobar qimmat va texnik jihatdan ancha nozik. Agar radio
tomoni real foydalanuvchi olmagan bo'lsa — TV'ga o'tish xato bo'ladi. Avval radio
tomonini o'stirish kerak.

---

## 🟪 4-bosqich — O'sish va qo'shimchalar

- [ ] Akkauntlar — qurilmalar orasida sevimlilarni sinxronlash
- [ ] "Hozir ijroda" (ICY metadata → SSE orqali real vaqtda)
- [ ] Fan-out optimizatsiyasi (bitta upstream → N tinglovchi)
- [ ] Tavsiyalar — "shunga o'xshash stansiyalar", janr bo'yicha
- [ ] PWA — offline qobiq, telefonga o'rnatish
- [ ] Ko'p tillilik (uz / ru / en)
- [ ] TV uchun EPG (XMLTV dastur jadvali)
- [ ] Globusda stansiya nuqtalari (`geo_lat`/`geo_lon` bo'yicha)
- [ ] Telegram bot — "shu stansiyani tingla" havolasi bilan

---

## 📊 Vaqt baholari

| Bosqich | Davomiyligi | Jamlangan |
| :--- | :--- | :--- |
| 0 — Poydevor | 1 hafta | 1 hafta |
| 1 — Radio MVP | 2 hafta | 3 hafta |
| 2 — Sifat va SEO | 1.5 hafta | 4.5 hafta |
| 3 — TV | 2–3 hafta | 7.5 hafta |
| 4 — O'sish | uzluksiz | — |

---

## 🎯 Asosiy printsip

> **Avval 42 ta ishlaydigan o'zbek radiosi, keyin 50 000 ta yarmi o'lik stansiya.**

Katalog hajmi emas, **ishonchliligi** muhim. Foydalanuvchi uch marta bosib ishlamasa
qaytmaydi — hech qanday dizayn yoki funksiya buni qoplamaydi.
