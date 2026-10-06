# 06 — Yo'l xaritasi (roadmap)

Vaqt baholari **yakka dasturchi, kuniga 3–4 soat** holatiga ko'ra.
AI yordamida kod yozish hisobga olingan.

---

## Bosqich 0 — Qo'lda PoC (1–2 hafta)

> **Maqsad:** bitta ilovani boshidan oxirigacha **qo'lda** deploy qilish va
> **har bir buyruqni yozib olish.** Shu yozuv keyin avtomatlashtirish
> spetsifikatsiyasiga aylanadi.

- [ ] Server olish (Oracle ARM yoki lokal Docker)
- [ ] Domen va Cloudflare DNS sozlash, wildcard TLS olish
- [ ] Traefik ko'tarish, `test.app.domen.uz` ishlashini ko'rish
- [ ] Nixpacks bilan qo'lda: Node ilova, FastAPI, aiogram bot, statik React
- [ ] Ichki registry ko'tarish
- [ ] Konteynerni barcha limitlar bilan ishga tushirish (04-hujjat ro'yxati)
- [ ] `docker stats` dan metrika o'qib ko'rish
- [ ] **Har qadamni `docs/runbook-manual.md` ga yozish**

**Parallel (texnik emas, lekin eng uzun yo'l):**
- [ ] Brend va domen nomi tanlash
- [ ] YaTT/MChJ ro'yxatdan o'tkazishni boshlash
- [ ] Hetzner akkaunt + xalqaro karta masalasini hal qilish
- [ ] Payme/Click bilan birinchi aloqa

---

## Bosqich 1 — MVP: **faqat statik** (3–4 hafta)

> **Qaror:** Bosqich 1 da konteyner **umuman yo'q** —
> [08-hujjat](08-zichlik-strategiyasi.md). Sabab: statik quvur konteyner
> quvuridan mustaqil, demak keyinchalik qayta ishlanmaydi; va runtime'da
> begona kod ishlamagani uchun xavfsizlikning eng og'ir qismi (cgroup,
> izolyatsiya, mayning, spam) **butunlay keyinga suriladi**.
>
> **Maqsad:** begona odam ro'yxatdan o'tib, `git push` qilib, HTTPS'li
> ishlaydigan sayt olishi.

### 1.1 Skelet (1 hafta)
- [ ] Django proyekt, Postgres, Redis, Docker Compose (dev)
- [ ] `django-allauth`: Google + GitHub kirish
- [ ] Modellar: `User`, `Project`, `Site`, `Deployment`, `SshKey`, `Domain`
- [ ] Panel skeleti (HTMX + Tailwind), Django admin

### 1.2 Statik quvur (1.5 hafta)
- [ ] SSH git receiver: kalit → foydalanuvchi, `git-receive-pack` ushlash
- [ ] **Ilova turini aniqlash** — Nixpacks'dan oldin ishlaydigan o'z
      aniqlovchimiz ([07-hujjat](07-qaysi-texnologiya-qancha-ram.md#74-tuzoqlar--statik-korinadi-lekin-emas))
- [ ] `build` navbati: klon → `npm run build` (yoki build yo'q) → `dist/`
- [ ] Build **bir martalik sandbox**da, tarmoq cheklangan, 10 daq / 2 GB
- [ ] Natija → `/srv/sites/<id>/releases/<sha>/` + atomik symlink
- [ ] Bitta umumiy nginx, `server_name` regexp bilan — har saytga
      konfiguratsiya yozilmaydi ([03-hujjat 3.2a](03-arxitektura.md#zichlik-qanday-texnologiya-bilan-olinadi))
- [ ] **Wildcard TLS** `*.app.<brend>.uz` (Cloudflare DNS-01)
- [ ] **SPA fallback** — bo'lmasa AI yozgan har ikkinchi React sayt 404 beradi
- [ ] Deploy holati panelda real vaqtda (SSE)

### 1.3 Ekspluatatsiya (1 hafta)
- [ ] Build log oqimi (panelda `follow`)
- [ ] Rollback — symlink'ni burish (bir sekund)
- [ ] Sayt o'chirish, qayta deploy, release tozalash (oxirgi 3 ta)
- [ ] Build vaqtidagi env (`VITE_*` kabi) — shifrlangan
- [ ] SSR aniqlangan loyihada **tushunarli xabar** + chiqish yo'li
      maslahati ([07-hujjat 7.5](07-qaysi-texnologiya-qancha-ram.md#75-panelda-qanday-korsatiladi))

### 1.4 Xavfsizlik bazasi (0.5 hafta) — statikda ancha yengil
- [ ] Build sandbox izolyatsiyasi + vaqt/RAM chegarasi
- [ ] `server_name` regexp qat'iy `[a-z0-9-]` — path traversal yo'q
- [ ] Subdomen nomlari qora ro'yxati (`www`, `api`, `admin`, `mail`...)
- [ ] Deploy hajmi chegarasi, disk kvotasi (XFS prjquota)
- [ ] `gitleaks` pre-commit (o'z repomiz uchun)

### 1.5 Node o'rnatish — keyin tuzatilmaydigan qarorlar
- [ ] Fayl tizimi **XFS**, `prjquota` yoqilgan (`mkfs` paytida!)
- [ ] Ilova domeni Cloudflare'da
- [ ] Control va build alohida (bir xil node bo'lsa ham alohida cgroup)

**Chiqish mezoni:** 5 ta tanish dasturchi o'z statik loyihasini
(kamida bittasi React) o'zi deploy qildi, siz hech narsa qilmadingiz.

---

## Bosqich 2 — AI qatlami (2–3 hafta) — **farqlantiruvchi xususiyat**

> Bu bosqich **monetizatsiyadan oldin** turadi: mahsulotning sotuv
> hikoyasi shu, va aynan shuni sinab ko'rish kerak.

- [ ] Public API `/api/v1` + token
- [ ] CLI: `login` (device code), `deploy`, `logs`, `env`, `status`
- [ ] **MCP server**: `create_app`, `deploy`, `get_logs`, `set_env`,
      `get_status`, `rollback`
- [ ] `llms.txt`, `AGENTS.md` shabloni, Claude Code skill
- [ ] Shablonlar: Telegram bot, FastAPI, Next.js, statik
- [ ] GitHub App: repo ulash + `push` webhook → avtomatik deploy
- [ ] **Namoyish videosi:** "Claude'ga aytdim — o'zi deploy qildi, xatoni
      o'zi topdi, o'zi tuzatdi". Bu marketingning asosi

**Chiqish mezoni:** AI agent bitta buyruqdan keyin, odam aralashmasdan,
deploy → xato → log → tuzatish → qayta deploy aylanasini bajara oldi.

---

## Bosqich 3 — Backend qatlami + monetizatsiya (5–6 hafta)

> Bu bosqichda konteyner **birinchi marta** paydo bo'ladi. Pul aynan shu
> yerdan keladi, shu sababli billing bilan **birga** qilinadi
> ([08-hujjat](08-zichlik-strategiyasi.md)).

### 3.1 Konteyner dvigateli
- [ ] Nixpacks bilan build → ichki registry
- [ ] node-agent, Docker API, Traefik yorliqlari
- [ ] **04-hujjatning Bosqich 1 xavfsizlik ro'yxati to'liq** — endi
      runtime'da begona kod ishlaydi, hammasi kerak bo'ladi
- [ ] Chiquvchi SMTP va private/metadata diapazonlar bloki
- [ ] Har ilovaga alohida tarmoq
- [ ] Env sirlari (shifrlangan, logga tushmaydi)
- [ ] Runtime log oqimi, restart, rollback

### 3.2 Scale-to-zero (zichlikning kaliti)
- [ ] Traefik oldida so'rovni **ushlab turuvchi** proxy (502 bermaslik)
- [ ] Idle reaper: 15 daqiqa so'rov yo'q → `docker stop`
- [ ] So'rov keldi → `docker start` (1–3 s) → uzatish
- [ ] Panelda "uxlayapti / yoniq" holati, "doimiy yoniq" upsell tugmasi

### 3.3 Telegram bot — webhook avtomatik
- [ ] HTTPS endpoint: `/tg/<sir>` + `setWebhook` ni **biz chaqiramiz**
- [ ] Foydalanuvchi faqat `BOT_TOKEN` kiritadi
- [ ] Webhook bot → uxlaydi (arzon tarif)
- [ ] Long polling bot → doimiy yoniq (qimmat tarif)
- [ ] `templates/telegram-bot/` shabloni **webhook rejimida** bo'lsin

### 3.4 Monetizatsiya

- [ ] Metering: `app_usage_hourly`, agent metrikalari, soatlik rollup
- [ ] Tarif modellari, kvota tekshiruvi, majburlash (05-hujjat 5.4)
- [ ] Balans, kunlik yechish, ogohlantirish, grace → to'xtatish → o'chirish
- [ ] Payme / Click integratsiyasi (shartnoma Bosqich 0 da boshlangan)
- [ ] Panelda "foydalanish" sahifasi — real vaqtda
- [ ] Idle → uxlatish (scale-to-zero) — bepul tarif uchun **shart**
- [ ] Ommaviy oferta, maxfiylik siyosati, ToS saytga qo'yilishi

---

## Bosqich 4 — To'laqonli platforma (4–6 hafta)

- [ ] **PostgreSQL xizmat sifatida** (per-app DB + `DATABASE_URL` + backup)
- [ ] Redis xizmat sifatida
- [ ] **Mijozning o'z domeni** + TLS (on-demand)
- [ ] Jamoalar / tashkilotlar, rollar
- [ ] Preview deploy (PR uchun)
- [ ] Cron / scheduled job
- [ ] Doimiy disk (volume)
- [ ] Telegram Login (O'zbek bozori uchun)

---

## Bosqich 5 — Miqyos va barqarorlik (doimiy)

- [ ] Ko'p node: agent orqali joylashtirish (scheduling), node drain
- [ ] Loki + Grafana, Sentry, Uptime Kuma, Telegram ogohlantirishlari
- [ ] Backup tiklashni **oyda bir marta sinash**
- [ ] Status sahifasi (`status.<brend>.uz`)
- [ ] O'zbekistonda region (qonuniy talab chiqsa — 04-hujjat 4.3)
- [ ] Rootless Podman / gVisor ga o'tish
- [ ] Zero-downtime deploy (blue-green)

---

## Eng katta xatarlar (risk registri)

| # | Xatar | Ta'sir | Chora |
|---|---|---|---|
| 1 | **Suiiste'mol → IP qora ro'yxatda / provayder bloki** | Platforma o'ladi | 04-hujjat 4.2: bepul tarifda telefon tasdiqlash, SMTP bloki |
| 2 | **Oracle free tier shartlari buzilishi** | Barcha mijoz bir kunda yo'qoladi | Pulli mijoz ARM free'da turmaydi. Bosqich 1 da Hetzner |
| 3 | **Hetzner to'lovi UZ kartadan o'tmaydi** | Bosqich 1 bloklanadi | Bosqich 0 da hal qilinadi. Zaxira: Vultr/DO |
| 4 | **Payme shartnomasi kechikadi** | Daromad kechikadi | Bosqich 0 da parallel boshlanadi |
| 5 | **eskiz.uz da ACME API yo'q** | Wildcard TLS ishlamaydi | Ilova domeni Cloudflare'ga (01-hujjat 1.5) |
| 6 | **ARM mosligi — AI kodi ishlamaydi** | Foydalanuvchi ketadi | Worker node **x86** bo'lsin |
| 7 | **Bitta mijoz node'ni o'ldiradi** | Hamma saytlar yotadi | `--memory-swap`, pids, CPU cap, disk quota — Bosqich 1.4 |
| 8 | **Yakka dasturchi + 24/7 uptime** | Charchash, ishonch yo'qolishi | SLA bermaslik, "best effort". Avtomatik restart, watchdog |
| 9 | **Backup ishlamaydi** | Mijoz ma'lumoti yo'qoladi | Oyda bir marta tiklab sinash |
| 10 | **Qonuniy: shaxsiy ma'lumot chet elda** | Jarima / to'xtatish | Yurist bilan tekshirish (4.3) |

---

## Birinchi hafta — aniq qadamlar

1. **Brend/domen nomi** tanlash va olish
2. Oracle ARM A1.Flex so'rash (capacity bo'lmasa — lokal Docker)
3. Cloudflare'ga ilova domenini ulash, wildcard TLS sinash
4. Nixpacks'ni lokalda sinash: 4 xil loyihani qo'lda build qilish
5. YaTT ro'yxati va Hetzner karta masalasini boshlash
6. `docs/runbook-manual.md` — har buyruqni yozib borish
