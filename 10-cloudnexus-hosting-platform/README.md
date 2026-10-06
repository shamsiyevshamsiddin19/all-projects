# AI-native hosting platforma — arxitektura va reja

**Holat:** Bosqich 1 — arxitektura va rejalashtirish. Kod yozilmagan.

> 🚀 **Kodlashni boshlaysizmi?** Boshqa AI agentga (Claude Code, Cursor...)
> to'g'ridan-to'g'ri bering: [**IMPLEMENTATION_BRIEF.md**](IMPLEMENTATION_BRIEF.md)
> — o'z-o'zidan yetarli, Bosqich 1 (statik hosting MVP) uchun to'liq
> texnik topshiriq: stack, repo tuzilmasi, data model, aniqlash algoritmi,
> nginx config, deploy quvuri, qabul qilish mezonlari.
**Sana:** 2026-10-06

---

## Mahsulot g'oyasi

> AI endi kod yozishni hal qildi. Deployni hal qilmadi.

Bugun odam AI bilan 2 soatda ishlaydigan ilova yozadi, keyin uni serverga
qo'yishga 2 kun ketadi: VPS, SSH, nginx, systemd, TLS, domen, env, log.
Ko'pchilik shu yerda to'xtaydi va loyiha lokalda qolib ketadi.

**Bizning yechim:** Google yoki GitHub bilan ro'yxatdan o'tadi — tamom.
Qolganini **AI o'zi** qiladi: biz AI tushunadigan interfeys beramiz
(SSH/git + CLI + MCP), AI deploy qiladi, xatoni log'dan **o'zi o'qiydi**,
o'zi tuzatadi, qayta deploy qiladi.

### Nega bu raqiblardan farq qiladi

| | Vercel / Railway / Render | Mahalliy hosting (cPanel) | **Biz** |
|---|---|---|---|
| AI deploy qila oladi | qisman (CLI bor) | ❌ | ✅ birinchi darajali |
| AI xatoni **o'zi ko'ra oladi** | ❌ | ❌ | ✅ `get_logs` MCP |
| O'zbek tili, UZS to'lov | ❌ | ✅ | ✅ |
| Dockerfile yozmasdan | ✅ | ❌ | ✅ Nixpacks |
| Telegram bot hosting | noqulay | ❌ | ✅ alohida shablon |
| Narx (UZ daromadiga nisbatan) | qimmat | o'rtacha | arzon |

Asosiy farqlantiruvchi: **yopiq tuzatish aylanasi** —
`deploy → xato → log → AI tuzatadi → deploy`, odam aralashmasdan.

---

## Qabul qilingan qarorlar

| Mavzu | Qaror | Hujjat |
|---|---|---|
| **Server** | Bosqich 0: Oracle ARM free (bepul, dev). Bosqich 1+: **Hetzner x86**. Control / builder / worker **alohida node** | [01](docs/01-server-tanlovi.md) |
| **Deploy o'zagi** | **O'z control plane** + Nixpacks (build) + Docker API (run) + Traefik (route). Dokku/Coolify ustiga o'ralmaydi | [02](docs/02-ozak-tanlovi.md) |
| **Backend** | Django + DRF + HTMX + Tailwind (allauth Google/GitHub tayyor beradi) | [03](docs/03-arxitektura.md) |
| **Navbat** | Redis + RQ | [03](docs/03-arxitektura.md) |
| **MVP qamrovi** | **Bosqich 1 faqat statik** (konteyner yo'q). Backend — Bosqich 3, scale-to-zero bilan. PostgreSQL — Bosqich 4 | [08](docs/08-zichlik-strategiyasi.md) |
| **Statik ta'rifi** | Mezon: *so'rov kelganda server kodi ishlashi kerakmi?* Yo'q bo'lsa RAM=0 → bepul. Toza HTML/CSS/JS, React/Vue/Vite, SSG, WASM — hammasi bepul. Next.js SSR — emas | [07](docs/07-qaysi-texnologiya-qancha-ram.md) |
| **DNS/TLS** | Ilova domeni **Cloudflare**'ga (eskiz.uz da ACME API yo'q) | [01](docs/01-server-tanlovi.md#15-qoshimcha-domen-va-dns) |
| **To'lov modeli** | Obuna emas — **balans + kunlik yechish** (UZ bozorida ishonchliroq) | [05](docs/05-tariflar-va-billing.md) |
| **Uch qatlam** | 1) Statik = RAM 0 = bepul. 2) Uxlaydigan backend (scale-to-zero) = arzon. 3) Doimiy yoniq = qimmat | [08](docs/08-zichlik-strategiyasi.md) |
| **Bepul tarif** | Statik cheksizga yaqin, backend faqat **telefon tasdiqlangandan** keyin + idle'da uxlaydi | [04](docs/04-xavfsizlik.md#42-suiistemolni-oldini-olish-siyosati-mahsulot-qarori) |

---

## Hujjatlar

| # | Hujjat | Nima haqida |
|---|---|---|
| 01 | [Server tanlovi](docs/01-server-tanlovi.md) | Qanday server kerak, Oracle/Hetzner/UZ taqqoslash, nechta ilova sig'adi, 3 bosqichli plan, DNS |
| 02 | [Deploy o'zagi](docs/02-ozak-tanlovi.md) | Noldan vs Dokku vs Coolify vs k3s — ochiq tahlil va qaror |
| 03 | [Texnik arxitektura](docs/03-arxitektura.md) | Komponentlar, diagramma, AI deploy oqimlari (git / GitHub / CLI+MCP), repo tuzilmasi |
| 04 | [Xavfsizlik](docs/04-xavfsizlik.md) | Konteyner izolyatsiyasi, suiiste'mol, mayning, spam, huquqiy tomon. **Eng muhim hujjat** |
| 05 | [Tariflar va billing](docs/05-tariflar-va-billing.md) | Tannarx hisobi, 4 ta tarif, metering sxemasi, Payme/Click |
| 06 | [Yo'l xaritasi](docs/06-yolmap.md) | 6 bosqich, vaqt baholari, risk registri, birinchi hafta |
| 07 | [Qaysi texnologiya qancha RAM](docs/07-qaysi-texnologiya-qancha-ram.md) | RAM=0 ro'yxati (SPA, SSG, WASM), RAM yeydiganlar, "statik ko'rinadi lekin emas" tuzoqlari |
| 08 | [Zichlik strategiyasi](docs/08-zichlik-strategiyasi.md) | Statik-first vs statik-only, scale-to-zero, webhook botlar — **mahsulot qamrovi qarori** |

---

## Ochiq savollar (javob kerak)

1. **Brend va domen nomi?** — hujjatlarda `<brend>` deb qoldirildi
2. **Repo ochiq bo'lsinmi?** `vibe-coding` ochiq repo, bu loyihada
   OAuth secret, SSH host kaliti, to'lov kalitlari bo'ladi.
   Tavsiya: **alohida private repo**
3. **Boshlang'ich byudjet?** Bosqich 1 ≈ 15 €/oy, Bosqich 2 ≈ 85 €/oy
4. **Mijoz kim?** O'zbek AI-dasturchilari / talabalar / bot yozuvchilar —
   bu tarif narxini va tilni belgilaydi
5. **Yolg'izmisiz yoki hamkor bo'ladimi?** 04-hujjatdagi 24/7
   ekspluatatsiya yuki yakka odamga og'ir
