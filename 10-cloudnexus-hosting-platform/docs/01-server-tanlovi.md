# 01 — Server tanlovi: nima kerak va qancha turadi

> ⚠️ Barcha narxlar taxminiy va 2026 yil holatiga ko'ra. Buyurtma qilishdan
> oldin provayder saytidan **albatta qayta tekshiring**.

## 1.1 Hosting platformada nima resurs yeydi

Oddiy saytdan farqli, bizda **uch xil yuklama** bir-biriga xalaqit beradi:

| Yuklama | Nimani yeydi | Xarakteri |
|---|---|---|
| **Build** (npm install, pip install, docker build) | RAM + CPU + disk IO | Qisqa, lekin juda og'ir. Bitta `npm install` 1–2 GB RAM yeyishi mumkin |
| **Runtime** (ishlab turgan konteynerlar) | RAM (asosan) | Doimiy, barqaror |
| **Control plane** (panel, API, DB) | Kam, lekin **o'lmasligi kerak** | Doimiy |

Shundan kelib chiqib **birinchi arxitektura qoidasi**:

> Control plane, build va foydalanuvchi konteynerlari — **hech qachon bitta
> serverda bo'lmaydi**. Aks holda bitta foydalanuvchining `npm install`i
> butun platformani (shu bilan boshqa 50 mijozning saytini ham) o'ldiradi.

Bu qoida buzilsa, keyinchalik tuzatish deyarli imkonsiz — shu sababli
boshidan **node tipi** tushunchasi kiritiladi: `control`, `builder`, `worker`.

## 1.2 Bitta serverga qancha ilova sig'adi

Real o'lchovlar (taxminiy, RSS):

| Ilova turi | Xotira | Izoh |
|---|---|---|
| Statik sayt | ~0 MB | Konteyner kerak emas — fayl, nginx/Caddy o'qiydi. Minglab sayt bitta nodega sig'adi |
| Node.js (Express) | 60–120 MB | |
| Python FastAPI | 80–150 MB | |
| Django + gunicorn (2 worker) | 200–350 MB | |
| Telegram bot (aiogram) | 60–100 MB | Eng arzon mijoz |
| PostgreSQL (umumiy klaster) | 300 MB + har DB uchun ozgina | Alohida nodega chiqariladi |

**8 GB worker node** hisobi:
- 1 GB — OS + Docker + agent + Traefik
- 7 GB — foydalanuvchilar
- O'rtacha 150 MB/ilova → **~45 ta doimiy ishlaydigan ilova**
- Bepul tarifda "idle bo'lsa uxlatish" (sleep) bo'lsa → **100–150 ta ilova**

Bu raqam **butun tarif narxining asosi** (05-tariflar hujjatiga qarang).

## 1.3 Variantlar — ochiq taqqoslash

### A. Oracle Cloud Always Free (ARM A1.Flex)

- **Nima beradi:** 4 OCPU + 24 GB RAM + 200 GB disk — **bepul, doimiy**
- **Plus:** Bu bozordagi eng kuchli bepul taklif. 24 GB RAM = ~150 ta kichik ilova
- **Minus va xatarlar:**
  - `Out of host capacity` — Osaka/Stockholm regionlarida A1 ko'pincha bo'sh joy bermaydi. Oylab kutish mumkin
  - **ARM (aarch64)** — ba'zi Docker image va npm paketlari (`sharp`, `canvas`, eski binary'lar) ARM uchun yo'q. Foydalanuvchining AI yozgan kodi ishlamay qolishi ehtimoli bor
  - **Shartlar xatari:** Always Free resurslarini tijorat SaaS sifatida qayta sotish Oracle AUP'iga ziddiyat berishi mumkin. Pulli mijoz ARM free'da turganida akkaunt bloklansa — barcha mijozlar bir kunda yo'qoladi
  - Idle instansiyalar qayta olinishi mumkin
  - Sizdagi mavjud 945 MB micro'lar bunga **umuman yaramaydi** (01.2 hisobga ko'ra 5–6 ilova)
- **Hukm:** ✅ dev/staging va o'z testlaringiz uchun. ❌ pul to'lagan mijoz uchun.

### B. Hetzner Cloud (x86) — **tavsiya**

| Shape | vCPU | RAM | Disk | Narx (taxminan) |
|---|---|---|---|---|
| CX22 | 2 | 4 GB | 40 GB | ~4 €/oy |
| CX32 | 4 | 8 GB | 80 GB | ~7 €/oy |
| CPX41 | 8 (AMD ded.) | 16 GB | 240 GB | ~28 €/oy |
| **AX41/AX52 (dedicated)** | 6–8 yadro Ryzen | 64 GB | 2×512 GB NVMe | ~39–55 €/oy + o'rnatish |

