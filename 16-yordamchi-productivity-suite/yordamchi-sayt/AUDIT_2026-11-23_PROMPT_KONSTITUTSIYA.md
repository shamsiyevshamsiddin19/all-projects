# YORDAMCHI SAYT — MUHANDISLIK AUDITI

> **Sana:** 2026-yil 23-noyabr
> **Mezon:** `~/Documents/MY_SCILL/prompt/` — 8 ta temir-beton ustun, Hooker 7 tamoyili,
> SOLID, STRIDE, Immutability, Deklarativ agregatsiya, Test piramidasi, DevOps.
> **Qamrov:** `backend_py/` (5 537 qator Python, 26 modul), `assets/js/` (34 844 qator JS, 46 modul),
> `database/schema.sql` (29 jadval), `tests/run.js`, CI workflow'lari, jonli server (`82.70.41.85`).
> **Usul:** statik kod tahlili + jonli server tekshiruvi (systemd, nginx, portlar, HTTP sarlavhalar).

Bu audit **nuqson qidirmaydi** — `AUDIT_REPORT.md` (2026-09-10) allaqachon shuni qilgan.
Bu audit faqat bitta savolga javob beradi: **kod konstitutsiyaga qay darajada bo'ysunadi?**

---

## 1. UMUMIY BAHO

**Kod "Vibe Coding" emas.** Poydevor bor, lekin u **konstitutsiyaning 8 ustunidan 4 tasiga**
tayanadi. Qolgan 4 ustun — testlar, CI, baza cheklovlari va o'zgarmaslik — **deklaratsiya
darajasida qolgan**.

| № | Ustun | Holat | Baho |
|:-:|---|:-:|---|
| 1 | SOLID / Arxitektura | 🟡 | Qatlamlar bor, lekin CQS yo'q; admin tekshiruvi 5 marta ko'chirilgan |
| 2 | Clean Code | 🟢 | Type hints, izohlar namunali — har nuqson sababi hujjatlashgan |
| 3 | Test qamrovi | 🔴 | Backend: **0 ta test** (5 537 qator). Frontend: 575 tasdiq, faqat sof mantiq |
| 4 | Modular Design | 🟡 | Global mutable holat 3 joyda; `vocab.js` 4 620 qator |
| 5 | Security | 🟡 | Auth default-deny, Google token tekshirilgan ✓; CSP yo'q, security log yo'q |
| 6 | Scalability | 🟡 | SQL agregatsiya ishlatilgan ✓; baza cheklovlari **yo'q** |
| 7 | Documentation | 🟢 | Eng kuchli tomoni — "nega shunday" izohlari ko'rgazmali |
| 8 | Monitoring & Logs | 🟡 | Aylanuvchi log fayl ✓; xavfsizlik hodisalari umuman yozilmaydi |

**Xulosa:** bu "axlatxona ustidagi bino" emas, ammo "qoyatoshga qoqilgan qoziq" ham emas —
**zich tuproqqa o'rnatilgan mustahkam plita**. Uni qoyatoshga yetkazish uchun 4 ta ish kerak:
baza cheklovlari, backend testlari, haqiqiy CI, va rate-limit'ni jarayondan tashqariga chiqarish.

---

## 2. KONSTITUTSIYA SELF-AUDIT CHECKLIST (8 mezon)

`ANTI_VIBE_CODING...md` §4 dagi jadval bo'yicha:

| № | Mezon | Natija | Izoh |
|:-:|---|:-:|---|
| 1 | **Arxitektura** (CQS) | ❌ | `services.py` / `selectors.py` **umuman yo'q**. Handler'lar o'qish+yozishni aralashtiradi |
| 2 | **Ma'lumotlar yaxlitligi** | ❌ | **0 ta `CHECK`**, 29 jadvalga faqat 4 FK, 4 tasi ham `CASCADE` (`PROTECT` emas) |
| 3 | **Unumdorlik (SQL)** | ✅ | Agregatsiya SQL'da (18 joyda `SUM/COUNT/GROUP BY`); Python siklida yig'ish yo'q |
| 4 | **Konkyurrensiya** | ❌ | `select_for_update` / `FOR UPDATE` — **0 marta**. `tx()` 9 joyda ishlatilgan ✓ |
| 5 | **Audit va o'zgarmaslik** | ❌ | `activity_log` da **hard DELETE** bor; 0 ta trigger |
| 6 | **Xotira va kesh** | ❌ | Rate-limit, login-limit, `_SEEDED_USERS` — jarayon xotirasida, worker'lar orasida bo'linmagan |
| 7 | **Xavfsizlik jurnali** | ❌ | 6 joyda `403` qaytariladi, **hech biri logga yozilmaydi**; `security` logger yo'q |
| 8 | **Sinovlar** | ❌ | Backend uchun 0 ta test; CI faqat `echo` qiladi |

