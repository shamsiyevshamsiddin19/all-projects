# 🤖 Quiz Bot

`.txt` fayldan savollarni o'qib, Telegram **quiz (test) poll**lariga aylantiradigan bot.
Ketma-ket savol beradi, javoblarni tekshiradi va ball hisoblaydi.

## 📥 O'rnatish

```powershell
cd "E:\Project\now\Quiz -bot"
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## ▶️ Ishga tushirish

```powershell
python bot.py
```

Token `.env` faylida saqlangan. Kerak bo'lsa o'zgartiring.

## 📄 Fayl formatlari

Bot ikkala formatni ham (hatto bitta faylda aralash) tushunadi.

**1-format (harfli):**
```
1. Savol matni
A) Variant
B) Variant
C) Variant
D) Variant
Javob: A
```

**2-format (+/- belgili — to'g'ri javob `+`):**
```
# Savol matni
+ To'g'ri variant
- Variant
- Variant
- Variant
```

## 💬 Foydalanish

1. Botga `/start` yozing.
2. `.txt` faylni yuboring → bot uni saqlaydi.
3. **▶️ Testni boshlash** tugmasini bosing.
4. Savollarga javob bering, oxirida natijangizni ko'rasiz.

Buyruqlar:
- `/testlar` — saqlangan testlar ro'yxati
- `/stop` — joriy testni to'xtatish

## 📁 Tuzilma

| Fayl | Vazifasi |
|------|----------|
| `bot.py` | Asosiy bot mantigʻi |
| `parser.py` | Fayldan savollarni o'qish |
| `storage.py` | Testlarni JSON'da saqlash |
| `config.py` | Sozlamalar (token, adminlar) |
| `quizzes/` | Saqlangan testlar (avtomatik yaratiladi) |

## 🔒 Adminlar

Faqat ma'lum foydalanuvchilar test yuklashi uchun `.env` da:
```
ADMIN_IDS=123456789,987654321
```
Bo'sh qoldirilsa — hamma yuklay oladi.
