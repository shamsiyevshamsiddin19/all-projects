# 07 — Qaysi texnologiya RAM yemaydi (ma'lumotnoma)

Bu hujjat ikki joyda ishlatiladi:
1. **Aniqlash mantiqi** ([03-hujjat 3.2a](03-arxitektura.md)) uchun ro'yxat
2. **Narx sahifasi** uchun — foydalanuvchiga "sizning loyihangiz bepulmi"
   deb aytadigan jadval

---

## 7.1 Yagona mezon

Texnologiya nomi ahamiyatsiz. Faqat bitta savol:

> **So'rov kelganda server tomonida kod ishlashi kerakmi?**
>
> - ❌ Yo'q — tayyor fayllarni o'zgartirmasdan berish yetarli → **RAM = 0**
> - ✅ Ha — DB, sessiya, SSR, API, hisob-kitob → **doimiy protsess kerak**

Ikkinchi savol (tez tekshirish uchun):

> **Build natijasida faqat `.html`, `.css`, `.js`, rasm, font qoladimi?**
> Ha bo'lsa — RAM 0.

Build vaqtida nima ishlatilgani — **farqi yo'q**. Hugo Go'da yozilgan,
Jekyll Ruby'da, Sphinx Python'da — lekin ularning natijasi HTML.
Build tugadi, protsess o'ldi, RAM bo'shadi.

---

## 7.2 RAM = 0 — faqat fayl (bepul tarifga kiradi)

### Toza frontend
| Texnologiya | Izoh |
|---|---|
| HTML + CSS + JS (vanilla) | Build ham kerak emas |
| Tailwind CSS, Bootstrap, Bulma | Natija — oddiy CSS fayl |
| jQuery, Alpine.js, htmx | Brauzerda ishlaydi |
| GSAP, Three.js, Chart.js, D3 | Brauzerda ishlaydi |

### SPA — build qilinadi, natija fayl
| Texnologiya | Shart |
|---|---|
| **React** (Vite, CRA) | SSR ishlatilmasa |
| **Vue** (Vite) | |
| **Svelte** | SvelteKit emas, toza Svelte |
| **Angular** | `ng build` (SSR/Universal emas) |
| Preact, Solid, Lit, Ember | |
| Qwik | statik rejimda |

### Statik sayt generatorlari (SSG)
| Texnologiya | Til | Shart |
|---|---|---|
| **Astro** | JS | `output: 'static'` (standart) |
| **Next.js** | JS | ⚠️ `output: 'export'` bo'lsa — quyida 7.4 ga qarang |
| **Nuxt** | JS | `nuxi generate` (`build` emas) |
| **SvelteKit** | JS | `adapter-static` |
| **Gatsby** | JS | Gatsby Functions ishlatilmasa |
| **Docusaurus, VitePress, Nextra** | JS | Hujjat saytlari |
| **Hugo** | Go | Natija — HTML |
| **Jekyll** | Ruby | |
| **Eleventy (11ty)** | JS | |
| **MkDocs, Sphinx, Pelican** | Python | |
| **Zola** | Rust | |

### WASM — "og'ir" ilova ham RAM 0 bo'lishi mumkin
Kod **brauzerda** ishlaydi, serverda emas:

| Texnologiya | Izoh |
|---|---|
| Rust / Go / C++ → WebAssembly | Serverda faqat `.wasm` fayl turadi |
| **Blazor WebAssembly** | ⚠️ Blazor **Server** emas — u RAM yeydi |
| **Flutter Web** | `flutter build web` |
| **Unity WebGL**, **Godot HTML5** | O'yinlar — serverda RAM 0 |
| Pyodide (brauzerda Python) | |
| SQLite WASM / absurd-sql | Brauzerda DB (!) |

### Statik + tashqi xizmat — muhim holat
| Qurilma | Serverda RAM |
|---|---|
| React + **Supabase** | 0 |
| Vue + **Firebase** | 0 |
| Astro + **Airtable / Google Sheets** API | 0 |
| Statik sayt + **Formspree / Resend** (forma) | 0 |

➡️ **To'laqonli CRUD ilova ham bepul tarifda yashashi mumkin**, agar DB
tashqarida bo'lsa. Bu bizga qarshi emas, **foyda**: foydalanuvchi keladi,
o'sadi, keyin bizning Postgres'imizga ko'chadi (05-hujjat, upsell).

---

## 7.3 RAM kerak — doimiy protsess (pulli tarif)

