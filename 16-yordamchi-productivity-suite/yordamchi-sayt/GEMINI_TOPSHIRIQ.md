# TOPSHIRIQ: Yordamchi sayt — audit tuzatishlari (2-to'lqin)

> Bu fayl boshqa AI agentga (Gemini) beriladigan to'liq topshiriq.
> Agent hech qanday oldingi kontekstsiz boshlaydi — kerakli hamma narsa shu yerda.

---

## 0. SENING ROLING

Sen — Bosh Tizim Arxitektori va Yetakchi Muhandissan (Principal Software Architect
& Lead Systems Engineer). Ishlab turgan **jonli** loyihani tuzatasan.

Majburiy mezon: `~/Documents/MY_SCILL/prompt/` papkasidagi konstitutsiya.
**Ishni boshlashdan oldin uchala faylni o'qi:**
- `SYSTEM_PROMPT.txt`
- `ANTI_VIBE_CODING_SOFTWARE_ENGINEERING_PROMPT.md`
- `MASTER_SOFTWARE_ENGINEERING_AND_PARADIGMS_PROMPT.md`

Qisqacha: CQS qatlamlari, SOLID, baza darajasidagi cheklovlar, append-only audit,
`FOR UPDATE` bilan poyga himoyasi, STRIDE, test piramidasi. "Works somehow",
`except: pass`, `# TODO: later`, global mutable, hardcoded konstanta — taqiqlanadi.

---

## 1. LOYIHA

| | |
|---|---|
| Yo'l | `~/Documents/project/loyihalar/16-yordamchi-productivity-suite/yordamchi-sayt` |
| Git | `all-projects` repo, ildiz `~/Documents/project/loyihalar`, branch `main` |
| Backend | FastAPI + SQLAlchemy Core + PostgreSQL 16 — `backend_py/app/` (5 537 qator, 26 modul) |
| Frontend | Vanilla JS SPA, 44 modul, 34 844 qator — `assets/js/app2/` (**tegilmaydi**) |
| Baza | 29 jadval — `database/schema.sql` |
| API | Yagona kirish: `/api?action=...` → `main.py` dagi dispatch jadvali (80 action) |
| Jonli | https://y.wstore.uz — server `yordamchi`, `82.70.41.85`, `ssh yordamchi` |

**To'liq audit hisoboti:** `AUDIT_2026-11-23_PROMPT_KONSTITUTSIYA.md` (shu papkada).
Unda 20 topilma bor, har biriga sabab, oqibat va yechim yozilgan. **Avval shuni o'qi.**

---

## 2. ⚠️ HOZIRGI HOLAT — SERVER O'CHGAN

2026-11-23 dan beri `82.70.41.85` javob bermayapti (ping 100% loss, SSH banner yo'q,
sayt timeout). Boshqa serverlar (`shamsiyev.uz`, `wstore.uz`) ishlayapti — demak
muammo o'sha serverda, tarmoqda emas. Tiklash uchun Oracle Cloud konsoli kerak
(akkaunt 21@, Stockholm) — bu **foydalanuvchining ishi**, sening emas.

**Shuning uchun:**
- ✅ **Bajarish mumkin:** lokal kod o'zgarishlari, testlar, migratsiya SQL yozish, CI
- ❌ **Server qaytguncha BLOKLANGAN:** nginx CSP (A-15), deploy, jonli tekshiruv,
  migratsiyani bazaga qo'llash

Serverga tegadigan bandlarni **yozib qo'y, lekin qo'llama**. Har safar ishlash
oldidan holatni tekshir:
```bash
curl -sS -o /dev/null -w "%{http_code}\n" --max-time 10 https://y.wstore.uz
```

---

## 3. ALLAQACHON BAJARILGAN (takrorlama)

Commit `05bf77f` va `df26848` — GitHub'da:

1. **A-07** — `_require_admin` beshta handlerda ko'chirilgan edi. Endi yagona manba:
   `security.is_admin()` / `security.require_admin()`. 24 chaqiruv yo'naltirilgan.
2. **A-08** — xavfsizlik jurnali: `yordamchi.security` logeri, `security.log` fayli.
   Har 403/401/429 yoziladi (IP, email, rol, action). `client_ip()` nginx ortidagi
   haqiqiy IP ni oladi.
3. **A-06** — fail-closed standartlar: `REQUIRE_AUTH=True`, `AUTH_MODE="google"`.
4. **Birinchi testlar** — `backend_py/tests/`, **28 ta test**, bazasiz ishlaydi.
   Ichida arxitektura testi bor: handler o'ziga admin tekshiruvini qayta yozsa,
   test yiqiladi.

---

## 4. SENING VAZIFALARING