**8 mezondan 1 tasi bajarilgan.**

---

## 3. AVVAL — NIMA ALLAQACHON TO'G'RI QILINGAN

Buni yozish muhim: quyidagilar konstitutsiya talabidan **past emas, balki undan yuqori**.

1. **`idempotency.py` — namunali konkyurrensiya yechimi.**
   `INSERT ... ON CONFLICT (key) DO NOTHING RETURNING key` — bu atomik band qilish,
   `SELECT`-keyin-`INSERT` poygasi mumkin emas. Xato bo'lsa kalit bo'shatiladi, 120 s
   dan keyin "tiqilib qolgan" kalit egallanadi. Bu kitobdagi to'g'ri yechim.
2. **`init_schema()` da `pg_advisory_xact_lock(727001)`** — 2 worker bir vaqtda DDL
   bajarganda `DeadlockDetected` berardi; advisory lock ularni navbatga qo'yadi.
   Konkyurrensiyani tushunish borligini ko'rsatadi.
3. **Sirlar kodda yo'q.** `config.py` hammasini `.env` dan oladi va prod'da
   `SESSION_SECRET` bo'lmasa **ishga tushmaydi** (`RuntimeError`) — fail-loud.
4. **SQL injection yo'q.** Hamma so'rov SQLAlchemy Core bound-parametrlari bilan.
5. **Auth default-deny.** `PUBLIC_ACTIONS = {"log_client"}` — faqat bittasi ochiq,
   o'qish ham himoyalangan. `ALLOWED_EMAILS` bo'sh bo'lsa **hech kim** kira olmaydi.
6. **Google ID token `aud` bo'yicha tekshiriladi** — mijoz yuborgan emailga ishonilmaydi
   (2026-08-29 da yopilgan haqiqiy teshik).
7. **30 ta indeks, 14 ta UNIQUE** — unumdorlik va takrorlanishdan himoya bor.
8. **Jonli xavfsizlik sarlavhalari:** HSTS, `X-Frame-Options`, `nosniff`,
   `Referrer-Policy`, `Permissions-Policy` — 6 tadan 5 tasi joyida.
9. **Hujjatlashtirish — Hooker 4 tamoyilining ko'rgazmali bajarilishi.**
   Deyarli har nozik joyda "ilgari shunday edi, shu sabab yiqildi, endi shunday"
   izohi bor. Bu auditning o'zini ham tezlashtirdi.

---

## 4. TOPILMALAR

Jami **20 ta**. Har biriga: nima buzilgan, konstitutsiyaning qaysi bandi, **aniq oqibat**, yechim.

### 🔴 KRITIK (4)

---

#### A-01 · CI yolg'on yashil signal beradi

**Joy:** `.github/workflows/quality.yml`
**Buzilgan band:** Ustun 8 (Test coverage), 5-Bosqich (DevOps)

Butun workflow mazmuni:

```yaml
- name: Verify repository structure
  run: |
    echo "Repository integrity check passed successfully."
```

Hech qanday test, linter yoki type-checker ishlamaydi — faqat matn chop etadi va yashil ✓ beradi.

**Oqibat:** bu CI yo'qligidan **yomonroq**. CI yo'q bo'lsa — hech kim ishonmaydi.
CI "passed successfully" deyotgan bo'lsa — buzuq kod tekshirilgan deb o'ylanadi.
Shu repoda esa boshqa loyihalarda **haqiqiy** CI bor: `wstore-tests.yml` da
`ruff check .`, `captionflow.yml` da `mypy`. Ya'ni namuna o'zida bor, bu loyihaga qo'llanmagan.

**Yechim:** `quality.yml` ni haqiqiy ishga aylantirish — `node tests/run.js`,
`ruff check`, `mypy`, va PostgreSQL servisi bilan `pytest`.

---

#### A-02 · Backend 5 537 qator — 0 ta test

**Joy:** butun `backend_py/`
**Buzilgan band:** Ustun 3 — "Kamida 80-90% avtomatlashtirilgan testlar"

```
Python testlari:  0 ta  (database/seeds/rus_tili/test_parser.py — bu parser utiliti, ilova testi emas)
JS testlari:      575 tasdiq (tests/run.js) — lekin faqat sof mantiq:
                  juftlash algoritmi va o'qish intonatsiyasi
```

