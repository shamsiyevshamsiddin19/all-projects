# 🧮 Modern Scientific Calculator (Django)

Ushbu loyiha zamonaviy va professional ko'rinishdagi **Scientific (Ilmiy) Kalkulyator** veb-ilovasi bo'lib, **to'liq toza Django (Python backend)** asosida qurilgan.

## ✨ Asosiy Xususiyatlari
- **To'liq Python Backend:** Hech qanday JavaScript ishlatilmagan — barcha hisob-kitoblar, xotira va tarix Django orqali ishlaydi.
- **Barcha Matematik & Ilmiy Funksiyalar:** 
  - Asosiy amallar (`+`, `-`, `×`, `÷`, `x^y`)
  - Trigonometriya (`sin`, `cos`, `tan`, `cot`, `sec`, `csc`)
  - Daraja va eksponentalar (`x²`, `x³`, `eˣ`, `10ˣ`, `2ˣ`)
  - Logarifmlar va Faktorial (`ln`, `logₓ`, `x!`, `|x|`)
  - Burchak birliklari (`Deg` va `Rad`)
- **Tarix va Ma'lumotlar Bazasi:** Barcha hisob-kitoblar SQLite bazasiga saqlanadi, o'tgan natijalarni qayta ekranga chiqarish va tarixni tozalash mumkin.
- **Tarixni Eksport qilish:** Hisob-kitoblar tarixini `.txt` fayl ko'rinishida yuklab olish (Save History) va chop etish (Print) imkoniyati.
- **Ko'p rejimli (Modes):** `Standard`, `Scientific`, `Programmer` (HEX, DEC, OCT, BIN qiymatlari bilan).
- **Mavzular (Themes):** Tungi (Dark) va Kunduzgi (Light) zamonaviy dizayn.
- **Moslashuvchan Dizayn (Responsive):** Katta ekranlar, noutbuklar, planshetlar va mobil telefonlar uchun moslashgan.

## 🚀 Ishga tushirish (Local Setup)

1. **Repozitoriyani klonlash:**
   ```bash
   git clone https://github.com/shamsiyevshamsiddin19/calculator.git
   cd calculator
   ```

2. **Virtual muhit yaratish va faollashtirish:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux / Mac
   # venv\Scripts\activate   # Windows
   ```

3. **Kutubxonalarni o'rnatish:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Migratsiyalarni bajarish:**
   ```bash
   python manage.py migrate
   ```

5. **Serverni ishga tushirish:**
   ```bash
   python manage.py runserver
   ```
   Brauzerda ochish: `http://127.0.0.1:8000/`