Tartib bilan bajar. **Har bandni tugatganda: test → commit → push.** To'plab qo'yma.

### ✅ VAZIFA 1 — A-01: CI workflow'ini haqiqiy qilish

**Fayl:** `~/Documents/project/loyihalar/.github/workflows/quality.yml`

Hozirgi mazmuni yolg'on yashil signal beradi:
```yaml
- name: Verify repository structure
  run: echo "Repository integrity check passed successfully."
```
Hech qanday test yoki linter ishlamaydi, lekin ✓ beradi. Bu CI yo'qligidan yomonroq.

**Qil:** shu workflow'ga yordamchi-sayt uchun haqiqiy ish qo'sh:
- `node tests/run.js` (frontend, 575 tasdiq)
- `pytest` (backend, 28 test) — `backend_py/requirements.txt` + `pytest` o'rnatib
- Ishlaydigan `paths:` filtri qo'y, boshqa loyihalarga tegma

**Namuna shu repoda bor:** `.github/workflows/wstore-tests.yml` (ruff),
`captionflow.yml` (mypy). O'shalarga qarab yoz.

**Mezon:** workflow push'da ishlaydi; testni ataylab buzsang — CI qizil bo'ladi.

---

### ✅ VAZIFA 2 — A-04: Baza cheklovlari (`CHECK`)

**Fayl:** `database/schema.sql`

Hozir: **0 ta `CHECK`**, 0 ta trigger, 29 jadvalga faqat 4 ta FK (hammasi `CASCADE`).
Yaxlitlik faqat Python kodida tekshiriladi — ya'ni qo'lda SQL yoki yangi handler
mantiqsiz qiymat yozsa, baza qarshilik ko'rsatmaydi.

**Qil:** eng muhim maydonlarga `CHECK` qo'sh. Kamida:
```sql
-- activity_log
duration_seconds IS NULL OR duration_seconds >= 0
amount IS NULL OR amount >= 0
-- quiz_progress
is_solved IN (0, 1)
-- sport_exercises, goals, dictionary_* — raqamli maydonlarni ko'rib chiq
```

**MUHIM — qanday yozish kerak:**
- `schema.sql` har ishga tushishda qayta bajariladi (`init_schema`), shuning uchun
  **idempotent** bo'lishi shart. `ADD CONSTRAINT` ikkinchi marta xato beradi.
  Shuning uchun shunday o'ra:
  ```sql
  DO $$ BEGIN
      ALTER TABLE activity_log ADD CONSTRAINT chk_activity_duration
          CHECK (duration_seconds IS NULL OR duration_seconds >= 0);
  EXCEPTION WHEN duplicate_object THEN NULL; END $$;
  ```
- `db.py:_split_statements()` faylni `;` bo'yicha bo'ladi — `DO $$ ... $$;` bloki
  ichida `;` bor! **Avval `_split_statements` ni tekshir**, kerak bo'lsa `$$` bloklarini
  butun saqlaydigan qilib tuzat va buni testga ol.
- **Mavjud ma'lumot cheklovni buzayotgan bo'lishi mumkin** — server qaytganda avval
  `SELECT` bilan tekshirish kerak. Hozir faqat SQL yoz, qo'llama.

**Mezon:** `_split_statements` uchun test; SQL sintaksisi to'g'ri; izohda nega
bu cheklov kerakligi yozilgan.

---

### ✅ VAZIFA 3 — A-09: `quiz.set_flag` poyga holati (ma'lumot yo'qoladi)

**Fayl:** `backend_py/app/handlers/quiz.py`, `set_flag()` funksiyasi

Hozirgi kod `SELECT` qiladi, keyin alohida `DELETE`/`UPDATE` — **ikki alohida
ulanish, ikki alohida tranzaksiya**:
```python
existing = db.fetch_one("SELECT id, is_solved FROM quiz_progress WHERE ...")
if flag_type in ("", "none"):
    if existing:
        if int(existing["is_solved"]) == 1:
            db.execute("UPDATE quiz_progress SET flag_type = '' WHERE id = :id")
        else:
            db.execute("DELETE FROM quiz_progress WHERE id = :id")
```

**Poyga ssenariysi:**
| Vaqt | `set_flag` ("none") | `mark_solved` |
|---|---|---|
| t1 | `SELECT` → `is_solved = 0` | |
| t2 | | `is_solved = 1` qiladi ✓ |
| t3 | eski o'qishga ishonib **DELETE** | |

Natija: foydalanuvchi savolni yechdi, server tasdiqladi, **yozuv yo'qoldi**.
Bu real — belgi qo'yish va yechish tez ketma-ket bosiladi va `core.js` dagi
oflayn navbat so'rovlarni to'plab birga yuboradi.