Test **umuman yo'q** bo'lgan joylar — aynan eng xatarli joylar:
`auth.py` (509 qator), `quiz.py` (563), `users.py` (ruxsatlar), `idempotency.py`,
`security.py` (rate-limit), `owner.py` (kimning ma'lumoti kimga ko'rinadi).

**Oqibat:** `owner.py` dagi `fetch_val` → `fetch_value` typo'si bir necha kun ko'rinmagan
(fayl izohida o'zi yozilgan). Bitta test shuni birinchi daqiqada tutardi. Hozir ham
xuddi shunday nuqson bo'lsa — uni faqat foydalanuvchi ma'lumoti yo'qolganda bilib qolinadi.

**Yechim:** `pytest` + `httpx.ASGITransport` bilan API darajasida test. Birinchi navbatda
`_require_admin` (403 chindan qaytadimi), `idempotency` (takror so'rov ikki marta bajarilmaydimi),
`owner_context` (user admin ma'lumotini ko'rmasligi), `auth` (noto'g'ri token rad etiladimi).

---

#### A-03 · Rate-limit worker'lar orasida bo'linmagan — cheklov 2 baravar yumshoq

**Joy:** `backend_py/app/security.py:38` (`_login_attempts`), `:70` (`_req_hits`), `:71` (`_last_sweep`)
**Buzilgan band:** "Global holat mutlaqo taqiqlanadi. Kesh faqat thread-safe infratuzilma orqali" + STRIDE **D**

```python
_login_attempts: dict[str, deque[float]] = defaultdict(deque)
_req_hits: dict[str, deque[float]] = defaultdict(deque)
_last_sweep = [0.0]
```

Bular jarayon xotirasida. Jonli serverda tasdiqlangan:
`gunicorn ... --workers 2` (`systemctl cat yordamchi-site`).

**Aniq oqibat — raqamlar bilan:**

| Sozlama | Mo'ljallangan | Haqiqiy (2 worker) |
|---|---|---|
| `LOGIN_MAX_ATTEMPTS=8` / 5 daq | 8 urinish | **16 urinish** |
| `RATE_LIMIT_REQUESTS=300` / daq | 300 so'rov | **600 so'rov** |

So'rovlar worker'lar orasida navbat bilan taqsimlanadi, ya'ni har bir worker alohida
hisob yuritadi. Bundan tashqari: **har `systemctl restart` da hisob nolga tushadi** —
ya'ni deploy paytida cheklov butunlay yo'qoladi. Va worker soni 4 ga oshirilsa,
cheklov jimgina 32 urinishga aylanadi — hech qayerda ogohlantirish chiqmaydi.

**Yechim:** hisobni PostgreSQL'ga yoki Redis'ga chiqarish. Baza allaqachon shu serverda —
`idempotency_keys` jadvali bilan bir xil uslubda `login_attempts` jadvali yetarli
(yangi infratuzilma kerak emas). Yoki `--workers 1` + `--threads`.

---

#### A-04 · Schema'da 0 ta `CHECK` constraint

**Joy:** `database/schema.sql` (29 jadval, 18 ta raqamli maydon)
**Buzilgan band:** §5 "Baza sxemasida `CheckConstraint` lar ... majburiy bo'lsin" + checklist 2

```
CHECK constraint:  0
TRIGGER:           0
REFERENCES (FK):   4   ← 29 jadvalga
ON DELETE:         4 × CASCADE   (0 × PROTECT)
UNIQUE:           14   ✓
INDEX:            30   ✓
```

Konstitutsiya bu bandni shartsiz talab qiladi: "Manfiy sonlar taqiqlanadi
(`CheckConstraint(condition=Q(balance__gte=0))`)". Hozir yaxlitlik **faqat Python kodida**
tekshiriladi — ya'ni `psql` orqali, qo'lda migratsiya orqali yoki yangi yozilgan
handler orqali mantiqsiz qiymat kiritish hech narsa bilan to'xtatilmaydi.

**Oqibat:** `sport_exercises` ga manfiy takror soni, `activity_log` ga manfiy
`duration_seconds`, `quiz_progress` ga `is_solved = 7` yozish bazaga qarshilik ko'rsatmaydi.
Keyin `SUM()` hisoboti sababini tushunib bo'lmaydigan son qaytaradi.

**Yechim:** eng muhim 10-15 maydonga `CHECK` qo'shish. Masalan:

```sql
ALTER TABLE activity_log
  ADD CONSTRAINT chk_activity_duration CHECK (duration_seconds IS NULL OR duration_seconds >= 0),
  ADD CONSTRAINT chk_activity_amount   CHECK (amount IS NULL OR amount >= 0);

ALTER TABLE quiz_progress
  ADD CONSTRAINT chk_progress_solved CHECK (is_solved IN (0, 1));
```

`schema.sql` allaqachon idempotent (`IF NOT EXISTS`) uslubda yozilgan, shuning uchun
`DO $$ ... EXCEPTION WHEN duplicate_object THEN NULL; END $$;` bilan xavfsiz qo'shiladi.

---

### 🟠 YUQORI (5)

---

#### A-05 · Audit jadvalida hard DELETE — append-only buzilgan

**Joy:** `backend_py/app/handlers/activity.py:92` (`unlog_activity`)
**Buzilgan band:** §4 Immutability — "audit yozuvlariga `UPDATE` va `DELETE` berish taqiqlanadi" + checklist 5

```python
n = db.execute(
    "DELETE FROM activity_log WHERE owner_type = :ot AND owner_key = :ok "
    "AND section IN ('sport', 'boostday') AND occurred_at >= CURRENT_DATE ..."
)
```

`activity_log` — bu tizimning **tarix daftari**: Tarix lentasi, grafiklar va heatmap
shundan o'qiladi. Hozir u o'chiriladigan jadval.

**Oqibat:** "umuman qilmagan" va "qilgan, keyin belgini olib tashlagan" holatlari
**bir-biridan farqlanmaydi**. Statistika orqaga qarab o'zgaradi — o'tgan hafta
ko'rgan grafik bugun boshqacha bo'lishi mumkin va sababi qayerda ekani yo'qolgan.
Sport bo'limi uchun `section IN ('sport','boostday')` bo'yicha o'chirish esa
Telegram botdan kelgan yozuvni ham o'chiradi.

**Yechim:** o'chirish o'rniga **qarama-qarshi yozuv** (`compensating entry`) qo'shish —
masalan `meta = '{"undo": true}'` yoki `amount = NULL, unit = 'undo'`, va o'qish
so'rovida juftlangan undo'larni SQL darajasida chiqarib tashlash. Shunda tarix
to'liq qoladi, UI esa to'g'ri ko'rsatadi. Keyin DB trigger bilan `DELETE` ni taqiqlash.

---

#### A-06 · `REQUIRE_AUTH` va `AUTH_MODE` — fail-open standart qiymatlar

**Joy:** `backend_py/app/config.py:63`, `:71`
**Buzilgan band:** STRIDE **S** / **E**; konstitutsiya "xavfsizligi kafolatlanmagan kod" taqiqi

```python
REQUIRE_AUTH: bool = _bool("REQUIRE_AUTH", False)
AUTH_MODE: str = (os.getenv("AUTH_MODE", "password").strip().lower() or "password")
```

Izoh ham eskirgan: *"Bu ilova login talab qilmaydi (hamma umumiy fazoda ishlaydi)"* —
sayt 2026-08-29 da Google bilan **qulflangan**.

**Hozir xavf yo'q** — jonli `.env` tasdiqlandi: `REQUIRE_AUTH=true`, `AUTH_MODE=google`.
Bu **yashirin** xavf: `.env` yo'qolsa, bo'sh fayl bilan almashsa yoki yangi serverga
ko'chirilganda unutilsa — `require_write_access()` darhol `return` qiladi va
**butun sayt, o'qish ham yozish ham, hammaga ochiladi**. `AUTH_MODE` esa parol
bilan kirishni qayta yoqadi.

Diqqat qiladigan narsa: **xuddi shu faylda to'g'ri qilingan namuna bor** —
`ALLOWED_EMAILS` bo'sh bo'lsa hech kim kirmaydi va izohda *"sayt ochilib qolgandan
ko'ra yopilib qolgani xavfsizroq"* deb yozilgan. Ya'ni printsip ma'lum, ikki
sozlamaga qo'llanmagan.

**Yechim:** `REQUIRE_AUTH` standartini `True`, `AUTH_MODE` ni `"google"` qilish.
Lokal ishlash uchun `.env` da ataylab `REQUIRE_AUTH=false` yozilsin — himoyani
o'chirish **aniq harakat** bo'lishi kerak, unutish natijasi emas.

---

#### A-07 · `_require_admin` 5 marta ko'chirilgan

**Joy:** `quiz.py:17`, `dictionary.py:16`, `misc.py:28`, `language_topics.py:101`,
`users.py:59` + 6-chi variant `auth.py:350` (`_require_admin_session`)
**Buzilgan band:** Hooker 6 (DRY), SOLID S, ANTI_VIBE "COPY-PASTE CODE"

Beshtasida ham tana aynan bir xil:

```python
if role == "admin" or (email and email in settings.ALLOWED_EMAILS):
    return
raise ApiError("Faqat administrator uchun ruxsat berilgan.", 403)
```

Eng achchiq tomoni: `google_auth.py:109` da **`is_admin_email()` allaqachon mavjud** —
aynan shu ish uchun. Ya'ni to'g'ri abstraksiya yozilgan, keyin 5 marta qo'lda qayta yozilgan.

**Oqibat:** ruxsat mantig'iga har qanday o'zgarish (yangi rol, A-08 dagi xavfsizlik
logi, ALLOWED_EMAILS o'rniga jadval) **6 joyda** bajarilishi kerak. Bittasi
e'tibordan chetda qolsa — STRIDE **E** (Elevation of Privilege): oddiy foydalanuvchi
o'sha endpoint orqali admin amalini bajaradi. Bu nazariy emas: xuddi shu loyihada
2026-09-08 da admin bo'lmagan foydalanuvchi quiz bazalarini o'chira olardi.

**Yechim:** `security.py` ga yagona `require_admin(request)` qo'shib, 6 ta nusxani
unga almashtirish. Xavfsizlik logini (A-08) ham faqat shu bitta joyga yozish kerak bo'ladi.

---

#### A-08 · Xavfsizlik hodisalari umuman yozilmaydi

**Joy:** 403 qaytaradigan 6 joy; `main.py` dagi 401; `security.py` dagi 429
**Buzilgan band:** Ustun 7 + §2.7 STRIDE **R** (Repudiation) + checklist 7

```
Alohida `security` logger:                    0 ta
403/401/429 hodisasini logga yozadigan joy:   0 ta
```

Konstitutsiya aniq talab qiladi: *"Har qanday shubhali urinish ... maxsus xavfsizlik
audit logiga (`wms.security`) vaqt tamg'asi va user ID bilan yoziladi"*. Checklist 7
da esa xato ustun sifatida aynan shu ko'rsatilgan: *"Faqat foydalanuvchiga 403
xatolik qaytarish"* ← hozirgi holat.

**Oqibat:** kimdir admin endpoint'larini sinab ko'rsa, parolni 16 marta xato kiritsa
yoki boshqa odamning idempotency kalitini ochishga urinsa (`idempotency.py` buni
aniqlaydi!) — **hech qanday iz qolmaydi**. Buzilish bo'lganda "nima bo'lganini"
tiklash imkoniyati yo'q. `app.log` da faqat ilova xatolari bor.

**Yechim:** `logging.getLogger("yordamchi.security")` + alohida fayl handler,
va `require_admin` / `require_write_access` / `check_login_rate_limit` ichiga
bitta `logger.warning("UNAUTHORIZED_ADMIN", extra={...})` — email, IP, action, vaqt bilan.
A-07 tuzatilgandan keyin bu **3 qator kod**.

---

#### A-09 · `quiz.set_flag` — poyga holati, "yechilgan" belgisi yo'qoladi

**Joy:** `backend_py/app/handlers/quiz.py:256-277`
**Buzilgan band:** §3.8 Konkyurrensiya + checklist 4. Butun kod bazasida `FOR UPDATE` — **0 marta**

```python
existing = db.fetch_one("SELECT id, is_solved FROM quiz_progress WHERE ...")   # (1) O'QISH

if flag_type == "" or flag_type == "none":
    if existing:
        if int(existing["is_solved"]) == 1:
            db.execute("UPDATE quiz_progress SET flag_type = '' WHERE id = :id")  # (2a)
        else:
            db.execute("DELETE FROM quiz_progress WHERE id = :id")                # (2b) YOZISH
```

`fetch_one` va `execute` — **ikki alohida ulanish, ikki alohida tranzaksiya**.
(1) va (2) orasida boshqa so'rov o'tishi mumkin.

**Aniq ssenariy:**

| Vaqt | So'rov A (`set_flag` → "none") | So'rov B (`mark_solved`) |
|---|---|---|
| t1 | `SELECT` → `is_solved = 0` | |
| t2 | | `INSERT ... ON CONFLICT DO UPDATE SET is_solved = 1` ✓ |
| t3 | `is_solved == 0` deb **DELETE** | |

Natija: foydalanuvchi savolni yechdi, server tasdiqladi, keyin yozuv **butunlay yo'qoldi**.
Bu real holat — ilovada belgi qo'yish va yechish ketma-ket, tez bosiladi va
`core.js` dagi oflayn navbat so'rovlarni to'plab birga yuboradi.

**Yechim:** bitta `tx()` ichiga olib, `SELECT ... FOR UPDATE` qo'shish. Yoki
deklarativ qilish — o'qishni butunlay olib tashlab, bitta `UPDATE`:

```sql
UPDATE quiz_progress SET flag_type = '' WHERE ... AND is_solved = 1;
DELETE FROM quiz_progress WHERE ... AND is_solved = 0;
```

`db.tx()` konteksti allaqachon yozilgan va 9 joyda ishlatilgan — vosita bor, bu yerda qo'llanmagan.

---

### 🟡 O'RTA (7)

#### A-10 · `goals.toggle_goal` — o'qi-o'zgartir-yoz

`goals.py:248-265`. `SELECT completed` → `yangi = 0 if completed == 1 else 1` → `UPDATE`.
Ikki parallel bosishda oxirgi holat tasodifiy (lost update). Bundan tashqari `UPDATE`
`id` emas, **matn bo'yicha** qatorlarni yangilaydi — ya'ni bir nechta qator o'zgaradi
va ularning boshlang'ich holati har xil bo'lishi mumkin.
**Yechim:** o'qishni olib tashlash — `SET completed = 1 - completed` bitta so'rovda.

#### A-11 · CQS yo'q — `services.py` / `selectors.py` umuman mavjud emas

Konstitutsiyaning 1-bandi va checklist 1-qatori. Hozirgi qatlamlar:
`main.py` (HTTP) → `handlers/*.py` (o'qish + yozish + validatsiya + biznes mantiq aralash) → `db.py`.
`quiz.py` ning 563 qatorida `get_data` (o'qish) va `upload_base` (yozish, tranzaksiyali)
bir faylda yonma-yon turadi.
**Baho:** bu eng og'ir topilma emas — 4 qatlamdan 3 tasi bor va `db.py` toza ajratilgan.
Ammo `select_for_update` va `tx()` ni izchil qo'llash uchun yozish amallarini bir
joyga yig'ish kerak bo'ladi, shuning uchun A-09/A-10 bilan birga hal qilinadi.

#### A-12 · Dispatch jadvali har so'rovda qaytadan quriladi

`main.py:106` — `_dispatch_query_action()` **ichida** 100 ta kalitli lug'at va
100 ta `lambda` yaratiladi, keyin ulardan bittasi chaqiriladi. Qolgan 99 tasi darhol tashlanadi.
Har API so'rovida. 946 MB RAM'li serverda bu bekorga sarflangan ish.
**Yechim:** jadvalni modul darajasiga chiqarish — `lambda` lar o'rniga
`(handler, arg_spec)` juftligi bilan. Bir martalik ish bo'ladi.

#### A-13 · 29 jadval, faqat 4 FK — aloqalar satr bo'yicha

`owner_key` (email satri) orqali bog'lanish — baza darajasida hech qanday kafolat yo'q.
Foydalanuvchi o'chirilsa yoki email o'zgarsa, uning `app_storage`, `goals`,
`activity_log`, `quiz_progress` yozuvlari **yetim qoladi** va hech qachon tozalanmaydi.
Mavjud 4 FK ning hammasi `CASCADE` — konstitutsiya `PROTECT` ni talab qiladi
(§1-Bosqich: "Xavfli o'chirishlarni bartaraf eting").
**Baho:** `CASCADE` bu yerda ataylab bo'lishi mumkin (ota o'chsa bola kerak emas) —
lekin qaror hech qayerda yozilmagan. Kamida izoh, yaxshisi `PROTECT`.

#### A-14 · Linter, type-checker, Docker yo'q

```
pyproject.toml / setup.cfg:  YO'Q
ruff / mypy konfiguratsiyasi: YO'Q
Dockerfile / docker-compose:  YO'Q
.env.example:                 BOR ✓
```

5-Bosqich talablaridan 1 tasi bajarilgan. Yana bir marta: shu repoda
`wstore-tests.yml` da `ruff`, `captionflow.yml` da `mypy --strict` ishlaydi —
namuna bor, bu loyihaga qo'llanmagan. Docker yo'qligi esa serverni qayta
qurish kerak bo'lganda qo'lda sozlashni talab qiladi (Portability, ISO 25010 §8).

#### A-15 · CSP sarlavhasi yo'q; 358 ta `innerHTML`

Jonli sarlavhalar tekshirildi — 6 tadan 5 tasi bor, **faqat
`Content-Security-Policy` yo'q**. Frontend'da 358 joyda `innerHTML` ishlatiladi;
himoya `esc()` bilan qo'lda qilinadi (513 chaqiruv — intizom yaxshi).
Ammo 358 joydan bittasida `esc()` tushib qolsa — stored XSS yo'li ochiladi,
va sayt endi ko'p foydalanuvchili (admin kontenti user brauzerida render bo'ladi).
CSP — aynan shu bitta xatoni zararsizlantiradigan ikkinchi qatlam.
**Yechim:** `25-radioglobe-world-streaming/infra/nginx.conf:43` da tayyor CSP bor —
shu qatorni moslashtirib `yordamchi.conf` ga qo'yish. HSTS ga `includeSubDomains` ham qo'shilsa yaxshi.

#### A-16 · `_SEEDED_USERS` — global mutable, xatodan keyin qayta urinmaydi

`owner.py:16` — modul darajasidagi `set()`. Ikki muammo:
(1) konstitutsiya global mutable holatni taqiqlaydi, worker'lar orasida bo'linmaydi;
(2) **mantiqiy xato:** `_SEEDED_USERS.add(email)` `try` blokidan **oldin** turadi,
shuning uchun ko'chirish vaqtincha xato bersa (baza band edi) email "bajarilgan"
deb belgilanadi va **o'sha worker umrida qayta urinmaydi**. Fayl izohida aynan
shu funksiyaning oldingi nuqsoni haqida uzun ogohlantirish bor — xato shakli o'zgargan, o'zi qolgan.
**Yechim:** `add()` ni muvaffaqiyatdan keyinga ko'chirish; holatni bazada belgilash.

---

### 🔵 PAST (4)

| ID | Topilma | Joy |
|---|---|---|
| **A-17** | `vocab.js` **4 620 qator** (`home.js` 2 695, `kun.js` 2 320) — SRP / "Modular Design" buzilgan | `assets/js/app2/` |
| **A-18** | `except Exception: return {}` — noto'g'ri JSON jimgina bo'sh tanaga aylanadi, mijoz 400 emas, boshqa xato oladi | `main.py:95,103` |
| **A-19** | `@app.on_event("startup")` eskirgan (FastAPI `lifespan` tavsiya qiladi) | `main.py:69` |
| **A-20** | `ALLOWED_SECTIONS` **4 joyda** takrorlanadi (fayl izohi buni o'zi tan oladi va ogohlantiradi) | `activity.py:19-30` |

---

## 5. TUZATISH REJASI

Tartib **xatar × mehnat** bo'yicha, konstitutsiyaning 5 bosqichiga moslangan.

### 1-to'lqin — poydevor (1-2 kun, eng katta foyda)

| № | Ish | Nega birinchi | Holat |
|:-:|---|---|:-:|
| 1 | **A-07** → `security.py` ga yagona `require_admin()`, 6 nusxani almashtirish | A-08 ni 3 qatorga aylantiradi | ✅ Bajarildi (`05bf77f`) |
| 2 | **A-08** → `yordamchi.security` logger + har rad etishni yozish | Buzilishni ko'rish imkoniyati paydo bo'ladi | ✅ Bajarildi (`05bf77f`) |
| 3 | **A-06** → `REQUIRE_AUTH=True`, `AUTH_MODE="google"` standart | Bir qatorlik o'zgarish, yashirin xavfni yopadi | ✅ Bajarildi (`df26848`) |
| 4 | **A-15** → `yordamchi.conf` ga CSP (RadioGlobe'dan ko'chirib) | 358 `innerHTML` uchun ikkinchi himoya qatlami | ⏸ Server qaytishini kutmoqda |
| 5 | **A-01** → `quality.yml` ni haqiqiy qilish (`node tests/run.js` dan boshlab) | Yolg'on signal to'xtaydi | ✅ Bajarildi (`ee2e06c`) |

### 2-to'lqin — yaxlitlik (2-3 kun)

| № | Ish | Holat |
|:-:|---|:-:|
| 6 | **A-04** → eng muhim 10-15 maydonga `CHECK` (`activity_log`, `quiz_progress`, `sport_exercises`) | ✅ Bajarildi (`a77b630`) |
| 7 | **A-09** → `set_flag` ni `tx()` + `FOR UPDATE` ga o'tkazish (ma'lumot yo'qolishi to'xtaydi) | ✅ Bajarildi (`b5b2ac9`) |
| 8 | **A-10** → `toggle_goal` ni deklarativ bitta `UPDATE` ga aylantirish | ✅ Bajarildi (`f27ee90`) |
| 9 | **A-05** → `unlog_activity` ni DELETE'dan compensating-entry'ga o'tkazish | ✅ Bajarildi (`171c89b`) |
| 10 | **A-03** → login/request hisobini bazaga chiqarish (`idempotency_keys` uslubida) | ✅ Bajarildi (`e1d864d`) |

### 2-to'lqin ijrosi hisoboti (2026-11-24):
- **A-01:** CI workflow (`quality.yml`) haqiqiy qilindi — push va PR da `paths:` filtri bilan frontend (Node.js 635 test) va backend (Python 3.12 50 test) avtomatlashtirildi.
- **A-04:** `schema.sql` ga 12 ta idempotent CHECK cheklovi qo'shildi; `db.py:_split_statements` dollar-quote bloklarini (`$$...$$`) butun saqlaydigan qilib kengaytirildi va testlandi.
- **A-09:** `quiz.py:set_flag` poyga holati yo'qotildi: dastlabki `SELECT` olib tashlandi, shart to'liq SQL darajasida va bitta `db.tx()` tranzaksiyasida atomik bajariladigan qilindi.
- **A-10:** `goals.py:toggle_goal` poygasi yo'qotildi: o'qish va yozish bitta CTE so'roviga birlashtirilib, `FOR UPDATE` bilan qulflandi; bir xil nomli maqsadlar birga yangilanishi saqlandi.
- **A-05:** `activity_log` to'liq append-only audit daftariga aylantirildi. Hard DELETE o'rniga `unit='undo'` compensating yozuv kiritiladi; `get_activity_log` va `sport._today_boost_done` juftlangan undo'larni SQL darajasida chiqarib tashlaydi; `schema.sql` ga DELETE ni taqiqlovchi trigger yozildi.
- **A-03:** `security.py` dagi global mutable xotira (`_login_attempts`, `_req_hits`) PostgreSQL dagi `rate_limit_hits` jadvaliga chiqarildi; workerlar soni va restartlar cheklovga ta'sir qilmaydi.
- Jami backend testlari **28 tadan 50 taga** yetkazildi, barcha testlar (50 backend + 635 frontend) 100% yashil.

### 3-to'lqin — intizom (davomiy)

| № | Ish |
|:-:|---|
| 11 | **A-02** → `pytest` + `httpx.ASGITransport`; birinchi 20 test: auth, ruxsat, idempotency, owner izolyatsiyasi |
| 12 | **A-14** → `pyproject.toml` + `ruff` + `mypy`, CI'ga ulash |
| 13 | **A-12** → dispatch jadvalini modul darajasiga chiqarish |
| 14 | **A-16, A-18, A-19, A-20** → kichik tozalashlar |
| 15 | **A-11** → yozish amallarini `services.py` ga, o'qishni `selectors.py` ga (eng katta ish, oxirida) |

---

## 6. QISQA XULOSA

Konstitutsiya "Vibe Coding" ni *"tashqi ko'rinishi yaltiroq, poydevori chirigan"* deb ta'riflaydi.
Bu loyiha unga **to'g'ri kelmaydi** — poydevorda chuqur o'ylangan yechimlar bor
(idempotency, advisory lock, default-deny auth, token tekshiruvi, SQL parametrlari),
va hujjatlashtirish darajasi konstitutsiya talabidan yuqori.

Asosiy farq boshqa joyda: **himoya kodda bor, baza va avtomatizatsiyada yo'q.**
Yaxlitlik Python'da tekshiriladi — bazada emas. Testlar frontend'da bor — backend'da yo'q.
CI mavjud — lekin hech narsa qilmaydi. Rate-limit yozilgan — lekin ikki worker'da ikkiga bo'linadi.

Konstitutsiya tili bilan: bino mustahkam qurilgan, lekin **qoziqlar qoyatoshga yetmagan** —
ular zich tuproqda to'xtagan. 1- va 2-to'lqin (jami ~4 kun) ularni qoyatoshga yetkazadi.

---
*Audit: Claude Code · Mezon: `~/Documents/MY_SCILL/prompt/`*
*Statik tahlil + jonli server tekshiruvi (`82.70.41.85`, 2026-11-23)*
