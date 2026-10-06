# 🛒 15-wstore-digital-marketplace (wstore.uz)

Raqamli mahsulotlar bozori (raqamli kod loyihalari, botlar, saytlar, ilovalar) savdo platformasi.

Loyiha ichida 2 ta to'liq mustaqil arxitektura mavjud:

---

## 📁 Papkalar Strukturasi

```
15-wstore-digital-marketplace/
├── django/       # Django 5 (Python) to'liq backend va monolit veb-ilova
└── next.js/      # Next.js 15 (React 19 + TypeScript + Prisma) zamonaviy veb-ilova
```

---

## 1. 🐍 `django/` — Django 5 Platformasi

- **Texnologiyalar:** Python 3.12, Django 5, PostgreSQL / SQLite, HTML5, Vanilla CSS/JS
- **Autentifikatsiya:** Google OAuth 2.0
- **To'lovlar:** Click Merchant API integratsiyasi
- **Xususiyatlari:** Ko'p tilli (uz, ru, en), sotuvchi/xaridor panellari, filtrlar, savat, sharhlar

👉 Batafsil qo'llanma: [`django/README.md`](django/README.md)

---

## 2. ⚡ `next.js/` — Next.js 15 Platformasi

- **Texnologiyalar:** Next.js 15 (App Router), React 19, TypeScript, TailwindCSS, Prisma ORM
- **Autentifikatsiya:** Auth.js (NextAuth v5) + Google OAuth
- **To'lovlar:** Click, Payme, Uzum to'lovlari va webhooklari
- **Fayl saqlash:** Cloudflare R2 (kod arxivlarini xavfsiz yuklab berish)
- **Xususiyatlari:** Dark UI dizayn, katalog filtrlari, sotuvchi va admin paneli

👉 Batafsil qo'llanma: [`next.js/README.md`](next.js/README.md)
