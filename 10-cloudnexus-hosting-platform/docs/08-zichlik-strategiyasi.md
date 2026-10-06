# 08 — Zichlik strategiyasi: statik-first, lekin statik-only emas

> ⚠️ Narx va bepul tarif hajmlari taxminiy (2026) — raqiblar sahifasidan
> qayta tekshirilishi kerak.

## 8.1 Savol

"Faqat RAM yemaydigan texnologiyalarni render qilsak, Netlify'ga o'xshagan
bo'ladi" — bu to'g'ri instinkt. Lekin **ikkita** narsani ajratish kerak:

| | Qaror |
|---|---|
| Statik dvigatelni **birinchi** qurish | ✅ **Ha, shunday qilamiz** |
| Mahsulotni **faqat statik** deb belgilash | ❌ Yo'q — biznes qurilmaydi |

## 8.2 Nega statik-first to'g'ri

- Statik quvur konteyner quvuridan **mustaqil** (03-hujjat 3.2a) — uni
  birinchi yozish keyinchalik qayta ishlanmaydi, yo'qotish yo'q
- Xavfsizlikning **eng qo'rqinchli qismi yo'qoladi**: runtime'da begona
  kod ishlamaydi. Faqat build vaqtida, u ham bir martalik sandbox'da
  (04-hujjat). Mayning, spam, konteynerdan chiqish — bularning hammasi
  statik saytda **mumkin emas**
- Tannarx ~0 → bepul tarif haqiqatan bepul
- MVP 3–4 hafta, 6 hafta emas

## 8.3 Nega statik-**only** biznes emas

### Muammo 1: statik hostingning bozor narxi — nol

| Raqib | Bepul tarifi |
|---|---|
| Cloudflare Pages | Cheksiz trafik, cheksiz so'rov |
| GitHub Pages | Bepul, cheklovlar yumshoq |
| Netlify | ~100 GB trafik/oy |
| Vercel | Hobby bepul |

Statik sayt uchun o'zbek dasturchisi **nega 39 000 so'm to'laydi?**
Faqat statik qolsak, javob yo'q. Bizning ustunliklarimiz (o'zbek tili,
UZS to'lov, mahalliy ping) bepul raqibni yengishga **yetmaydi**.

### Muammo 2: AI ko'proq backend yozadi

Dastlabki g'oya: *"AI kod yozadi, deploy qiyin"*. Lekin deploy **qiyin
bo'lgan qismi aynan statik emas:**

| AI nima yozadi | Deploy qiyinligi | Statikmi |
|---|---|---|
| Telegram bot | **qiyin** (token, webhook, doimiy ishlash) | ❌ |
| FastAPI / Express API | **qiyin** (port, env, DB) | ❌ |
| Django panel | **juda qiyin** | ❌ |
| React landing | oson — Netlify'ga drag-and-drop | ✅ |

➡️ Statik deploy **allaqachon oson**. Biz qiyin bo'lgan joyni hal
qilmasak, mahsulotning asosiy hikoyasi yo'qoladi.

### Muammo 3: Netlify ham faqat statik emas
Netlify'da Functions, Vercel'da Serverless, Cloudflare Pages'da Workers
bor. "Netlify'ga o'xshash" degani ham aslida "statik + biror runtime".

## 8.4 O'rta yo'l: **scale-to-zero** — backend ham "deyarli RAM 0"

Bu bo'lim savolning asl javobi.

Konteyner **doimiy** ishlashi shart emas. So'rov kelganda uyg'otiladi,
jim bo'lsa uxlatiladi:

```
So'rov yo'q 15 daqiqa   →  konteyner to'xtatiladi  →  RAM 0
So'rov keldi            →  Traefik ushlab turadi
                        →  konteyner ko'tariladi (1–3 s)
                        →  so'rov uzatiladi
```

**Hobbi backend kuniga 10 ta so'rov oladi** — ya'ni vaqtning **99%+**
uxlaydi. Demak:

| Model | 8 GB node'ga sig'adi |
|---|---|
| Doimiy ishlaydigan backend | ~45 ta |
| **Scale-to-zero backend** (10% faol) | **300–450 ta** |
| Statik sayt | ~8 000 ta (disk chegarasi) |

