# FastAPI darsligi — Barcha mavzular (to'liq, 8 bo'lim, 22 dars)

_Ushbu darslik noldan (FastAPI nima ekanidan) tortib, Pydantic validatsiyasi, loyiha tashkil etish, PostgreSQL bilan asinxron ma'lumotlar bazasi integratsiyasi, JWT autentifikatsiya va rol-asosidagi ruxsatlar, WebSocket va testlashdan, Docker+Nginx orqali to'liq production deploy va GitHub Actions bilan CI/CD avtomatlashtirishgacha bo'lgan to'liq yo'lni qamrab oladi. Daraja pastdan yuqoriga: 00-bob → 07-bob. Barcha terminal buyruqlari **Ubuntu** uchun moslashtirilgan, va darslik siz avval yaratgan Python, Django, Docker va Git/GitHub darsliklariga faol, izchil bog'liq holda tuzilgan. Texnik ma'lumotlar (FastAPI 0.141.x, Pydantic v2.13.x, `uv` paket menejeri, `pwdlib`/`PyJWT` xavfsizlik kutubxonalari) 2026-yildagi joriy holat bo'yicha tadqiqot asosida tekshirilgan._

---

## 00-BOB — Kirish

| № | Mavzu | Fayl |
|---|---|---|
| 0.1 | FastAPI nima va nima uchun tanlanadi | 0.1-fastapi-nima-nima-uchun-tanlanadi.md |
| 0.2 | Muhitni sozlash: Ubuntu'da FastAPI loyihasini boshlash (`uv`) | 0.2-muhitni-sozlash-ubuntu-uv.md |

## 01-BOB — Asoslar

| № | Mavzu | Fayl |
|---|---|---|
| 1.1 | Birinchi FastAPI ilovasi va avtomatik hujjatlar | 1.1-birinchi-ilova-avtomatik-hujjatlar.md |
| 1.2 | Path va Query parametrlar | 1.2-path-query-parametrlar.md |
| 1.3 | Request Body va Response Model | 1.3-request-body-response-model.md |

## 02-BOB — Pydantic va validatsiya

| № | Mavzu | Fayl |
|---|---|---|
| 2.1 | Pydantic v2 chuqur: Field, validatorlar va ichma-ich modellar | 2.1-pydantic-chuqur-validatorlar.md |
| 2.2 | Xatolarni boshqarish, fayl yuklash va formalar | 2.2-xatolarni-boshqarish-fayl-yuklash.md |

## 03-BOB — Routing va Dependency Injection

| № | Mavzu | Fayl |
|---|---|---|
| 3.1 | APIRouter bilan loyihani tashkil etish | 3.1-apirouter-loyiha-tuzilmasi.md |
| 3.2 | Dependency Injection (Depends) asoslari | 3.2-dependency-injection-depends.md |
| 3.3 | Middleware va CORS | 3.3-middleware-cors.md |

## 04-BOB — Ma'lumotlar bazasi

| № | Mavzu | Fayl |
|---|---|---|
| 4.1 | SQLModel asoslari va PostgreSQL bilan ulanish | 4.1-sqlmodel-postgresql-asoslari.md |
| 4.2 | CRUD amaliyotlari | 4.2-crud-amaliyotlari.md |
| 4.3 | Alembic bilan migratsiyalar | 4.3-alembic-migratsiyalar.md |
| 4.4 | Asinxron ma'lumotlar bazasi (async SQLAlchemy + asyncpg) | 4.4-async-database.md |

## 05-BOB — Autentifikatsiya va xavfsizlik

| № | Mavzu | Fayl |
|---|---|---|
| 5.1 | OAuth2, parol xeshlash va JWT token | 5.1-oauth2-parol-xeshlash-jwt.md |
| 5.2 | Ruxsatlarni boshqarish (Role-Based Access Control) | 5.2-role-based-ruxsatlar.md |

## 06-BOB — Ilg'or mavzular

| № | Mavzu | Fayl |
|---|---|---|
| 6.1 | Background Tasks va WebSocket | 6.1-background-tasks-websocket.md |
| 6.2 | FastAPI'ni testlash: pytest va httpx | 6.2-testing-pytest-httpx.md |
| 6.3 | Lifespan events va asinxron dasturlash bo'yicha eng yaxshi amaliyotlar | 6.3-lifespan-async-best-practices.md |