| Texnologiya | Taxminiy RAM |
|---|---|
| Express / Fastify / NestJS | 60–150 MB |
| **Next.js** (SSR / API routes / ISR / middleware) | 120–250 MB |
| Nuxt (SSR), Remix, SvelteKit (`adapter-node`) | 100–200 MB |
| FastAPI / Flask (uvicorn, gunicorn) | 80–150 MB |
| **Django** + gunicorn (2 worker) | 200–350 MB |
| Laravel / WordPress / har qanday PHP (php-fpm) | 150–400 MB |
| Spring Boot (JVM) | 300–600 MB |
| ASP.NET Core, Blazor **Server** | 150–300 MB |
| Go / Rust backend | 15–60 MB (eng arzon!) |
| **aiogram / telegraf bot** | 60–100 MB |
| Socket.io / WebSocket server | 80–200 MB |
| Strapi, Directus, Payload (headless CMS) | 250–500 MB |
| PostgreSQL / MySQL / MongoDB / Redis | alohida xizmat |

⚠️ **Go va Rust 15–60 MB** — bu juda muhim: bitta 8 GB node'ga
Go backend'lar **200+ ta** sig'adi. Bu kelajakda alohida arzon tarif
("mikro-backend") qilish imkonini beradi.

---

## 7.4 Tuzoqlar — "statik ko'rinadi, lekin emas"

Bu ro'yxat **qo'llab-quvvatlash murojaatlarining yarmi** bo'ladi:

| Holat | Nega chalg'itadi | Haqiqat |
|---|---|---|
| **Next.js** | "React'ku, statik" | Standart holatda **SSR** — RAM kerak. `output: 'export'` yozilgan bo'lsa statik, lekin unda API routes, ISR, middleware, `next/image` optimizatsiyasi **ishlamaydi** |
| **WordPress** | "shunchaki sayt" | PHP + MySQL — **hech qachon statik emas** |
| **Nuxt** | `build` va `generate` farqi yashirin | `nuxi build` → SSR, `nuxi generate` → statik |
| **SvelteKit** | adapter nomiga bog'liq | `adapter-static` → statik, `adapter-node` → RAM |
| **Astro** | standart statik, lekin... | `output: 'server'` yoki SSR integratsiyasi qo'shilsa → RAM |
| **Blazor** | ikki xil rejim bir nom ostida | WebAssembly → 0, Server → RAM |
| **Gatsby** | statik, lekin | Gatsby Functions ishlatilsa → RAM |
| **React + forma** | "faqat frontend" | Email yuborish uchun **backend yoki tashqi xizmat** kerak |
| **`.php` fayl bor** | "oddiy sayt" | Bitta `.php` fayl ham php-fpm talab qiladi |
| **Rasm optimizatsiyasi** | build vaqtida bo'lsa 0 | So'rov vaqtida bo'lsa → RAM |
| **Sessiya bilan auth** | | Server sessiyasi → RAM. Brauzerdagi JWT → 0 |

### Aniqlash uchun amaliy qoidalar

```
next.config.* ichida output: 'export'        → statik
next.config.* ichida boshqa narsa / yo'q     → SSR (RAM)
nuxt: package.json scripts da "generate"     → statik
svelte.config.* ichida adapter-static        → statik
astro.config.* ichida output: 'server'       → SSR (RAM)
*.php fayl topilsa                           → PHP runtime
wp-config.php / wp-content/                  → WordPress, qo'llab-quvvatlanmaydi (MVP)
```

⚠️ Shubha bo'lganda **SSR deb hisoblang** (RAM ajratilsin). Noto'g'ri
"statik" deb aniqlangan sayt **ishlamaydi** va foydalanuvchi ketadi;
noto'g'ri "SSR" deb aniqlangani esa shunchaki ozgina ko'proq resurs
yeydi — xato narxi teng emas.

---

## 7.5 Panelda qanday ko'rsatiladi

Deploydan **oldin** aniq xabar:

> ✅ **Statik sayt aniqlandi** (Vite + React)
> RAM talab qilmaydi — **bepul tarifda ishlaydi**.

> ⚠️ **Doimiy ishlaydigan ilova aniqlandi** (Next.js, SSR rejimi)
> ~150 MB RAM kerak — **Start tarif** (39 000 so'm/oy).
> Statik qilmoqchi bo'lsangiz: `next.config.js` ga `output: 'export'`
> qo'shing — lekin API routes ishlamaydi.

Ikkinchi xabardagi **maslahat** muhim: foydalanuvchiga chiqish yo'li
ko'rsatiladi, "pul to'la" deb yopilmaydi. Bu ishonch quradi.