Bu **statik emas**, lekin iqtisodiyoti statikka yaqin. Va asosiysi —
*qiyin* muammoni hal qiladi.

**Tannarxi:** sovuq start (cold start) 1–3 sekund. Hobbi loyiha uchun
muammo emas, pulli tarifda esa "doimiy yoniq" (always-on) qilib sotiladi
— bu **tabiiy upsell**.

### Texnik talablar
- Traefik oldida so'rovni **ushlab turish** (request buffering) — konteyner
  ko'tarilguncha 502 bermaslik. Buning uchun kichik proxy qatlami kerak
  (Go'da ~200 qator, yoki `knative`-ga o'xshash yondashuv)
- `docker start` (`run` emas) — image allaqachon node'da, 1–2 s
- Oxirgi so'rov vaqtini kuzatish → idle reaper (har daqiqa)
- Holat (state) konteynerda saqlanmasligi kerak → tashqi DB/volume

## 8.5 Alohida topilma: **webhook rejimidagi Telegram bot uxlashi mumkin**

O'zbekistonda eng ko'p yozilayotgan narsa — Telegram bot. Va bu yerda
muhim nuqta bor:

| Bot rejimi | Uxlashi mumkinmi | Nega |
|---|---|---|
| **Long polling** (`start_polling`) | ❌ | Doimiy ulanish kerak, RAM doimiy band |
| **Webhook** (`set_webhook`) | ✅ | Telegram HTTP POST yuboradi → konteyner uyg'onadi |

➡️ **Biz botlarni webhook rejimiga o'tkazamiz va ular uxlaydi.**
Natijada bot hosting tannarxi statikka yaqinlashadi.

Bu nafaqat arzon — **sotuv argumenti**: aiogram/telegraf'da webhook
sozlash (TLS, domen, `set_webhook`, port) yangi dasturchi uchun og'riq.
Biz buni **avtomatik** qilamiz:

```
Bot deploy qilindi
  → biz HTTPS endpoint beramiz:  https://bot-nomi.app.<brend>.uz/tg/<sir>
  → biz o'zimiz setWebhook chaqiramiz
  → foydalanuvchi faqat BOT_TOKEN ni kiritadi
```

⚠️ Tuzoq: long polling bilan yozilgan botni webhook'ga o'tkazish kod
o'zgarishini talab qiladi. Yechim — **shablon** (`templates/telegram-bot/`)
boshidan webhook'da bo'lsin, va AI uchun `AGENTS.md` da shu yozilsin
(03-hujjat 3.4). Long polling'ni ham qo'llab-quvvatlaymiz, lekin u
"doimiy yoniq" tarifga kiradi — bu **to'g'ri narxlash signali**.

## 8.6 Yakuniy qaror

> **Platforma uch xil ishni biladi, uchalasi ham zichlikka moslangan:**
>
> | Qatlam | RAM | Tarif | Bosqich |
> |---|---|---|---|
> | **1. Statik** (HTML/React/SSG/WASM) | 0 | Bepul | 1 |
> | **2. Uxlaydigan backend** (scale-to-zero) | ~0 idle | Arzon | 3 |
> | **3. Doimiy yoniq** (always-on, long polling, DB) | to'liq | Qimmat | 3 |
>
> Mahsulot hikoyasi: *"AI yozgan narsangni — sayt bo'ladimi, bot
> bo'ladimi, API bo'ladimi — bir buyruq bilan joylashtiramiz."*
> Statik bepul bo'lib foydalanuvchi oqimini beradi, backend pul keltiradi.

### Yo'l xaritasiga ta'sir
- **Bosqich 1** faqat statikka qisqaradi → MVP 4–6 haftadan **3–4 haftaga**
  tushadi. Konteyner, cgroup, izolyatsiya — hammasi keyinga suriladi
- **Bosqich 2** (AI qatlami) o'z joyida qoladi — statik ham MCP orqali
  deploy qilinadi
- **Bosqich 3** ga `scale-to-zero` va `webhook bot` qo'shiladi —
  monetizatsiya bilan birga, chunki pul aynan shu qatlamdan keladi

✅ Bu statik-first yondashuvning afzalligini (tezlik, xavfsizlik, arzonlik)
saqlaydi, lekin mahsulotni bepul raqiblar bilan taqqoslanadigan holatga
tushirmaydi.
