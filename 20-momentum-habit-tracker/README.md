# 🎓 Tracker App — Teacher–Student Task Management System

**Tracker App** — bu o'qituvchilar va talabalar uchun vazifalarni boshqarish, topshirilgan ishlarni baholash, feedback berish, tahliliy ko'rsatkichlarni kuzatish hamda **PDF va Excel (XLSX)** formatida professional hisobotlarni shakllantirish uchun yaratilgan zamonaviy kross-platforma tizim.

---

## 🚀 Texnologiyalar Staki

- **Backend**: Python 3.12+ / **FastAPI (Async)** / **SQLAlchemy 2.0** / **Pydantic v2** / **Asyncpg & Aiosqlite**
- **Security**: **JWT Access (30m) & Refresh Token (7d)** / **Bcrypt** xeshlash / **RBAC** (Teacher & Student) / **IDOR Protection**
- **Eksport Dvigatellari**: **ReportLab** (Professional PDF) & **OpenPyXL** (Formatlangan Excel jadvallari)
- **Frontend & Mobile**: **Flutter 3.x (Dart 3.x)** — Android, iOS, macOS, Linux, Web uchun yagona pixel-perfect kod bazasi
- **Dizayn Tizimi**: **Linear / Notion / Apple** estetikasi, **Dark Mode** & **Light Mode**, `fl_chart` interaktiv grafiklari

---

## 📁 Loyiha Strukturasi

```
Tracker-app/
├── backend/
│   ├── app/
│   │   ├── core/               # Konfiguratsiya, xavfsizlik (JWT, Bcrypt), DB sessiyalari
│   │   ├── models/             # 10 ta SQLAlchemy relational jadvallari
│   │   ├── schemas/            # Pydantic v2 validatsiya schemalari
│   │   ├── api/v1/             # Versiyalangan REST API routerlar (auth, groups, assignments...)
│   │   ├── services/           # Asosiy biznes logika va hisob-kitoblar
│   │   ├── exports/            # PDF (ReportLab) va Excel (OpenPyXL) generator modullari
│   │   └── main.py             # FastAPI ilovasi kirish nuqtasi
│   ├── tests/                  # Pytest to'liq integratsiya testlari (100% PASSED)
│   ├── storage/uploads/        # Xavfsiz lokal fayllar ombori
│   ├── requirements.txt
│   └── .env
│
├── mobile/
│   ├── lib/
│   │   ├── core/theme/         # Design Tokens, Dark & Light mavzular, Ranglar
│   │   ├── core/network/       # Dio API Client, Token Interceptor, Error handler
│   │   ├── features/
│   │   │   ├── auth/           # Login, Register (Rol tanlash), Splash
│   │   │   ├── dashboard/      # Teacher & Student boshqaruv panellari
│   │   │   ├── groups/         # Guruhlar ro'yxati, yaratish va taklif kodi
│   │   │   ├── assignments/    # Vazifalar yaratish, ko'rish, filtrlar
│   │   │   ├── submissions/    # Topshirish, baholash, izoh yozish
│   │   │   ├── reports/        # Tahliliy hisobotlar, 1-klik PDF/Excel yuklash
│   │   │   └── profile/        # Profil sozlamalari, Dark mode, Til
│   │   ├── shared/widgets/     # Reusable Button, TextField, StatCard, Badges
│   │   └── main.dart           # Flutter MultiProvider ilova kirish nuqtasi
│   ├── test/                   # Flutter smoke & widget testlari
│   └── pubspec.yaml
└── prompt.md                   # Master texnik topshiriq hujjati
```

---

## ⚡️ Tezkor Ishga Tushirish Qo'llanmasi

### 1. Backend Serverni Ishga Tushirish:
```bash
cd backend
# Virtual muhitni faollashtirish
source venv/bin/activate

# Serverni uvicorn orqali ishga tushirish
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
- **API Swagger Hujjatlari**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Salomatlik tekshiruvi (Health Check)**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

### 2. Backend Testlarini Ishga Tushirish:
```bash
cd backend
PYTHONPATH=. venv/bin/pytest tests/test_api.py -v
```

### 3. Mobile / Desktop Ilovani Ishga Tushirish:
```bash
cd mobile

# Paketlarni yangilash
flutter pub get

# Testlarni tekshirish
flutter test

# Ilovani ishga tushirish (Linux desktop, Android yoki Web)
flutter run
```

---

## 🔑 Asosiy API Endpointlar

| Metod | Endpoint | Ruxsat | Tavsif |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/auth/register` | Ochiq | O'qituvchi yoki Talaba ro'yxatdan o'tishi |
| `POST` | `/api/v1/auth/login` | Ochiq | Email va parol bilan tizimga kirish (JWT) |
| `GET` | `/api/v1/auth/me` | Auth | Joriy kirgan foydalanuvchi ma'lumotlari |
| `GET` | `/api/v1/groups` | Auth | Foydalanuvchining guruhlari |
| `POST` | `/api/v1/groups` | Teacher | Yangi guruh yaratish (6 xonali taklif kodi bilan) |
| `POST` | `/api/v1/groups/join` | Student | Taklif kodi orqali guruhga ulanish |
| `GET` | `/api/v1/assignments` | Auth | Vazifalar ro'yxati (Filtr, qidiruv, saralash) |
| `POST` | `/api/v1/assignments` | Teacher | Yangi vazifa yaratish (deadline, ustuvorlik) |
| `POST` | `/api/v1/assignments/{id}/submit` | Student | Vazifaga javob matni va fayllarni topshirish |
| `POST` | `/api/v1/submissions/{id}/review` | Teacher | Topshiriqni baholash (0-100 ball), feedback berish |
| `GET` | `/api/v1/analytics/dashboard` | Auth | Rol bo'yicha tahliliy statistika va grafiklar |
| `GET` | `/api/v1/analytics/export/pdf` | Teacher | Rasmiy PDF hisobotini yuklab olish |
| `GET` | `/api/v1/analytics/export/excel` | Teacher | Excel (XLSX) hisobotini yuklab olish |
| `POST` | `/api/v1/files/upload` | Auth | Xavfsiz fayl yuklash (PDF, DOCX, ZIP, Rasm) |

---

## 📄 Litsenziya
Ushbu loyiha maxsus ta'lim samaradorligini oshirish maqsadida ishlab chiqilgan.