## 07-BOB — Production va Deploy

| № | Mavzu | Fayl |
|---|---|---|
| 7.1 | FastAPI ilovasini Docker bilan konteynerlashtirish | 7.1-docker-bilan-konteynerlashtirish.md |
| 7.2 | Production: Uvicorn worker'lari va Nginx | 7.2-nginx-worker-production.md |
| 7.3 | CI/CD bilan GitHub Actions va yakuniy real loyiha | 7.3-cicd-github-actions-yakuniy-loyiha.md |

---

## Umumiy ma'lumot

- **00-bob (0.1-0.2):** Kirish — FastAPI nima, uning Flask/Django'dan farqi, asinxron (ASGI) dasturlash asoslari, `uv` paket menejerini Ubuntu'ga o'rnatish va `fastapi[standard]` bilan birinchi loyihani boshlash.
- **01-bob (1.1-1.3):** Asoslar — birinchi endpoint va avtomatik Swagger UI/ReDoc hujjatlari, path/query parametrlar va ularning avtomatik validatsiyasi, Pydantic orqali request body va `response_model` bilan javobni nazorat qilish.
- **02-bob (2.1-2.2):** Pydantic va validatsiya — `Field`, `field_validator`/`model_validator`, ichma-ich modellar, `ConfigDict`; `HTTPException` orqali biznes xatolarini boshqarish, `UploadFile` bilan fayl yuklash, `Form()` bilan HTML formalar.
- **03-bob (3.1-3.3):** Routing va DI — `APIRouter` orqali ko'p fayldan iborat loyiha tuzilmasi, `Depends()` orqali Dependency Injection (zanjirlash bilan), Middleware va `CORSMiddleware` orqali frontend-backend integratsiyasi.
- **04-bob (4.1-4.4):** Ma'lumotlar bazasi — SQLModel va Docker orqali PostgreSQL, to'liq CRUD amaliyotlari va `Relationship`, Alembic bilan xavfsiz migratsiyalar, `asyncpg` orqali to'liq asinxron ma'lumotlar bazasi integratsiyasi.
- **05-bob (5.1-5.2):** Autentifikatsiya — `pwdlib` bilan parol xeshlash, `PyJWT` bilan token yaratish, `OAuth2PasswordBearer` orqali to'liq kirish tizimi; rol-asosidagi (RBAC) ruxsatlar va resursga egalik tekshiruvi.
- **06-bob (6.1-6.3):** Ilg'or mavzular — `BackgroundTasks` va WebSocket orqali real vaqtli xususiyatlar, `TestClient`/`httpx.AsyncClient` va `dependency_overrides` orqali testlash, `lifespan` va asinxron kodda bloklovchi chaqiruvlardan qochish.
- **07-bob (7.1-7.3):** Production va Deploy — multi-stage Dockerfile va Docker Compose (PostgreSQL bilan), Nginx teskari proksi va ko'p worker jarayoni, GitHub Actions orqali to'liq CI/CD (test → Docker build → deploy) va yakuniy, to'liq real loyiha xulosasi.
- **Jami: 22 dars** (0.1 dan 7.3 gacha), noldan to'liq production-tayyor FastAPI bilimigacha to'liq qamrab olingan.
- Har bir dars bir xil tuzilmaga ega: **Bu darsda nimalarni o'rganasiz** → **Nazariy qism** → **Amaliy misol** → **Keng tarqalgan xatolar** (har biri ❌/✅ va SABAB bilan) → **Mashq/topshiriq** (Oson/O'rtacha/Qiyin, javoblari bilan) → **Qisqacha xulosa**.
- Barcha terminal buyruqlari Ubuntu (`uv`, `apt`, `docker`) uchun moslashtirilgan; darslik siz avval yaratgan **Python darsligi** (sintaksis, OOP, `pytest`), **Django darsligi**, **Docker darsligi** (konteynerlashtirish, Compose, GitHub Actions) va **Git va GitHub darsligi** (SSH, branch workflow, CI/CD, migratsiyalar) bilimlariga izchil tayangan holda, ularni to'liq, zamonaviy FastAPI ekotizimida qanday qo'llashni o'rgatadi.