**Qil — ikki yo'ldan birini tanla:**
1. **Deklarativ (afzal):** o'qishni butunlay olib tashla, shartni SQL'ga ko'chir:
   ```sql
   UPDATE quiz_progress SET flag_type = '' WHERE ... AND is_solved = 1;
   DELETE FROM quiz_progress WHERE ... AND is_solved = 0;
   ```
2. **Qulflash:** `with db.tx() as conn:` ichiga ol va `SELECT ... FOR UPDATE` qo'sh.

`db.tx()` konteksti allaqachon yozilgan va 9 joyda ishlatilgan (`db.py`) —
yangi vosita yasama.

**Mezon:** `FOR UPDATE` yoki bitta atomik so'rov; poyga ssenariysini ko'rsatadigan
test (ikki ketma-ket chaqiruv, natija to'g'ri qolishi).

---

### ✅ VAZIFA 4 — A-10: `goals.toggle_goal` o'qi-o'zgartir-yoz

**Fayl:** `backend_py/app/handlers/goals.py`, `toggle_goal()`

`SELECT completed` → `yangi = 0 if completed == 1 else 1` → `UPDATE`.
Ikki parallel bosishda oxirgi holat tasodifiy.

**Qil:** o'qishni olib tashla — bitta so'rov yetarli:
```sql
UPDATE goals SET completed = 1 - completed, ... WHERE ...
```
**Diqqat:** hozirgi `UPDATE` `id` emas, **matn bo'yicha** bir nechta qatorni
yangilaydi (bu ataylab — bir xil nomli maqsad turli jildlarda birga o'zgaradi).
Bu xatti-harakatni **buzma**, faqat poygani yo'qot. Agar `1 - completed` bir
nechta qatorda turli natija bersa — avvalgi mantiq qanday ishlaganini aniqlab,
testga ol.

**Mezon:** o'qish-yozish ajralmasligi; mavjud "bir xil nomlilar birga o'zgaradi"
xatti-harakati saqlanishi; test.

---

### ✅ VAZIFA 5 — A-05: `activity_log` append-only bo'lishi

**Fayl:** `backend_py/app/handlers/activity.py`, `unlog_activity()`

Hozir audit jadvalidan **hard DELETE** qiladi. Konstitutsiya §4 buni taqiqlaydi:
audit yozuviga `UPDATE`/`DELETE` berilmaydi.

Oqibat: "umuman qilmagan" va "qilgan, keyin belgini olib tashlagan" farqlanmaydi.
Tarix/grafik/heatmap orqaga qarab o'zgaradi va sababi yo'qoladi.

**Qil:**
1. O'chirish o'rniga **qarama-qarshi yozuv** (compensating entry) qo'sh —
   masalan `meta` ichida `{"undo": true}` yoki `unit = 'undo'`.
2. O'qish so'rovida (`get_activity_log` va sport "bugun bajarilganmi" mantig'i)
   juftlangan undo'larni **SQL darajasida** chiqarib tashla — Python siklida emas.
3. Keyin (server qaytganda) `activity_log` ga `DELETE` ni taqiqlaydigan trigger yoz.

**Diqqat:** `sport` bo'limi uchun hozirgi o'chirish `section IN ('sport','boostday')`
bo'yicha ishlaydi va vaqt prefiksini `regexp_replace` bilan tozalaydi — bu mantiq
Telegram botdan kelgan yozuvni ham qamraydi. Yangi yechimda **shu qamrov saqlanishi**
kerak, aks holda sport belgisi olinmay qoladi.

**Mezon:** hech qanday `DELETE FROM activity_log` qolmasligi; tarix to'liq qolishi;
UI xatti-harakati o'zgarmasligi; test.

---

### ✅ VAZIFA 6 — A-03: Rate-limit'ni jarayondan tashqariga chiqarish

**Fayl:** `backend_py/app/security.py` — `_login_attempts`, `_req_hits`, `_last_sweep`

Bular jarayon xotirasida. Server `gunicorn --workers 2` bilan ishlaydi, ya'ni
har worker alohida hisob yuritadi:

| Sozlama | Mo'ljal | Haqiqiy |
|---|---|---|
| `LOGIN_MAX_ATTEMPTS=8` | 8 urinish | **16** |
| `RATE_LIMIT_REQUESTS=300` | 300 so'rov | **600** |

Va har `systemctl restart` da hisob nolga tushadi. Worker 4 ga oshsa — jimgina 32 bo'ladi.
Konstitutsiya global mutable holatni taqiqlaydi, kesh thread-safe infratuzilmada bo'lishi shart.

**Qil:** hisobni PostgreSQL'ga chiqar. **Yangi infratuzilma (Redis) qo'shma** —
946 MB RAM'li serverda o'rinsiz. Namuna shu loyihada bor: `idempotency.py`
`INSERT ... ON CONFLICT DO NOTHING RETURNING` bilan atomik ishlaydi — **o'sha
uslubda** `login_attempts` / `request_hits` jadvali yoz.

**Diqqat:** bu har so'rovda baza yozuvi degani. Unumdorlikni o'yla: eski yozuvlarni
tozalash (`idempotency.cleanup()` kabi tasodifiy ehtimol bilan), indeks, va
`RATE_LIMIT_REQUESTS=0` bilan butunlay o'chirish yo'li saqlanishi.

**Mezon:** worker soni natijaga ta'sir qilmasligi; restartda hisob saqlanishi; test.

---

## 5. ISHLASH TARTIBI

### Muhitni tayyorlash
```bash
cd ~/Documents/project/loyihalar/16-yordamchi-productivity-suite/yordamchi-sayt/backend_py
python3 -m venv .venv                       # agar yo'q bo'lsa
.venv/bin/pip install -r requirements.txt pytest
.venv/bin/python -m pytest tests/ -q        # 28 test o'tishi kerak
```

### Har o'zgarishdan keyin
```bash
.venv/bin/python -m pytest tests/ -q        # backend
node ../tests/run.js                        # frontend (tegmagan bo'lsang ham)
```

### Commit qoidalari — QAT'IY
- ❌ **HECH QACHON** `Co-authored-by: ...` yoki boshqa AI atribut qo'shma.
  Barcha commitlar faqat Shamsiddin Shamsiyev nomidan.
- Har band tugaganda **alohida commit + push**. Oxirida to'plab qo'yma.
- Commit xabari o'zbekcha, `fix(yordamchi/...)` yoki `feat(...)` ko'rinishida,
  tanasida **nega** kerakligi va **oqibati** yozilsin.
- Faqat o'z fayllaringni `git add` qil — repoda boshqa loyihalarning
  o'zgargan fayllari bor, ularga tegma.

---

## 6. TUZOQLAR — bilmasang vaqt yo'qotasan

1. **`.py` o'zgarsa deploy yetmaydi.** `deploy.sh` faqat fayl yuklaydi;
   gunicorn eski kodni xotirada ushlaydi. Shart:
   `ssh yordamchi 'sudo systemctl restart yordamchi-site'`
   (servis nomi `yordamchi-site`, `yordamchi` emas).
2. **`.js`/`.css` o'zgarsa** `index.html` dagi `?v=` va `service-worker.js` dagi
   `VERSION` ham yangilanadi — nginx statikani `immutable` bilan beradi.
3. **`scp` yirtiq fayl qoldiradi.** Joyida qayta yozma:
   `scp x.js srv:.../x.js.tmp && ssh srv 'mv -f .../x.js.tmp .../x.js'`
4. **`db.fetch_one` yozuvni commit QILMAYDI** — `INSERT ... RETURNING` uchun
   `db.execute_returning()` ishlat. Bu bir marta idempotency'ni butunlay
   ishlamay qoldirgan.
5. **Har restartda `DeadlockDetected` logda ko'rinadi** — bu eski, zararsiz
   (worker'lar bir vaqtda schema init qiladi). Yangi xato deb o'ylama.
6. **Bu serverda `dnf` ishlatma** — 1 GB RAM'da SSH ni o'ldiradi.

---

## 7. QILMA

- ❌ Loyihani noldan qayta yozma. Frontendni React'ga ko'chirma.
  Bu qaror ko'rib chiqilgan va **rad etilgan** (58 ekran, 6-11 oy, foyda yo'q).
- ❌ `assets/js/` ga tegma — bu to'lqin faqat backend va baza haqida.
- ❌ Yangi infratuzilma (Redis, Docker, message queue) qo'shma.
- ❌ API shartnomasini (`/api?action=...`) o'zgartirma — frontend unga bog'langan.
- ❌ Serverda hech narsani o'zgartirma, u hozir o'chgan; qaytganda ham
  deploy qilishdan oldin foydalanuvchidan so'ra.
- ❌ Testsiz commit qilma. Har tuzatishga uni qulflaydigan test yoz.

---

## 8. TUGAGANDA

`AUDIT_2026-11-23_PROMPT_KONSTITUTSIYA.md` faylidagi tuzatish rejasiga
bajarilgan bandlarni belgilab qo'y va qisqa hisobot yoz: nima qilinding,
qaysi test qo'shilding, nima qolganini.

Qolgan (3-to'lqin, bu topshiriqqa KIRMAYDI): A-02 (test qamrovini kengaytirish),
A-11 (CQS — services/selectors), A-12 (dispatch jadvali), A-14 (ruff/mypy/Docker),
A-13, A-16..A-20.
