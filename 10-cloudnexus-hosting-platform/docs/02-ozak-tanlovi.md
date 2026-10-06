# 02 — Deploy o'zagi: noldan yozamizmi yoki tayyor asos ustiga?

## 2.1 Savolning mohiyati

"Deploy o'zagi" deganda to'rtta ishni bajaradigan qism tushuniladi:

1. **Build** — foydalanuvchi kodidan ishga tushadigan narsa yasash
2. **Run** — uni konteyner sifatida limit bilan ishga tushirish
3. **Route** — `nomi.app.domen.uz` ni shu konteynerga ulash + TLS
4. **Operate** — log, restart, env, rollback, o'chirish

Bu to'rttasi uchun tayyor ochiq manba yechimlar bor. Savol — ularni
olamizmi yoki o'zimiz yozamizmi.

## 2.2 Variantlar tahlili

### A. Dokku ustiga o'rash

Dokku — "bitta serverdagi ochiq Heroku". Bash + Docker ustida qurilgan.

- **Beradi:** `git push dokku main` → buildpack avtomatik aniqlaydi → deploy.
  Let's Encrypt plagini, Postgres/Redis plaginlari, zero-downtime deploy
- **Plus:** MVP'ni **eng tez** chiqarish. Bizga faqat ro'yxatdan o'tish,
  panel va AI qatlami qoladi
- **Minus:**
  - **API yo'q** — faqat CLI. Biz `subprocess.run(["dokku", "apps:create", ...])`
    qilamiz. Bu mo'rt: chiqish formati o'zgarsa kodimiz sinadi, xato
    xabarlarini parse qilish kerak, parallel chaqiruvlar race beradi
  - **Bitta nodega mo'ljallangan.** Bosqich 2 (multi-node) da butunlay
    qayta yozish kerak bo'ladi
  - **Resurs hisobi yo'q** — billing uchun kerakli CPU-sekund / RAM-soat
    o'lchovini o'zimiz yig'ishimiz kerak, ya'ni Dokku'ning foydasi kamayadi
  - Ko'p ijarachi (multi-tenant) uchun yozilmagan — barcha ilovalar bitta
    Docker daemon'da, izolyatsiya sozlamalari qo'lda qo'shiladi
- **Hukm:** 🟡 Faqat "2 hafta ichida demo kerak" bo'lsa.

### B. Coolify ustiga

Coolify — self-hosted Vercel/Netlify alternativi, chiroyli UI, multi-server.

- **Plus:** UI tayyor, DB, backup, multi-server bor
- **Minus:**
  - **Bir ijarachi uchun yozilgan** (o'z serverini o'zi boshqaradigan odam).
    Ko'p mijozli SaaS qilish — uning tabiatiga qarshi kurash
  - **O'z brendimizni boshqa UI ustiga qo'yish qiyin** — mahsulot ko'rinishi
    bizning emas
  - ⚠️ **Litsenziyani tekshirish kerak** — ochiq manba mahsulotni
    o'zgartirib SaaS sifatida sotish ba'zi litsenziyalarda (AGPL)
    manba kodni ochishni talab qiladi. Buyurtma qilishdan oldin
    `LICENSE` faylini o'qing
- **Hukm:** ❌ Bizning maqsadga mos emas.

### C. Kubernetes / k3s

- **Plus:** Sanoat standarti, cheksiz miqyos, tayyor ekotizim (ingress, HPA,
  operator pattern)
- **Minus:** Yakka dasturchi uchun **katta murakkablik soliqi**. k3s o'zi
  512 MB–1 GB RAM yeydi. CRD, operator, RBAC, networking (CNI) — har biri
  alohida mavzu. MVP 2 hafta emas, 2 oy cho'ziladi
- **Hukm:** ❌ Hozir emas. ✅ Bosqich 5+ da, 10+ node bo'lganda migratsiya yo'li.

### D. O'z control plane + Docker + Nixpacks — **✅ TAVSIYA**

**Nixpacks** — Railway'ning ochiq builderi (MIT, Rust'da yozilgan):
`nixpacks build ./loyiha` → Dockerfile **yozmasdan** Node, Python, Go, PHP,
Rust, Deno, Java ni avtomatik aniqlaydi va OCI image yasaydi.

Bu bizning butun g'oyamizning kaliti: **AI kod yozdi, hech narsa
sozlamadi — biz o'zimiz tushunib olamiz.**

Alternativa: **Cloud Native Buildpacks** (`pack` CLI, Heroku/Paketo) — ancha
kuchli va standart, lekin sekinroq va murakkabroq. Nixpacks'dan boshlab,
keraksa CNB qo'shish mumkin.

```
Foydalanuvchi kodi
   │
   ├─ Dockerfile bormi? ──► ha  ──► docker build (foydalanuvchi o'zi hal qildi)
   │                        yo'q
   ├─ nixpacks detect ──► Node / Python / Go / PHP / static...
   │                        │
   │                        └─► OCI image
   └─ ichki registry ──► worker node ──► docker run (limit bilan)
                                             │
                                        Traefik label
                                             │
                                     nomi.app.domen.uz + TLS
```

- **Plus:**
  - **To'liq nazorat** — billing uchun kerak bo'lgan aniq resurs o'lchovini
    boshidan to'g'ri yig'amiz
  - **AI-native API birinchi darajali** — bu mahsulotning o'zi, qobiq emas
  - Multi-node boshidan rejalashtiriladi
  - Mahsulot bizniki, hech kimning litsenziyasiga bog'liq emas
- **Minus:** Ko'proq ish. Lekin **o'zagi kutganingizdan kichik**: Docker API
  + Nixpacks + Traefik birgalikda Dokku funksiyasining ~80% ini beradi, va
  "yopishtiruvchi kod" aslida bizning mahsulot mantiqimiz

### 2.3 Qaror

> **O'z control plane. Build — Nixpacks. Run — Docker API. Route — Traefik.**
>
> Dokku'dan **g'oyalarni** o'g'irlaymiz (git receiver dizayni, deploy
> bosqichlari, plagin modeli), kodini emas.

**Sabab:** pulli tariflar bo'lishi tasdiqlandi. Billing aniq metering
talab qiladi; metering esa konteyner hayot aylanishini o'zimiz
boshqarmasak to'g'ri ishlamaydi. Tayyor PaaS ustiga o'rash — billingni
boshidan mo'rt qiladi, bu esa to'g'ridan-to'g'ri pul yo'qotish demakdir.

## 2.4 Run vaqtidagi muhim tanlov: Docker vs Podman

| | Docker | Podman (rootless) |
|---|---|---|
| Xavfsizlik | root daemon — escape bo'lsa butun node | rootless, daemonsiz — escape ham oddiy foydalanuvchi |
| Ekotizim | Traefik, registry, hamma narsa birinchi navbatda Docker uchun | mos, lekin ba'zan yamoq kerak |
| Tajriba | Sizda bor (hotelbookingbot docker compose) | yo'q |

**Tavsiya:** Bosqich 1 da **Docker + userns-remap + qat'iy cgroup/seccomp**
(tajriba bor, tez boshlanadi). Bosqich 3 da **rootless Podman** yoki
**gVisor** ga o'tishni rejaga kiritish — ikkinchi mijoz pul to'lagandan
keyin xavfsizlik birinchi o'ringa chiqadi. Batafsil: 04-xavfsizlik.