- **Plus:** Narx/sifat bozorda eng yaxshisi. 20 TB trafik kiradi. Snapshot, private network, floating IP, firewall — hammasi bor. Dedicated serverda 64 GB RAM ≈ 400 ta kichik ilova
- **Minus:**
  - ⚠️ **To'lov:** O'zbekiston kartalaridan (Uzcard/Humo) to'lov o'tmaydi. Visa/Mastercard (xalqaro) yoki PayPal kerak. Akkaunt ochganda shaxsni tasdiqlash (ID) so'raladi — **buni birinchi kundan hal qilib qo'ying**, keyin shoshilib qolmaslik uchun
  - Toshkentga ping ~80–110 ms (Germaniya/Finlandiya)
  - Abuse xatosi (mijoz spam yuborsa) → akkaunt ogohlantirishi
- **Hukm:** ✅ Haqiqiy mahsulot uchun to'g'ri yo'l.

### C. O'zbekiston provayderlari (Ahost, UZINFOCOM, Billur, Tashhost)

- **Plus:** Toshkentga ping 3–10 ms. To'lov UZS da, Payme/Click orqali. Shartnoma O'zbek qonuniga mos — `.uz` domen va rezident mijozlar uchun muhim. Ma'lumotni mamlakat ichida saqlash talabiga javob beradi
- **Minus:** 1 GB RAM narxi Hetzner'dan 3–6 barobar qimmat. KVM/snapshot/API ko'pincha yo'q yoki chala. Tarmoq xalqaro yo'nalishda sekin
- **Hukm:** 🟡 Mijoz bazasi faqat O'zbekistonda bo'lsa va qonuniy talab chiqsa — kerak. Boshidan emas, 2-yoki 3-bosqichda **qo'shimcha region** sifatida.

### D. Contabo / arzon VPS'lar
- Juda arzon RAM, lekin **disk IO va CPU steal juda yomon**. Build yuklamasi uchun o'ldiruvchi. ❌ Tavsiya etilmaydi.

### E. DigitalOcean / Vultr / Linode
- 8 GB ≈ 48 $/oy — Hetzner'dan 5–6 barobar qimmat. Faqat kerakli afzalligi: ba'zan to'lov osonroq o'tadi.
- 🟡 Hetzner to'lovi hal bo'lmasa — zaxira variant.

## 1.4 Tavsiya etilgan yo'l (3 bosqich)

### Bosqich 0 — PoC va MVP ishlab chiqish (0 so'm)
```
Oracle ARM A1.Flex (4 OCPU / 24 GB)  ← hammasi shu yerda
  ├── control plane (panel, API, Postgres)
  ├── builder (konteyner ichida)
  └── worker (test ilovalari — faqat o'zingiznikiler)
```
Maqsad: kodni yozish, oqimni ishlatish. Tashqi mijoz yo'q.
Agar A1 capacity bermasa — lokal kompyuterda Docker Compose bilan ishlang.

### Bosqich 1 — Birinchi mijozlar (~11–15 €/oy)
```
Hetzner CX22 (2/4 GB)   → control plane + Postgres + Traefik + registry
Hetzner CX32 (4/8 GB)   → worker #1 (foydalanuvchi konteynerlari)
         ↑ build ham shu yerda, lekin alohida cgroup + qat'iy limit bilan
Hetzner Storage Box (1 TB, ~4 €/oy) → backup va build kesh
```
Bu ~40 ta pulli ilovani ko'taradi. Birinchi 100 ta foydalanuvchi uchun yetarli.

### Bosqich 2 — O'sish (~45–70 €/oy)
```
Control plane: CX32 (alohida, hech qachon foydalanuvchi kodi tegmaydi)
Builder:       CPX31 (ephemeral, tarmoqdan izolyatsiya)
Worker:        AX41 dedicated 64 GB  → 300–400 ilova
DB node:       CX32  → PostgreSQL klaster + Redis
Backup:        Storage Box / Backblaze B2
```
Bu yerda birinchi marta **multi-node** kerak bo'ladi — shu sababli
arxitektura boshidan "node agent" modelida yozilishi kerak (03-hujjat).

## 1.5 Qo'shimcha: domen va DNS

⚠️ **Muhim topilma:** DNS'laringiz **eskiz.uz** panelida. Bizga
`*.ilova.domen.uz` uchun **wildcard TLS** kerak, u esa **DNS-01 ACME
challenge** talab qiladi — ya'ni DNS provayderda **API** bo'lishi shart.
Eskiz.uz da bunday API yo'q (yoki hujjatlashtirilmagan).

**Yechim:** faqat platformaning ilova domenini (masalan `*.app.<brend>.uz`)
**Cloudflare** ga ko'chirish. Cloudflare bepul, ACME DNS-01 API bor,
DDoS himoyasi va proxy ham qo'shimcha bonus. Qolgan domenlar eskiz.uz da
qolishi mumkin.

**Kerakli domenlar:**
| Domen | Nima uchun |
|---|---|
| `<brend>.uz` | Asosiy sayt, panel |
| `*.app.<brend>.uz` | Foydalanuvchi ilovalari (wildcard TLS) |
| `git.<brend>.uz` | SSH git receiver (22 yoki 2222 port) |
| `registry.<brend>.uz` | Ichki Docker registry (tashqariga yopiq) |
| `<brend>.dev` yoki `.app` | Xalqaro ko'rinish uchun, ixtiyoriy |

