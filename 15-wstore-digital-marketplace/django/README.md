# 🛒 wstore.uz — Django Backend & Platform

**wstore.uz** — raqamli mahsulotlar (tayyor kod loyihalari, botlar, veb-saytlar, mobil ilovalar va skriptlar) marketining Django 5 versiyasi.

---

## 🚀 Texnologiyalar to'plami

- **Backend:** Python 3.12, Django 5.x
- **Ma'lumotlar bazasi:** PostgreSQL (ishlab chiqarish) / SQLite (lokal test)
- **Frontend & Stil:** HTML5, Modern CSS3 (Dark Theme dizayn), Vanilla JavaScript
- **To'lov integratsiyasi:** Click Merchant API & to'lov ko'prigi
- **Autentifikatsiya:** Google OAuth 2.0 (yagona xavfsiz kirish)
- **Ko'p tillilik (i18n):** O'zbekcha (asosiy), Ruscha, Inglizcha

---

## ✨ Imkoniyatlar va Funksiyalar

1. **Katalog & Qidiruv:**
   - Kategoriya va texnologiyalar (Python, Django, Flutter, PHP, JS va h.k.) bo'yicha saralash
   - Narx oralig'i, reyting va saralash (eng yangi, arzon, qimmat)
   - Jonli qidiruv tizimi

2. **Google OAuth orqali kirish:**
   - Parolsiz, xavfsiz va bir bosqichli Google autentifikatsiyasi
   - Yangi foydalanuvchilar uchun avtomatik profil yaratish

3. **Sotuvchi va Xaridor Paneli:**
   - Yangi mahsulot yuklash (fayllar, skrinshotlar, narx, tavsif)
   - Buyurtmalar tarixi va to'lov holati
   - Sotuvchi balansi va mablag'ni yechib olish so'rovlari

4. **To'lov Tizimi (Click API):**
   - Click tizimi orqali to'lov havolasini generatsiya qilish
   - To'lov tasdiqlangach faylni xavfsiz yuklab olish imkoniyati

5. **Lokalizatsiya (Ko'p tilli):**
   - Sayt interfeysini o'zbek, rus va ingliz tillarida to'liq qo'llab-quvvatlash (`locale/`)

---

## 🛠️ Ishga tushirish

```bash
# 1. Virtual muhit yaratish
python3 -m venv venv
source venv/bin/activate

# 2. Bog'liqliklarni o'rnatish
pip install -r requirements.txt

# 3. Muhit fayli (.env)
cp .env.example .env

# 4. Migratsiyalar
python manage.py migrate

# 5. Namunaviy ma'lumotlar (ixtiyoriy)
python manage.py seed_data

# 6. Serverni yurgizish
python manage.py runserver
```

---

## 📂 Struktura

```
django/
├── apps/
│   ├── core/         # Asosiy modellar, Google OAuth, yordamchi filtrlar
│   ├── orders/       # Buyurtmalar, to'lovlar, sotuvchi balansi
│   └── store/        # Mahsulotlar katalogi, sharhlar, wishlist
├── config/           # Django settings, asgi, wsgi, urls
├── locale/           # uz, ru, en tarjima fayllari
├── media/            # Mahsulot skrinshotlari va muqovalari
├── static/           # CSS, JS, rasmlar va logotiplar
├── templates/        # HTML andozalari
├── .env.example      # Namunaviy konfiguratsiya
├── manage.py         # Django boshqaruv skripti
└── requirements.txt  # Python paketlari
```
