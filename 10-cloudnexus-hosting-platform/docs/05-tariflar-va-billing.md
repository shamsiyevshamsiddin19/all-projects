# 05 — Tariflar va billing arxitekturasi

> Pulli tariflar bo'lishi **tasdiqlangan**, shu sababli billing MVP'dan
> keyin yamoq sifatida emas, arxitekturaga **boshidan** kiritiladi.
>
> ⚠️ Quyidagi narxlar **illyustrativ** — kurs va provayder narxlari
> o'zgaradi. Ishga tushirishdan oldin 1.4-bosqich real xarajati bilan
> qayta hisoblang.

## 5.1 Xarajat asosi (unit economics)

Bosqich 2 infratuzilmasi (01-hujjat):

| Qism | Taxminiy narx/oy |
|---|---|
| Control node (CX32) | ~7 € |
| Builder (CPX31, ephemeral) | ~14 € |
| Worker (AX41 dedicated, 64 GB) | ~45 € |
| DB node (CX32) | ~7 € |
| Backup (Storage Box 1 TB) | ~4 € |
| Domen, pochta, Sentry, rezerv | ~8 € |
| **Jami** | **~85 €/oy** |

Sotiladigan sig'im: worker'dan ~55 GB foydali RAM.

```
512 MB slot soni (to'liq zichlikda) = 55 / 0.5 ≈ 110 ta
Bitta slot tannarxi = 85 € / 110 ≈ 0.77 €/oy
Real band bo'lish 50% deb olsak = ~1.55 €/oy  ≈  21 000 so'm
```
*(1 € ≈ 13 500 so'm deb olindi — kursni tekshiring)*

➡️ **512 MB ilovani 39 000 so'mga sotish ~2x marja beradi.** Statik sayt
tannarxi deyarli nol — shu sababli u bepul tarifning asosi bo'ladi.

**Muhim xulosa:** foyda zichlikdan keladi. Shu sababli "idle bo'lsa
uxlatish" (scale-to-zero) — bu qulaylik emas, **biznes modelining sharti**.

## 5.2 Tariflar (taklif)

| | **Bepul** | **Start** | **Pro** | **Biznes** |
|---|---|---|---|---|
| Narx/oy | 0 | **39 000** | **119 000** | **349 000** |
| Statik sayt | 3 | 10 | ∞ | ∞ |
| Backend ilova | 1 × 256 MB | 3 × 512 MB | 10 × 1 GB | 30 × 2 GB |
| Idle'da uxlaydi | ✅ 30 daq | ❌ | ❌ | ❌ |
| Trafik | 5 GB | 50 GB | 200 GB | 1 TB |
| Build daqiqa | 100 | 500 | 2000 | ∞ |
| Log saqlash | 1 kun | 7 kun | 30 kun | 30 kun |
| O'z domeni | ❌ | ✅ | ✅ | ✅ |
| PostgreSQL | ❌ | 1 × 1 GB | 3 × 10 GB | alohida konteyner |
| Backup | ❌ | haftalik | kunlik | kunlik + PITR |
| Preview deploy (PR) | ❌ | ❌ | ✅ | ✅ |
| Jamoa a'zolari | 1 | 1 | 3 | 15 |
| Qo'llab-quvvatlash | hujjat | email | Telegram, 24 soat | prioritet |

**Qo'shimchalar (add-on):** +512 MB RAM, +1 ilova, +DB, +trafik,
+saqlash — alohida o'lchov bo'yicha sotiladi. Bu ARPU'ni oshiradigan
eng oson yo'l.

⚠️ **Bepul tarifdagi backend uchun telefon tasdiqlash majburiy**
(04-hujjat, 4.2). Bu suiiste'molni to'xtatadigan eng samarali chora.

### "Statik sayt" nimani o'z ichiga oladi

Jadvaldagi "statik sayt" — **toza HTML/CSS/JS** va **React/Vue/Vite/Svelte/
Astro** (build qilinib statik faylga aylanadigani) — **ikkisi ham**.
Ularning runtime RAM'i nol, shu sababli bepul tarifda berilishi mumkin
(batafsil: [03-hujjat 3.2a](03-arxitektura.md#32a-ilova-turlarini-aniqlash--statik-nimani-bildiradi)).

**Next.js SSR, Nuxt, Remix — statik emas**, doimiy Node protsessi kerak,
demak "backend ilova" kvotasidan yeydi. Panelda deploydan **oldin**
ko'rsatilishi kerak: *"Bu loyiha doimiy ishlaydigan ilova — Start tarif
kerak"*. Aks holda foydalanuvchi "shunchaki sayt qo'ydim" deb noliydi.

⚠️ **Build limiti runtime kvotasidan ajratilgan.** `vite build` 1–2 GB RAM
yeyishi mumkin, holbuki ilovaning runtime kvotasi 0 MB. Bepul tarifda ham
build uchun **2 GB RAM + 10 daqiqa** beriladi (builder node'da).
Aks holda bepul foydalanuvchi React saytini umuman build qila olmaydi —
va bu asosiy kirish oqimini yopib qo'yadi. Cheklov RAM emas,
**build daqiqalari** orqali qo'yiladi.

## 5.3 To'lov modeli: obuna emas, **balans** — muhim qaror

O'zbekistonda avtomatik takrorlanuvchi karta to'lovi (recurring) ishonchsiz:
karta muddati, limit, bank rad etishi. Mahalliy hosting bozorida
**"hisobni to'ldirish"** modeli standart va foydalanuvchiga tushunarli.

**Tavsiya:**
```
Foydalanuvchi hisobni to'ldiradi  →  balans
Har kuni kechasi: balansdan kunlik tarif narxi yechiladi
Balans < 3 kunlik  →  Telegram + email ogohlantirish
Balans 0           →  3 kun grace  →  ilovalar to'xtatiladi (ma'lumot saqlanadi)
To'xtatilgandan 30 kun  →  o'chirish (oldin 3 marta ogohlantirish)
```

Afzalligi: o'lchov bo'yicha (usage-based) qo'shimchalar bilan tabiiy
qo'shiladi, qaytarib berish (refund) muammosi yo'q, kartani saqlash
talabi yo'q (PCI yuki kamayadi).

**To'lov tizimlari:** Payme, Click, Uzum Bank. Hammasi **yuridik shaxs**
(YaTT yoki MChJ) talab qiladi. Agregator (Atmos, Paynet) bittada
bir nechtasini beradi — yakka dasturchi uchun soddaroq.

⏱️ **Bu yo'lning eng uzun qismi** — shartnoma va integratsiya haftalar
oladi. Kod yozish bilan **parallel** boshlanishi kerak, ketma-ket emas.

## 5.4 Metering — texnik tomoni

Yagona haqiqat manbasi:
```sql
app_usage_hourly (
  app_id, hour,
  cpu_seconds      numeric,  -- cgroup cpuacct dan
  mem_gb_hours     numeric,  -- 60s namunalar o'rtachasi
  egress_bytes     bigint,   -- konteyner tarmoq statistikasi
  disk_gb          numeric,  -- volume o'lchami
  build_seconds    numeric
)
```
- Agent 60 sekundda namuna oladi → control plane soatlik rollup qiladi
- Kunlik `invoice_line` yoziladi → balansdan yechiladi
- Foydalanuvchi panelida **real vaqtda** ko'rsatiladi (kutilmagan hisob
  bo'lmasligi uchun — bu Vercel'ning eng katta shikoyati)

### Kvota majburlash (quota enforcement)
| Resurs | Qanday majburlanadi |
|---|---|
| RAM | cgroup `memory.max` — qattiq, OOM kill |
| CPU | cgroup `cpu.max` — throttle, o'ldirmaydi |
| Disk | XFS prjquota — yozish xatosi |
| Trafik | Traefik hisoblaydi → chegaradan oshsa 429 / to'xtatish |
| Ilova soni | Control plane'da tekshiriladi |
| Build daqiqa | Navbat ishga tushirishdan oldin tekshiradi |

⚠️ Trafik chegarasi **eng xatarli joy** — virusli bo'lib ketgan sayt bir
kunda 500 GB yeyishi mumkin. Qattiq to'xtatish (hard stop) + darhol
ogohlantirish kerak, "keyin hisob yuboramiz" emas.

## 5.5 Boshqa daromad g'oyalari (keyingi bosqichlar)
- **Domen sotish** — `.uz` registrator bilan hamkorlik, panel ichida
- **Shablon do'koni** — tayyor bot/sayt shablonlari
- **Managed DB** alohida mahsulot sifatida
- **AI kredit** — panel ichida kod tuzatuvchi AI (biz LLM API'ni qayta sotamiz)
- **Oq yorliq (white-label)** — agentliklar uchun
