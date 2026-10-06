# 📄 Document Convertor Bot (Python / aiogram 3 + PostgreSQL)

Eski PHP bot to'liq Python'ga ko'chirildi. Rasm/Fayl → PDF/ZIP, Matn → DOCX, PDF ↔ DOCX,
Office (Word/Excel/PowerPoint) → PDF, OCR (matn tanish), PDF birlashtirish/qirqish/watermark.
Admin panel botning o'zida emas, faqat saytda (`/docs/admin`).

## Tuzilishi

```
document-convertor/
├── run.py                 # kirish nuqtasi (polling + web-admin)
├── core/
│   ├── config.py           # .env dan sozlamalar
│   └── database.py         # PostgreSQL (asyncpg) + sxema
├── handlers/
│   ├── user_handlers.py    # /start, til tanlash, menyu tugmalari
│   └── file_handlers.py    # fayl qabul qilish, konvertatsiya oqimi
├── services/
│   ├── converter.py        # PDF/DOCX/OCR/watermark mantig'i (PyMuPDF, pdf2docx, LibreOffice, Tesseract)
│   ├── utils.py             # majburiy obuna tekshiruvi
│   └── lang.py              # ko'p tillilik (uz/ru/en)
├── web/
│   └── admin.py             # web-admin: statistika, foydalanuvchilar, xabar yuborish, sozlamalar
├── assets/
│   └── tuit_titul.docx      # tayyor shablon fayl
├── import_mysql_dump.py     # eski MySQL bazadan PostgreSQL'ga ko'chirish (bir martalik)
├── requirements.txt
├── deploy.sh                # Hetzner/Ubuntu uchun o'rnatish skripti
└── .env.example
```

## Ishga tushirish

```bash
cd document-convertor
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # va tokenlarni to'ldiring
python run.py
```

**Tizim talablari** (konvertatsiya uchun): `libreoffice` (Office→PDF) va `tesseract-ocr`
(+ `uzb`, `rus`, `eng` til paketlari) serverda o'rnatilgan bo'lishi kerak.

## Xususiyatlar

- Rasm → PDF, Fayl → ZIP (bir nechta fayl yig'ib, bitta natija)
- Matn → DOCX, PDF → DOCX, Office (docx/xlsx/pptx) → PDF
- OCR — rasmdan matn tanish (o'zbek/rus/ingliz)
- PDF birlashtirish, sahifalarga bo'lib qirqish, diagonal watermark
- Natija fayllarni Reply orqali qayta nomlash
- Ko'p tillilik (o'zbek, rus, ingliz)
- Web-admin panel (`/docs/admin`): statistika, foydalanuvchilar, xabar yuborish (broadcast),
  majburiy obuna kanallarini boshqarish — CSRF himoyasi va login rate-limit bilan

## Arxitektura eslatmalari

- Og'ir konvertatsiyalar (LibreOffice, OCR, PDF ishlov) `asyncio.to_thread` orqali alohida
  threadda ishlaydi — bitta foydalanuvchining vazifasi butun botni bloklamaydi.
- Har bir chat uchun lock orqali bir vaqtda ikkita konvertatsiya boshlanishining oldi olinadi.
- `pdfbot.service` uchun `PATH` ga tizim yo'llari qo'shilishi shart — aks holda `libreoffice`
  va `tesseract` subprocess orqali topilmaydi (`deploy.sh`da hisobga olingan).
