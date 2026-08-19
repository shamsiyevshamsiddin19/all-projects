# Yordamchi

Shaxsiy yordamchi — testlar, maqsadlar, sport, arxiv va kun jadvali bitta joyda.

**Stack:** FastAPI (Python) backend + PostgreSQL, build-siz vanilla JS frontend (SPA, `assets/js/app2/`).

- `backend_py/` — API (`app/handlers/*.py`), sozlamalar `app/config.py`, sxema `database/schema.sql`
- `index.html` + `assets/js/app2/` — frontend (yagona sahifa, hash-router)
- `assets/js/core/` — umumiy infratuzilma (server-sinxronlangan `localStorage`, ikonlar, log)

Lokal ishga tushirish: `backend_py/README.md` ga qarang.

## Deploy qilishdan oldin

```bash
python tools/check_contracts.py
```

Loyihada bir xil ro'yxat bir necha faylda takrorlanadi — sayt frontendida
(JS), sayt backendida (Python) va botda (Python). Ular uzilib qolsa
**hech qanday xato chiqmaydi**, ilova jimgina noto'g'ri ishlaydi. Amalda
uchragan uchta holat:

| Uzilish | Oqibati |
|---|---|
| `reading` backend ruxsat ro'yxatida yo'q edi | O'qish bo'limining har bir yozuvi jimgina tashlandi — Tarix ham, Statistika ham uni hech ko'rsatmadi |
| `press` backend `CATEGORIES` da yo'q edi | Yangi kategoriyadagi mashqlar saytga umuman yetib bormadi |
| `dasturlash` botning `CHANNEL_TOPICS` ida yo'q edi | Saytda "Saqlandi" chiqardi, lekin bot mavzuni jimgina o'chirardi |

Skript shu ro'yxatlarni o'qib solishtiradi va farq bo'lsa aytadi
(uzilish topilsa 1 kod bilan chiqadi). Yangi bo'lim, kategoriya yoki
mavzu qo'shganda **albatta ishlating** — uchala xato ham shu tekshiruv
bilan darrov ko'rinadi.
