# 🌍 RadioGlobe — World Radio & TV Streaming

Interaktiv **3D globus** orqali dunyo radiostansiyalari va TV kanallarini kashf qilish
platformasi. Globusdan biror davlatni bossang — o'sha davlatning radio va TV kanallari
chiqadi, bosib darhol tinglash/tomosha qilish mumkin.

![Status](https://img.shields.io/badge/Status-Arxitektura_bosqichi-f59e0b)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-15-000000?logo=nextdotjs&logoColor=white)
![MapLibre](https://img.shields.io/badge/MapLibre_GL-v5_globe-396CB2?logo=maplibre&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?logo=redis&logoColor=white)

**Repozitoriya:** [shamsiyevshamsiddin19/radio-world-streaming](https://github.com/shamsiyevshamsiddin19/radio-world-streaming)

---

## 📌 Loyiha holati

> ⚠️ **Hozircha kod yozilmagan.** Bu bosqichda faqat tizim arxitekturasi, ma'lumotlar
> modeli, API shartnomasi va texnik tuzoqlar hujjatlashtirilgan. Kod yozishdan oldin
> `docs/` dagi barcha hujjatlarni o'qib chiqish shart.

| Bosqich | Holat |
| :--- | :--- |
| G'oya va qamrov | ✅ Tugallandi |
| Tizim arxitekturasi | ✅ Hujjatlashtirildi |
| Ma'lumotlar modeli | ✅ Hujjatlashtirildi |
| API shartnomasi | ✅ Hujjatlashtirildi |
| Backend kodi | ⬜ Boshlanmagan |
| Frontend kodi | ⬜ Boshlanmagan |

---

## 🎯 Qabul qilingan asosiy qarorlar

Arxitektura muhokamasida uchta tamal qaror qabul qilindi:

| Qaror | Tanlov | Sabab |
| :--- | :--- | :--- |
| **MVP qamrovi** | 🎙 **Faqat radio** | Bandwidth 20 barobar arzon, legal jihatdan toza, 2-3 haftada tirik mahsulot. TV — 3-bosqichda, bir xil arxitekturaga qo'shiladi. |
| **Frontend** | **Next.js 15** (App Router) | Har bir davlat/stansiya uchun SSR sahifa. Bu turdagi saytga organik qidiruv trafigi asosiy o'sish kanali. |
| **Xarita** | **MapLibre GL v5** globe projection | Haqiqiy 3D globus, zoomda tekis xaritaga silliq o'tish, basemap/API key kerak emas. |

---

## 🏗️ Arxitektura (qisqa)

```
Next.js 15 (MapLibre globus + doimiy pleyer + SSR davlat sahifalari)
      │
      ├── FastAPI ──── PostgreSQL 16    katalog, health, statistika
      │        └────── Redis            kesh, play counter, rate limit
      │
      ├── Audio Proxy (nginx / Go)      imzolangan token, stream_id bo'yicha
      │
      └── Worker (asyncio)
            ├── radio-browser sync      (kunlik)
            └── health checker          (exponential backoff bilan)
```

Batafsil: [`docs/01-arxitektura.md`](./docs/01-arxitektura.md)

---

## 📚 Hujjatlar

| Fayl | Mazmuni |
| :--- | :--- |
| [`docs/01-arxitektura.md`](./docs/01-arxitektura.md) | Tizim arxitekturasi, komponentlar, ularning mas'uliyati va aloqasi |
| [`docs/02-malumotlar-modeli.md`](./docs/02-malumotlar-modeli.md) | PostgreSQL sxemasi, jadvallar, indekslar, nozik nuqtalar |
| [`docs/03-api.md`](./docs/03-api.md) | REST endpointlar shartnomasi, javob formatlari, keshlash |
| [`docs/04-frontend.md`](./docs/04-frontend.md) | Next.js tuzilmasi, MapLibre globus, doimiy pleyer, SEO |
| [`docs/05-manbalar.md`](./docs/05-manbalar.md) | Kontent manbalari (radio-browser, iptv-org), ingest, huquqiy jihat |
| [`docs/06-tuzoqlar.md`](./docs/06-tuzoqlar.md) | ⚠️ **Eng muhim fayl** — CORS, mixed content, SSRF, SEO/WebGL ziddiyati |
| [`docs/07-reja.md`](./docs/07-reja.md) | Bosqichlar (roadmap), har bir bosqichning "tayyor" mezoni |

---

## 🧩 Texnologiyalar

**Backend:** Python 3.12 · FastAPI · PostgreSQL 16 · Redis 7 · asyncpg / SQLAlchemy 2 · Alembic · httpx
**Frontend:** Next.js 15 · TypeScript · Tailwind CSS · MapLibre GL JS v5 · Zustand · hls.js
**Infra:** Docker Compose · Caddy (TLS) · nginx yoki Go (audio proxy) · Oracle Cloud / AWS EC2

---

## 👨‍💻 Muallif

**Shamsiddin Shamsiyev** — Backend Developer (Python, FastAPI, PostgreSQL, Docker)

Litsenziya: [MIT](./LICENSE)

[![GitHub](https://img.shields.io/badge/GitHub-@shamsiyevshamsiddin19-181717?logo=github&logoColor=white)](https://github.com/shamsiyevshamsiddin19)
