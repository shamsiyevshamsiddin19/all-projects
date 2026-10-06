# -*- coding: utf-8 -*-
"""
PostgreSQL to'liq darsligining barcha 36 ta darsini va mundarijasini professional darajada yaratuvchi generator.
"""
import os
import sys

BASE_DIR = os.getenv('POSTGRES_BASE_DIR', '/home/shamsiddin/Documents/shamsiyev/Dasturlash/PostgreSQL-Darslik')

CHAPTERS = [
    {
        "dir": "00-bob-kirish-ornatish",
        "title": "00. Kirish va O'rnatish",
        "lessons": [
            {
                "fn": "0.1-postgresql-nima-tarixi-arxitekturasi.md",
                "name": "0.1. PostgreSQL nima, tarixi va arxitekturasi",
                "content": """# 0.1. PostgreSQL nima, tarixi va arxitekturasi

## Bu darsda nimalarni o'rganasiz
- PostgreSQL (Postgres) nima va u qanday yaratilgan
- Relyatsion ma'lumotlar bazasi (RDBMS) tushunchasi
- PostgreSQL arxitekturasi: Client-Server modeli, jarayonlar va xotira
- Nega zamonaviy loyihalarda (Django, FastAPI, Node.js) PostgreSQL tanlanadi

## Nazariy qism

### PostgreSQL nima?
**PostgreSQL** (ko'pincha shunchaki **Postgres**) — dunyodagi eng ilg'or, ochiq kodli (open-source) obyekt-relyatsion ma'lumotlar bazasini boshqarish tizimi (ORDBMS). U 1986-yilda Berkli universitetida (UC Berkeley) Michael Stonebraker boshchiligida POSTGRES loyihasi sifatida boshlangan.

PostgreSQL quyidagi asosiy xususiyatlari bilan ajralib turadi:
1. **ACID xususiyatlariga 100% moslik:** Ma'lumotlarning ishonchliligi va yaxlitligini kafolatlaydi.
2. **Kengaytiriluvchanlik (Extensibility):** O'z ma'lumot turlaringizni, funksiyalaringizni va indekslaringizni yaratishingiz mumkin.
3. **Boy ma'lumot turlari:** Matn, son, sana bilan bir qatorda `JSON/JSONB`, Geografik ma'lumotlar (`PostGIS`), massivlar (`ARRAY`), UUID va IP manzillarni qo'llab-quvvatlaydi.
4. **Kuchli hamjamiyat va litsenziya:** PostgreSQL litsenziyasi bo'yicha u mutlaqo bepul va tijoriy loyihalarda hech qanday to'lovlarsiz ishlatiladi.

### PostgreSQL arxitekturasi
PostgreSQL **Client-Server** arxitekturasida ishlaydi:
- **Server (Postmaster / postgres jarayoni):** Baza fayllarini boshqaradi, mijozlar (client) ulanishlarini qabul qiladi va har bir yangi ulanish uchun alohida server jarayonini (`backend process`) ishga tushiradi.
- **Client:** Baza bilan bog'lanuvchi dasturlar — masalan, `psql` konsol utilitasi, pgAdmin, Python (psycopg2/asyncpg), Django ORM va h.k.
- **Shared Memory:** Barcha jarayonlar uchun umumiy kesh xotirasi (`shared_buffers`, `WAL buffers`).
- **WAL (Write-Ahead Logging):** Barcha o'zgarishlar avval diskdagi jurnalga yoziladi, bu esa server to'satdan o'chib qolganda ma'lumotlarning tiklanishini ta'minlaydi.

## Amaliy misol

PostgreSQL versiyasini va holatini tekshirish (Terminal):

```bash
# PostgreSQL xizmati holatini tekshirish
systemctl status postgresql

# O'rnatilgan versiyani ko'rish
psql --version
```

SQL orqali versiyani aniqlash:
```sql
SELECT version();
```

## Keng tarqalgan xatolar

❌ **Noto'g'ri:** PostgreSQL ni oddiy faylga asoslangan SQLite kabi alohida server jarayonisiz ishlatishga urinish.
✅ **To'g'ri:** PostgreSQL doimiy ishlovchi fon xizmati (service/daemon) sifatida ishlaydi va 5432-portda so'rovlarni tinglaydi.
> **Sababi:** PostgreSQL ko'p foydalanuvchili yuqori yuklamali tizimlar uchun mo'ljallangan to'laqonli serverdir.

## Mashq va vazifalar
1. **Oson:** Terminalda `psql --version` buyrug'ini ishga tushirib, PostgreSQL versiyangizni aniqlang.
2. **O'rtacha:** PostgreSQL ning MySQL va SQLite dan asosiy 3 ta ustunligini yozing.
3. **Qiyin:** Write-Ahead Logging (WAL) ning maqsadi va ishlash mexanizmini tushuntirib bering.

## Qisqacha xulosa
PostgreSQL — ishonchliligi, ACID talablariga to'liq mosligi va keng imkoniyatlari bilan zamonaviy veb-dasturlashning standart ma'lumotlar bazasi hisoblanadi."""
            },
            {
                "fn": "0.2-postgresql-ornatish-psql-ubuntu-docker.md",
                "name": "0.2. PostgreSQL o'rnatish va psql bilan ishlash (Ubuntu & Docker)",
                "content": """# 0.2. PostgreSQL o'rnatish va psql bilan ishlash (Ubuntu & Docker)

## Bu darsda nimalarni o'rganasiz
- Ubuntu (Linux) tizimida PostgreSQL o'rnatish
- Docker orqali PostgreSQL konteynerini ko'tarish
- `psql` interaktiv konsoli va uning eng muhim meta-buyruqlari
- Standart `postgres` foydalanuvchisi va parollarni sozlash

## Nazariy qism

### 1. Ubuntu tizimida PostgreSQL o'rnatish
Ubuntu'da rasmiy paket menejeri orqali o'rnatish:

```bash
# 1. Paketlar ro'yxatini yangilash
sudo apt update

# 2. PostgreSQL va qo'shimcha utilitalarni o'rnatish
sudo apt install postgresql postgresql-contrib -y

# 3. PostgreSQL xizmatini yoqish va ishga tushirish
sudo systemctl enable postgresql
sudo systemctl start postgresql
```

### 2. Docker orqali ishga tushirish (Tavsiya etiladi)
Docker yordamida izolyatsiyalangan PostgreSQL muhitini yaratish:

```bash
docker run --name postgres-db -e POSTGRES_PASSWORD=sirli_parol -p 5432:5432 -d postgres:16
```

### 3. `psql` interaktiv terminali
`psql` — PostgreSQL bilan to'g'ridan-to'g'ri muloqot qilish uchun rasmiy buyruqlar satri vositasidir:

```bash
# postgres foydalanuvchisi nomidan psql ga kirish
sudo -u postgres psql
```

## Amaliy misollar: psql Meta-buyruqlari

`psql` ichidagi maxsus buyruqlar `\\` (backslash) bilan boshlanadi:

| Buyruq | Vazifasi |
|---|---|
| `\\l` | Barcha ma'lumotlar bazalari ro'yxatini ko'rsatish |
| `\\c baza_nomi` | Boshqa ma'lumotlar bazasiga ulanish (connect) |
| `\\dt` | Joriy bazadagi barcha jadvallar ro'yxati |
| `\\d+ jadval_nomi` | Jadval tuzilishi, ustunlari va turlarini batafsil ko'rish |
| `\\du` | Barcha foydalanuvchilar va rollar ro'yxati |
| `\\x` | Kengaytirilgan chiqish rejimi (uzun qatorlarni o'qishli formatda ko'rsatish) |
| `\\timing` | Har bir SQL so'rovining bajarilish vaqtini ko'rsatishni yoqish |
| `\\q` | psql konsolidan chiqish |

Parol o'rnatish misoli:
```sql
ALTER USER postgres WITH PASSWORD 'yangi_kuchli_parol';
```

## Keng tarqalgan xatolar

❌ **Noto'g'ri:** `\\l` yoki `\\dt` kabi psql buyruqlari oxiriga nuqta-vergul (`;`) qo'yish shart deb o'ylash.
✅ **To'g'ri:** Faqat SQL so'rovlari (SELECT, INSERT va h.k.) oxiriga `;` qo'yiladi. `\\` bilan boshlanuvchi meta-buyruqlarga `;` shart emas.

❌ **Noto'g'ri:** Oddiy Linux foydalanuvchisi sifatida to'g'ridan-to'g'ri `psql` terib ulanishga urinish va "FATAL: role does not exist" xatosini olish.
✅ **To'g'ri:** `sudo -u postgres psql` yoki `psql -U postgres -h localhost` orqali ulanish.

## Mashq va vazifalar
1. **Oson:** Ubuntu'da `sudo -u postgres psql` orqali konsolga kiring va `\\l` buyrug'i bilan mavjud bazalarni ko'ring.
2. **O'rtacha:** Yangi `test_db` nomli baza yarating va `\\c test_db` orqali unga ulaning.
3. **Qiyin:** Docker orqali PostgreSQL 16 konteynerini ishga tushiring va uning ichiga `docker exec -it` orqali kirib `psql` ni oching.

## Qisqacha xulosa
`psql` — PostgreSQL ning eng tezkor va qudratli vositasi bo'lib, ishlab chiquvchilar uchun serverlarni boshqarishda asosiy qurol hisoblanadi."""
            },
            {
                "fn": "0.3-pgadmin-dbeaver-grafik-interfeys.md",
                "name": "0.3. pgAdmin 4 va DBeaver vositalarini sozlash",
                "content": """# 0.3. pgAdmin 4 va DBeaver vositalarini sozlash

## Bu darsda nimalarni o'rganasiz
- GUI (grafik interfeys) vositalarining vazifasi va afzalliklari
- pgAdmin 4 va DBeaver o'rtasidagi farqlar
- PostgreSQL serveriga GUI orqali xavfsiz ulanishni sozlash
- Query Tool (So'rovlar oynasi) bilan ishlash

## Nazariy qism

### Grafik mijozlar (GUI Clients)
Terminaldagi `psql` buyruqlari juda qulay bo'lsa-da, katta jadvallarni ko'rish, diagrammalar tuzish va murakkab so'rovlar yozishda grafik dasturlar yordam beradi:
1. **DBeaver:** Barcha SQL bazalar (PostgreSQL, MySQL, SQLite, Oracle) uchun universal, nihoyatda tezkor va professional bepul dastur.
2. **pgAdmin 4:** PostgreSQL uchun maxsus ishlab chiqilgan rasmiy veb/desktop vosita.

### Ulanish parametrlari (Connection Settings)
Istalgan GUI vositasi orqali ulanishda 5 ta asosiy parametr kiritiladi:
- **Host (Manzil):** `localhost` yoki server IP manzili (masalan, `127.0.0.1` yoki `82.70.41.85`).
- **Port:** Standart `5432`.
- **Database (Baza nomi):** `postgres` yoki o'zingiz yaratgan baza.
- **Username (Foydalanuvchi):** `postgres` yoki loyiha useri.
- **Password (Parol):** Foydalanuvchiga berilgan parol.

## Amaliy misol

DBeaver o'rnatish (Ubuntu):
```bash
sudo snap install dbeaver-ce
```

DBeaver orqali SQL Query yozish va natijani jadval ko'rinishida olish:
```sql
-- DBeaver Query Editor oynasida
SELECT 
    schemaname, 
    tablename, 
    tableowner 
FROM pg_catalog.pg_tables 
WHERE schemaname NOT IN ('pg_catalog', 'information_schema');
```

## Keng tarqalgan xatolar

❌ **Noto'g'ri:** Masofaviy serverga ulanishda PostgreSQL porti (5432) xavfsizlik devori (UFW/Firewall) orqali yopiq bo'lsa ham "nega ulanmayapti" deb hayron bo'lish.
✅ **To'g'ri:** Serverda `postgresql.conf` da `listen_addresses = '*'` va `pg_hba.conf` da ruxsat berilgan bo'lishi yoki SSH Tunnel orqali ulanish kerak.

## Mashq va vazifalar
1. **Oson:** DBeaver yoki pgAdmin dasturini kompyuteringizga o'rnating.
2. **O'rtacha:** Mahalliy PostgreSQL serveringizga ulanish yarating va Query Tool oynasini oching.
3. **Qiyin:** DBeaver orqali ER-diagramma (jadvallar bog'liqligi grafigi) ko'rinishini ochib ko'ring.

## Qisqacha xulosa
Grafik dasturlar ma'lumotlarni tahlil qilish, jadvallarni vizual boshqarish va so'rovlar natijasini chiroyli ko'rish uchun ajoyib yordamchidir."""
            }
        ]
    },
    {
        "dir": "01-bob-baza-va-jadvallar-ddl",
        "title": "01. Baza va Jadvallar (DDL)",
        "lessons": [
            {
                "fn": "1.1-create-drop-database.md",
                "name": "1.1. CREATE DATABASE va DROP DATABASE (Baza boshqaruvi)",
                "content": """# 1.1. CREATE DATABASE va DROP DATABASE (Baza boshqaruvi)

## Bu darsda nimalarni o'rganasiz
- DDL (Data Definition Language) tushunchasi
- Yangi ma'lumotlar bazasini yaratish (`CREATE DATABASE`)
- Bazani xavfsiz o'chirish (`DROP DATABASE IF EXISTS`)
- Baza parametrlarini sozlash (Encoding, Owner, Collation)

## Nazariy qism
**DDL (Data Definition Language)** — ma'lumotlar bazasining strukturasi (bazalar, jadvallar, ustunlar, indekslar)ni yaratish, o'zgartirish va o'chirish uchun ishlatiladigan SQL buyruqlari to'plamidir.

### Baza yaratish sintaksisi
```sql
CREATE DATABASE baza_nomi
    [WITH]
    [OWNER = egasi]
    [ENCODING = 'UTF8']
    [LC_COLLATE = 'C']
    [LC_CTYPE = 'C']
    [TEMPLATE = shablon];
```

### Bazani o'chirish sintaksisi
```sql
DROP DATABASE [IF EXISTS] baza_nomi;
```
> ⚠️ **DIQQAT:** `DROP DATABASE` buyrug'i bazadagi BARCHA jadvallar va ma'lumotlarni butunlay o'chirib tashlaydi. Orqaga qaytarib bo'lmaydi!

## Amaliy misollar

```sql
-- 1. Oddiy baza yaratish
CREATE DATABASE oquv_markaz;

-- 2. UTF-8 kodirovkasi bilan baza yaratish
CREATE DATABASE do'kon_db WITH ENCODING 'UTF8';

-- 3. Agar mavjud bo'lsa xatosiz o'chirish
DROP DATABASE IF EXISTS test_db;

-- 4. Baza nomini o'zgartirish
ALTER DATABASE oquv_markaz RENAME TO oquv_markazi_crm;
```

## Keng tarqalgan xatolar

❌ **Noto'g'ri:** O'zingiz ayni paytda ulanib turgan bazani o'chirishga urinish (`ERROR: cannot drop the currently open database`).
✅ **To'g'ri:** Avval boshqa bazaga (masalan, `postgres` bazasiga `\\c postgres`) ulanib, so'ngra maqsadli bazani o'chirish kerak.

## Mashq va vazifalar
1. **Oson:** `shop_db` nomli yangi baza yarating.
2. **O'rtacha:** `shop_db` bazasini `ecommerce_db` ga o'zgartiring (rename).
3. **Qiyin:** Faqat SQL so'rovi yordamida barcha bazalar ro'yxatini va ularning hajmini (`pg_size_pretty`) chiqaring.

## Qisqacha xulosa
`CREATE DATABASE` va `DROP DATABASE` bazaning eng yuqori darajadagi boshqaruv buyruqlari bo'lib, har bir yangi loyiha alohida ma'lumotlar bazasida boshlanadi."""
            },
            {
                "fn": "1.2-malumot-turlari-data-types.md",
                "name": "1.2. Ma'lumot turlari (INTEGER, VARCHAR, TEXT, BOOLEAN, DATE, JSONB)",
                "content": """# 1.2. Ma'lumot turlari (INTEGER, VARCHAR, TEXT, BOOLEAN, DATE, JSONB)

## Bu darsda nimalarni o'rganasiz
- PostgreSQL da asosiy sonli turlar (SMALLINT, INTEGER, BIGINT, NUMERIC/DECIMAL)
- Matn turlari (CHAR, VARCHAR, TEXT) va ularning farqi
- Sana va vaqt turlari (DATE, TIME, TIMESTAMP, TIMESTAMPTZ)
- Maxsus turlar: BOOLEAN, UUID, JSON, JSONB, ARRAY

## Nazariy qism

PostgreSQL dunyodagi eng boy ma'lumot turlariga ega ma'lumotlar bazasidir:

| Toifa | Ma'lumot turi | Tavsif / Xotira | Misol |
|---|---|---|---|
| **Sonlar** | `SMALLINT` | 2 bayt (-32,768 dan 32,767 gacha) | `yosh SMALLINT` |
| | `INTEGER` (`INT`) | 4 bayt (2 milliardgacha) | `id INTEGER` |
| | `BIGINT` | 8 bayt (juda katta sonlar) | `telegram_id BIGINT` |
| | `NUMERIC(p, s)` | Aniq kasr sonlar (pul mablag'lari uchun) | `narx NUMERIC(10, 2)` |
| | `REAL / DOUBLE` | Suzuvchi nuqtali sonlar | `koordinata DOUBLE PRECISION` |
| **Matnlar** | `VARCHAR(n)` | Maksimal `n` ta belgili satr | `ism VARCHAR(50)` |
| | `TEXT` | Cheksiz uzunlikdagi matn | `tavsif TEXT` |
| | `CHAR(n)` | Doimiy `n` ta belgi (yetmaganiga bo'sh joy qo'shadi) | `kod CHAR(3)` |
| **Mantiqiy** | `BOOLEAN` | `TRUE`, `FALSE` yoki `NULL` | `faolmi BOOLEAN` |
| **Vaqt** | `DATE` | Faqat sana (YIL-OY-KUN) | `2026-08-19` |
| | `TIMESTAMP` | Sana va vaqt (soat, minut, sekund) | `2026-08-19 14:30:00` |
| | `TIMESTAMPTZ` | Vaqt mintaqasi bilan (Timezone) — **TAVSIYA** | `2026-08-19 14:30:00+05` |
| **Maxsus** | `UUID` | 128-bitli takrorlanmas identifikator | `a0eebc99-9c0b...` |
| | `JSONB` | Binary JSON (indekslanuvchi, tezkor) | `{'key': 'value'}` |
| | `TEXT[]` | Massiv (ro'yxat) | `{'olma', 'anor'}` |

## Amaliy misol

```sql
CREATE TABLE foydalanuvchilar (
    id BIGSERIAL,
    uuid_id UUID DEFAULT gen_random_uuid(),
    ism VARCHAR(50),
    email VARCHAR(100),
    balans NUMERIC(12, 2),
    faolmi BOOLEAN DEFAULT TRUE,
    qoshilgan_vaqt TIMESTAMPTZ DEFAULT NOW(),
    sozlamalar JSONB
);
```

## Keng tarqalgan xatolar

❌ **Noto'g'ri:** Narxlar va moliyaviy hisob-kitoblar uchun `FLOAT` yoki `DOUBLE PRECISION` ishlatish (yaxlitlashdagi xatolar tufayli tiyinlar yo'qoladi).
✅ **To'g'ri:** Moliyaviy ma'lumotlar uchun doimo **`NUMERIC` / `DECIMAL`** ishlatish kerak.

❌ **Noto'g'ri:** Vaqt saqlash uchun oddiy `TIMESTAMP` ishlatish.
✅ **To'g'ri:** Serverlar turli mintaqalarda bo'lishi mumkinligi sababli **`TIMESTAMPTZ`** (Timezone bilan) ishlatish eng yaxshi amaliyotdir.

## Mashq va vazifalar
1. **Oson:** Telegram bot foydalanuvchilari uchun qaysi turdagi `id` tanlanadi? Nega `BIGINT`?
2. **O'rtacha:** Mahsulot narxini 12 xonali va 2 xona kasr aniqlikda saqlash turini yozing.
3. **Qiyin:** `JSON` va `JSONB` o'rtasidagi asosiy farqlarni tushuntiring.

## Qisqacha xulosa
To'g'ri ma'lumot turini tanlash — ma'lumotlar bazasining tezkorligi, disk xotirasi tejamkorligi va ma'lumotlar to'g'riligining asosiy poydevoridir."""
            },
            {
                "fn": "1.3-create-drop-table.md",
                "name": "1.3. CREATE TABLE va DROP TABLE (Jadval yaratish va o'chirish)",
                "content": """# 1.3. CREATE TABLE va DROP TABLE (Jadval yaratish va o'chirish)

## Bu darsda nimalarni o'rganasiz
- Jadval (Table) tushunchasi va relyatsion model
- `CREATE TABLE` sintaksisi va ustunlar ta'rifi
- `SERIAL` va `BIGSERIAL` avto-inkrement tushunchasi
- `DROP TABLE` va `DROP TABLE IF EXISTS`

## Nazariy qism
Jadval — ma'lumotlar bazasida qatorlar (rows/records) va ustunlar (columns/fields) shaklida saqlanadigan asosiy struktura birligidir.

### Sintaksis
```sql
CREATE TABLE [IF NOT EXISTS] jadval_nomi (
    ustun_1 malumot_turi [cheklovlar],
    ustun_2 malumot_turi [cheklovlar],
    ...
);
```

### Avto-inkrement (SERIAL vs IDENTITY)
PostgreSQL da har bir yangi qatorga avtomatik 1, 2, 3... raqam berish uchun:
- `SERIAL` (4-baytli avto-raqam)
- `BIGSERIAL` (8-baytli katta avto-raqam)
- `GENERATED ALWAYS AS IDENTITY` (SQL standarti)

## Amaliy misollar

```sql
-- 1. Talabalar jadvalini yaratish
CREATE TABLE talabalar (
    id SERIAL PRIMARY KEY,
    ism VARCHAR(50) NOT NULL,
    familiya VARCHAR(50) NOT NULL,
    yosh INTEGER,
    telefon VARCHAR(20),
    stipendiya NUMERIC(10, 2) DEFAULT 0.00,
    yaratilgan_sana TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Jadvalni tekshirib o'chirish
DROP TABLE IF EXISTS talabalar;

-- 3. Mavjud jadval asosida nusxa jadval yaratish
CREATE TABLE talabalar_zaxira AS 
SELECT * FROM talabalar;
```

## Keng tarqalgan xatolar

❌ **Noto'g'ri:** Jadval nomlarida va ustunlarda probel yoki katta-kichik harflar aralash nom ishlatib qo'shtirnoqqa bog'lanib qolish (`"Mening Jadvalim"`).
✅ **To'g'ri:** Doimo kichik harflar va pastki chiziq (snake_case) ishlating: `mening_jadvalim`.

❌ **Noto'g'ri:** O'chirilmoqchi bo'lgan jadval boshqa jadvalga Foreign Key orqali ulangan bo'lsa xato olish.
✅ **To'g'ri:** Bog'langan jadvallarni birga o'chirish uchun `DROP TABLE jadval_nomi CASCADE;` ishlatiladi.

## Mashq va vazifalar
1. **Oson:** `kitoblar` nomli jadval yarating: `id`, `nomi`, `muallif`, `sahifalar_soni`, `narxi`.
2. **O'rtacha:** `SERIAL` va `BIGSERIAL` farqini tushuntiring.
3. **Qiyin:** `CREATE TABLE IF NOT EXISTS` buyrug'ining afzalligini ayting.

## Qisqacha xulosa
`CREATE TABLE` — relyatsion ma'lumotlar bazasining yuragi bo'lib, uning yordamida loyihaning barcha obyektlari uchun modellar shakllantiriladi."""
            },
            {
                "fn": "1.4-constraints-cheklovlar.md",
                "name": "1.4. Cheklovlar (Constraints: PRIMARY KEY, NOT NULL, UNIQUE, CHECK, DEFAULT)",
                "content": """# 1.4. Cheklovlar (Constraints: PRIMARY KEY, NOT NULL, UNIQUE, CHECK, DEFAULT)

## Bu darsda nimalarni o'rganasiz
- Cheklovlar (Constraints) nima va nega ular kerak
- `PRIMARY KEY` — Birlamchi kalit
- `NOT NULL` — Bo'sh qolmaslik sharti
- `UNIQUE` — Takrorlanmaslik kafolati
- `CHECK` — Maxsus mantiqiy tekshiruvlar
- `DEFAULT` — Standart qiymat berish

## Nazariy qism

Cheklovlar — ma'lumotlar bazasiga noto'g'ri, mantiqsiz yoki buzilgan ma'lumotlar kirishining oldini oluvchi qoidalardir.

| Cheklov | Vazifasi | Misol |
|---|---|---|
| `PRIMARY KEY` | Qatorning yagona identifikatori (NOT NULL + UNIQUE) | `id SERIAL PRIMARY KEY` |
| `NOT NULL` | Ustun bo'sh (`NULL`) bo'lishi taqiqlanadi | `ism VARCHAR(50) NOT NULL` |
| `UNIQUE` | Ustundagi qiymat takrorlanmasligi shart | `email VARCHAR(100) UNIQUE` |
| `CHECK` | Shart bajarilishi majburiy (masalan, yosh > 0) | `CHECK (yosh >= 18 AND yosh <= 100)` |
| `DEFAULT` | Qiymat berilmasa, avtomatik o'rnatiladigan qiymat | `status VARCHAR(20) DEFAULT 'yangi'` |

## Amaliy misollar

```sql
CREATE TABLE xodimlar (
    id SERIAL PRIMARY KEY,
    tabel_raqam VARCHAR(10) UNIQUE NOT NULL,
    ism VARCHAR(50) NOT NULL,
    yosh INTEGER CHECK (yosh >= 18),
    maosh NUMERIC(10, 2) CHECK (maosh > 0),
    lavozim VARCHAR(50) DEFAULT 'Kichik dasturchi',
    email VARCHAR(100) UNIQUE NOT NULL,
    faolmi BOOLEAN DEFAULT TRUE,
    CONSTRAINT check_ism_uzunlik CHECK (LENGTH(ism) >= 2)
);
```

Cheklovni sinab ko'rish (xato yuzaga keladi):
```sql
-- Xato: Yosh 18 dan kichik bo'lishi mumkin emas!
INSERT INTO xodimlar (tabel_raqam, ism, yosh, maosh, email)
VALUES ('X001', 'Ali', 15, 5000000, 'ali@example.com');
-- ERROR: new row for relation "xodimlar" violates check constraint "xodimlar_yosh_check"
```

## Keng tarqalgan xatolar

❌ **Noto'g'ri:** Tekshiruvlarni faqat backend kodida (Python/Django) qilib, bazada `CHECK` va `NOT NULL` qo'ymash.
✅ **To'g'ri:** Xavfsizlik va ma'lumotlar yaxlitligi uchun tekshiruvlar ham backend da, ham ma'lumotlar bazasi darajasida o'rnatilishi shart.

## Mashq va vazifalar
1. **Oson:** `foydalanuvchilar` jadvaliga `email` ustunini `UNIQUE` va `NOT NULL` qilib qo'shing.
2. **O'rtacha:** Mahsulotlar jadvalida `narx > 0` va `chegirma_foizi BETWEEN 0 AND 100` shartini qo'ying.
3. **Qiyin:** Jadval darajasida (Table-level constraint) ikkita ustun birgalikda unikal bo'lishini (`UNIQUE(kurs_id, talaba_id)`) yozing.

## Qisqacha xulosa
Cheklovlar ma'lumotlar bazasining sofligi va ishonchliligini ta'minlaydi."""
            },
            {
                "fn": "1.5-alter-table-ustunlarni-boshqarish.md",
                "name": "1.5. ALTER TABLE (Ustun qo'shish, o'chirish va nomini o'zgartirish)",
                "content": """# 1.5. ALTER TABLE (Ustun qo'shish, o'chirish va nomini o'zgartirish)

## Bu darsda nimalarni o'rganasiz
- Mavjud jadval strukturasini o'zgartirish (`ALTER TABLE`)
- Yangi ustun qo'shish (`ADD COLUMN`)
- Ustunni o'chirish (`DROP COLUMN`)
- Ustun nomini va jadval nomini o'zgartirish (`RENAME`)
- Ustun turini o'zgartirish (`ALTER COLUMN TYPE`)
- Cheklov qo'shish va olib tashlash

## Nazariy qism
Loyiha rivojlangani sari jadvallarga yangi ustunlar qo'shish yoki mavjudlarini o'zgartirish talab etiladi. Buning uchun `ALTER TABLE` buyrug'i xizmat qiladi.

## Amaliy misollar

```sql
-- 1. Yangi ustun qo'shish
ALTER TABLE xodimlar ADD COLUMN manzil TEXT;
ALTER TABLE xodimlar ADD COLUMN passport_seriya VARCHAR(9) UNIQUE;

-- 2. Ustunni o'chirish
ALTER TABLE xodimlar DROP COLUMN manzil;

-- 3. Ustun nomini o'zgartirish
ALTER TABLE xodimlar RENAME COLUMN ism TO toliq_ism;

-- 4. Jadval nomini o'zgartirish
ALTER TABLE xodimlar RENAME TO ishchilar;

-- 5. Ustun ma'lumot turini o'zgartirish (masalan VARCHAR(50) dan VARCHAR(100) ga)
ALTER TABLE ishchilar ALTER COLUMN toliq_ism TYPE VARCHAR(100);

-- 6. Ustunga DEFAULT qiymat qo'shish yoki olib tashlash
ALTER TABLE ishchilar ALTER COLUMN lavozim SET DEFAULT 'Amaliyotchi';
ALTER TABLE ishchilar ALTER COLUMN lavozim DROP DEFAULT;

-- 7. Ustunga NOT NULL cheklovini qo'shish
ALTER TABLE ishchilar ALTER COLUMN toliq_ism SET NOT NULL;

-- 8. Yangi CHECK cheklovini qo'shish
ALTER TABLE ishchilar ADD CONSTRAINT check_maosh_chegara CHECK (maosh >= 1000000);
```

## Keng tarqalgan xatolar

❌ **Noto'g'ri:** Jadvalda allaqachon `NULL` qiymatli qatorlar mavjud bo'lganda, `SET NOT NULL` qo'yishga urinish.
✅ **To'g'ri:** Avval `UPDATE ishchilar SET toliq_ism = 'Noma'lum' WHERE toliq_ism IS NULL;` qilib bo'sh joylarni to'ldirib, keyin `SET NOT NULL` o'rnatiladi.

## Mashq va vazifalar
1. **Oson:** `talabalar` jadvaliga `tugilgan_sana DATE` ustunini qo'shing.
2. **O'rtacha:** `talabalar` jadvalidagi `telefon` ustuni nomini `telefon_raqam` ga o'zgartiring.
3. **Qiyin:** Mavjud ustun turini `VARCHAR` dan `INTEGER` ga `USING` kalit so'zi yordamida o'tkazish sintaksisini yozing.

## Qisqacha xulosa
`ALTER TABLE` buyrug'i ma'lumotlarni o'chirmasdan turib jadval strukturasini o'zgartirish imkonini beradi."""
            },
            {
                "fn": "1.6-foreign-key-boshqa-jadvallar-boglanish.md",
                "name": "1.6. Bog'lanishlar va Tashqi kalit (FOREIGN KEY, ON DELETE CASCADE / SET NULL)",
                "content": """# 1.6. Bog'lanishlar va Tashqi kalit (FOREIGN KEY, ON DELETE CASCADE / SET NULL)

## Bu darsda nimalarni o'rganasiz
- Relyatsion bog'lanishlar nima (Relational database)
- `FOREIGN KEY` (Tashqi kalit) tushunchasi
- Bog'lanish turlari: 1-to-1, 1-to-Many, Many-to-Many
- Kaskadli o'chirish turlari: `ON DELETE CASCADE`, `ON DELETE SET NULL`, `ON DELETE RESTRICT`

## Nazariy qism
Relyatsion bazaning asosiy kuchi — jadvallarning bir-biri bilan kalitlar orqali bog'lanishidadir.

### Tashqi kalit (Foreign Key)
Bir jadvaldagi ustun boshqa jadvalning `PRIMARY KEY` ustuniga havola qilsa, bu ustun **FOREIGN KEY** deyiladi.

### O'chirish qoidalari (ON DELETE actions)
Ota (asosiy) qatordagi ma'lumot o'chirilganda, unga bog'langan bola qatorlar nima bo'lishini belgilaydi:
- **`CASCADE`:** Ota o'chirilsa, unga bog'langan barcha bola qatorlar ham avtomatik o'chiriladi. (Masalan, Post o'chirilsa, uning barcha Kommentlari ham o'chadi).
- **`SET NULL`:** Ota o'chirilsa, bola qatordagi bog'lanish ustuni `NULL` bo'lib qoladi.
- **`RESTRICT / NO ACTION`:** Bog'langan bola qatorlar mavjud bo'lsa, ota qatorni o'chirishga ruxsat bermaydi (Standart xavfsiz rejim).

## Amaliy misollar

```sql
-- 1. Ota jadval: Fakultetlar
CREATE TABLE fakultetlar (
    id SERIAL PRIMARY KEY,
    nomi VARCHAR(100) NOT NULL UNIQUE
);

-- 2. Bola jadval: Talabalar (Fakultetga bog'langan)
CREATE TABLE talabalar (
    id SERIAL PRIMARY KEY,
    ism VARCHAR(50) NOT NULL,
    fakultet_id INTEGER NOT NULL,
    CONSTRAINT fk_fakultet
        FOREIGN KEY (fakultet_id) 
        REFERENCES fakultetlar(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- 3. Ko'pga-ko'p (Many-to-Many) bog'lanish uchun oraliq jadval
CREATE TABLE fanlar (
    id SERIAL PRIMARY KEY,
    nomi VARCHAR(100) NOT NULL
);

CREATE TABLE talaba_fanlar (
    talaba_id INTEGER REFERENCES talabalar(id) ON DELETE CASCADE,
    fan_id INTEGER REFERENCES fanlar(id) ON DELETE CASCADE,
    PRIMARY KEY (talaba_id, fan_id)
);
```

## Keng tarqalgan xatolar

❌ **Noto'g'ri:** Bola jadvalga ota jadvalda mavjud bo'lmagan ID ni kiritishga urinish (`ERROR: insert or update on table violates foreign key constraint`).
✅ **To'g'ri:** Avval ota jadvalga (fakultet) qator qo'shiladi, so'ngra uning ID si bola jadvalda ishlatiladi.

## Mashq va vazifalar
1. **Oson:** `mualliflar` va `kitoblar` jadvallarini `FOREIGN KEY` orqali bog'lang.
2. **O'rtacha:** Muallif o'chirilganda kitoblari o'chmasdan, `muallif_id` ustuni `NULL` bo'lib qolishi uchun qaysi parametr beriladi?
3. **Qiyin:** Buyurtmalar va Mahsulotlar o'rtasida Many-to-Many munosabatini yarating.

## Qisqacha xulosa
`FOREIGN KEY` — relyatsion ma'lumotlar bazasining yaxlitligini ta'minlovchi eng muhim mexanizmdir."""
            }
        ]
    },
    {
        "dir": "02-bob-malumotlar-dml",
        "title": "02. Ma'lumotlar bilan ishlash (DML)",
        "lessons": [
            {
                "fn": "2.1-insert-into-qator-qoshish.md",
                "name": "2.1. INSERT INTO — Qator qo'shish va ko'p qatorli kiritish",
                "content": """# 2.1. INSERT INTO — Qator qo'shish va ko'p qatorli kiritish

## Bu darsda nimalarni o'rganasiz
- DML (Data Manipulation Language) tushunchasi
- `INSERT INTO` sintaksisi
- Bitta va bir nechta qatorlarni bir vaqtda kiritish (Bulk insert)
- `RETURNING` kalit so'zi (Kiritilgan ma'lumotni darhol qaytarib olish)

## Nazariy qism
**DML (Data Manipulation Language)** — jadvallar ichidagi ma'lumotlar ustida amallar bajaruvchi buyruqlardir (`INSERT`, `SELECT`, `UPDATE`, `DELETE`).

### Sintaksis
```sql
INSERT INTO jadval_nomi (ustun1, ustun2, ...)
VALUES (qiymat1, qiymat2, ...);
```

## Amaliy misollar

```sql
-- 1. Bitta qator qo'shish
INSERT INTO fakultetlar (nomi) 
VALUES ('Dasturiy injiniring');

-- 2. Bir vaqtda bir nechta qator qo'shish (Ko'p qatorli INSERT)
INSERT INTO fakultetlar (nomi) VALUES 
('Kiberxavfsizlik'),
('Suniy intellekt'),
('Telekommunikatsiya');

-- 3. RETURNING orqali avtomatik hosil bo'lgan ID ni olish (PostgreSQL ning ajoyib imkoniyati)
INSERT INTO fakultetlar (nomi) 
VALUES ('Robototexnika') 
RETURNING id, nomi;

-- 4. Boshqa jadvaldan SELECT qilib INSERT qilish
INSERT INTO arxiv_talabalar (ism, familiya)
SELECT ism, familiya FROM talabalar WHERE bitirganmi = TRUE;
```

## Keng tarqalgan xatolar

❌ **Noto'g'ri:** Matnli qiymatlarni qo'sh tirnoq (`"Dasturiy injiniring"`) bilan yozish.
✅ **To'g'ri:** SQL da matnli qiymatlar doimo **bitta tirnoq** (`'Dasturiy injiniring'`) ichiga olinadi. Qo'sh tirnoq faqat jadval/ustun nomlari uchun ishlatiladi.

## Mashq va vazifalar
1. **Oson:** `foydalanuvchilar` jadvaliga o'z ismingiz va emailingizni kiriting.
2. **O'rtacha:** Birgina `INSERT` buyrug'i bilan 3 ta mahsulotni jadvalga qo'shing.
3. **Qiyin:** Yangi foydalanuvchi qo'shib, uning generatsiya qilingan `id` va `yaratilgan_vaqt` ini `RETURNING` orqali qaytaring.

## Qisqacha xulosa
`INSERT INTO` jadvalga yangi ma'lumot kiritishning asosiy buyrug'idir."""
            },
            {
                "fn": "2.2-select-asoslari.md",
                "name": "2.2. SELECT asoslari va ustun tanlash",
                "content": """# 2.2. SELECT asoslari va ustun tanlash

## Bu darsda nimalarni o'rganasiz
- `SELECT` — ma'lumotlarni o'qish buyrug'i
- Barcha ustunlarni tanlash (`SELECT *`)
- Faqat kerakli ustunlarni tanlash
- Ustunlarga taxallus (Alias — `AS`) berish
- Hisoblash ifodalarini SELECT da ishlatish

## Nazariy qism
`SELECT` — SQL tilidagi eng ko'p ishlatiladigan buyruq bo'lib, jadvallardan kerakli ma'lumotlarni so'rab olish vazifasini bajaradi.

## Amaliy misollar

```sql
-- 1. Barcha ustunlar va qatorlarni olish
SELECT * FROM talabalar;

-- 2. Faqat kerakli ustunlarni olish
SELECT ism, familiya, stipendiya FROM talabalar;

-- 3. Ustunlarga yangi nom (Alias - AS) berish
SELECT 
    ism AS talaba_ismi,
    familiya AS talaba_familiyasi,
    stipendiya * 12 AS yillik_stipendiya
FROM talabalar;

-- 4. Matnlarni birlashtirish (Concat - ||)
SELECT ism || ' ' || familiya AS toliq_ism FROM talabalar;

-- 5. Jadvallarsiz oddiy hisob-kitoblar
SELECT 25 * 4 AS natija, NOW() AS ayni_vaqt;
```

## Keng tarqalgan xatolar

❌ **Noto'g'ri:** Production (katta loyihalarda) doimo `SELECT *` ishlatish.
✅ **To'g'ri:** Doimo faqat kerakli ustunlarni sanab yozing (`SELECT id, ism, email`). Bu tarmoq trafigini va xotira yuklamasini keskin kamaytiradi.

## Mashq va vazifalar
1. **Oson:** `mahsulotlar` jadvalidan faqat `nomi` va `narxi` ustunlarini tanlang.
2. **O'rtacha:** Har bir mahsulot narxiga 12% QQS qo'shilgan narxni `narx_qqs_bilan` nomi ostida chiqaring.
3. **Qiyin:** Xodimlarning ismi va lavozimini bitta satrga birlashtirib chiqaring.

## Qisqacha xulosa
`SELECT` so'rovi ma'lumotlar bazasidan kerakli ma'lumotlarni saralab olishning kalitidir."""
            },
            {
                "fn": "2.3-where-filtr-solishtirish.md",
                "name": "2.3. WHERE filtrlash va solishtirish operatorlari",
                "content": """# 2.3. WHERE filtrlash va solishtirish operatorlari

## Bu darsda nimalarni o'rganasiz
- `WHERE` bandining vazifasi
- Solishtirish operatorlari: `=`, `!=` yoki `<>`, `<`, `>`, `<=`, `>=`
- Shart bo'yicha ma'lumotlarni filtrlash qoidalari

## Nazariy qism
`WHERE` — jadvaldagi barcha qatorlar orasidan faqat berilgan shartga mos keluvchi (`TRUE` qaytaruvchi) qatorlarni tanlab olish uchun xizmat qiladi.

## Amaliy misollar

```sql
-- 1. Aniq qiymatga tenglik
SELECT * FROM talabalar WHERE ism = 'Ali';

-- 2. Teng emaslik (!= yoki <>)
SELECT * FROM talabalar WHERE fakultet_id != 1;

-- 3. Katta va kichik solishtirishlar
SELECT * FROM talabalar WHERE stipendiya > 1000000;
SELECT * FROM talabalar WHERE yosh <= 20;

-- 4. Sana bo'yicha filtrlash
SELECT * FROM buyurtmalar WHERE yaratilgan_vaqt >= '2026-01-01';
```

## Keng tarqalgan xatolar

❌ **Noto'g'ri:** `WHERE` bandini `FROM` dan oldin yozish.
✅ **To'g'ri:** SQL sintaksisi qat'iy tartibga ega: `SELECT ... FROM ... WHERE ...`.

❌ **Noto'g'ri:** `NULL` qiymatni tekshirish uchun `WHERE ustun = NULL` deb yozish.
✅ **To'g'ri:** `NULL` uchun doimo **`IS NULL`** yoki **`IS NOT NULL`** ishlatiladi.

## Mashq va vazifalar
1. **Oson:** Narxi 50000 dan arzon bo'lgan barcha mahsulotlarni toping.
2. **O'rtacha:** 2005-yildan keyin tug'ilgan barcha talabalarni chiqaring.
3. **Qiyin:** `status` ustuni `'bekor_qilingan'` bo'lmagan barcha buyurtmalarni tanlang.

## Qisqacha xulosa
`WHERE` qatorlarni shart asosida saralash uchun asosiy filtr hisoblanadi."""
            },
            {
                "fn": "2.4-mantiqiy-operatorlar-and-or-in-like.md",
                "name": "2.4. Mantiqiy operatorlar (AND, OR, NOT, IN, BETWEEN, LIKE, ILIKE)",
                "content": """# 2.4. Mantiqiy operatorlar (AND, OR, NOT, IN, BETWEEN, LIKE, ILIKE)

## Bu darsda nimalarni o'rganasiz
- `AND` va `OR` mantiqiy operatorlari
- `NOT` inkor operatori
- `IN` va `NOT IN` (To'plamda mavjudlik)
- `BETWEEN ... AND ...` (Oraliqni tekshirish)
- `LIKE` va `ILIKE` (Shablon bo'yicha qidiruv, katta-kichik harflar)

## Nazariy qism

| Operator | Tavsif | Misol |
|---|---|---|
| `AND` | Ikkala shart ham to'g'ri bo'lishi shart | `yosh >= 18 AND yosh <= 25` |
| `OR` | Shartlardan kamida bittasi to'g'ri bo'lsa yetarli | `shahar = 'Toshkent' OR shahar = 'Samarqand'` |
| `IN (...)` | Qiymatlar ro'yxatidan biriga teng bo'lsa | `shahar IN ('Toshkent', 'Buxoro', 'Navoiy')` |
| `BETWEEN a AND b` | `a` dan `b` gacha oraliqda bo'lsa (ikkala chegara ham kiradi) | `narx BETWEEN 10000 AND 50000` |
| `LIKE` | Shablon bo'yicha qidiruv (`%` — ixtiyoriy belgilar, `_` — bitta belgi) | `ism LIKE 'A%'` (A bilan boshlanuvchilar) |
| `ILIKE` | Case-insensitive LIKE (PostgreSQL ga xos, registrni farqlamaydi) | `ism ILIKE 'ali%'` (Ali, ali, ALI mos keladi) |

## Amaliy misollar

```sql
-- 1. AND va OR birgalikda (Qavslarga e'tibor bering!)
SELECT * FROM xodimlar 
WHERE (lavozim = 'Dasturchi' OR lavozim = 'Dizayner') 
  AND maosh > 5000000;

-- 2. IN operatori
SELECT * FROM talabalar 
WHERE fakultet_id IN (1, 3, 5);

-- 3. BETWEEN operatori
SELECT * FROM mahsulotlar 
WHERE narx BETWEEN 50000 AND 200000;

-- 4. ILIKE orqali qidiruv (Qidiruv tizimi uchun)
SELECT * FROM kitoblar 
WHERE nomi ILIKE '%python%';
```

## Keng tarqalgan xatolar

❌ **Noto'g'ri:** `AND` va `OR` birga kelganda qavslarni qo'ymaslik (`AND` ning ustunligi yuqori bo'lgani uchun noto'g'ri natija beradi).
✅ **To'g'ri:** Mantiqiy guruhlarni har doim qavs `(...)` ichiga oling.

## Mashq va vazifalar
1. **Oson:** Ismi 'O' harfi bilan boshlanadigan barcha talabalarni toping.
2. **O'rtacha:** Narxi 100 000 dan 500 000 gacha bo'lgan va kategoriyasi 2 yoki 4 bo'lgan mahsulotlarni chiqaring.
3. **Qiyin:** Email manzili `@gmail.com` bilan tugaydigan xodimlarni toping.

## Qisqacha xulosa
Mantiqiy operatorlar orqali juda murakkab va aniq qidiruv shartlarini yaratish mumkin."""
            },
            {
                "fn": "2.5-order-by-limit-offset.md",
                "name": "2.5. Tartiblash va Cheklash (ORDER BY, LIMIT, OFFSET, FETCH)",
                "content": """# 2.5. Tartiblash va Cheklash (ORDER BY, LIMIT, OFFSET, FETCH)

## Bu darsda nimalarni o'rganasiz
- Ma'lumotlarni saralash (`ORDER BY`)
- O'sish (`ASC`) va Kamayish (`DESC`) tartibi
- Natijani cheklash (`LIMIT`)
- Sahifalash (Pagination) uchun `OFFSET`
- SQL standarti: `FETCH FIRST n ROWS ONLY`

## Nazariy qism

### 1. Tartiblash (`ORDER BY`)
Bazada ma'lumotlar tartibsiz saqlanadi. Aniq tartibda olish uchun `ORDER BY` ishlatiladi:
- `ASC` (Ascending) — O'sish tartibida (A dan Z gacha, 1 dan 9 gacha) — **Standart**.
- `DESC` (Descending) — Kamayish tartibida (Z dan A gacha, 9 dan 1 gacha).

### 2. Sahifalash (`LIMIT` va `OFFSET`)
Veb-saytlarda 1-sahifa, 2-sahifa qilib ma'lumotlarni bo'lib ko'rsatishda:
- `LIMIT N` — Faqat `N` ta qatorni qaytarish.
- `OFFSET M` — Boshidagi `M` ta qatorni tashlab yuborish.

Formula: `OFFSET = (sahifa_raqami - 1) * sahifa_hajmi`

## Amaliy misollar

```sql
-- 1. Eng qimmat 5 ta mahsulot
SELECT nomi, narx FROM mahsulotlar 
ORDER BY narx DESC 
LIMIT 5;

-- 2. Bir nechta ustun bo'yicha tartiblash
SELECT ism, familiya, yosh FROM talabalar 
ORDER BY yosh ASC, familiya ASC;

-- 3. Sahifalash (Pagination) — 2-sahifa (har sahifada 10 tadan)
SELECT * FROM mahsulotlar 
ORDER BY id ASC 
LIMIT 10 OFFSET 10;

-- 4. NULL qiymatlarni oxiriga yoki boshiga qo'yish
SELECT * FROM xodimlar 
ORDER BY maosh DESC NULLS LAST;

-- 5. Standart SQL FETCH sintaksisi
SELECT * FROM talabalar 
ORDER BY id 
FETCH FIRST 5 ROWS ONLY;
```

## Keng tarqalgan xatolar

❌ **Noto'g'ri:** `LIMIT` va `OFFSET` ni `ORDER BY` siz ishlatish (Har safar turli qatorlar chiqib qolishi mumkin).
✅ **To'g'ri:** Sahifalashda barqaror natija uchun doimo aniq ustun (masalan, `id`) bo'yicha `ORDER BY` qo'llang.

## Mashq va vazifalar
1. **Oson:** Eng ko'p maosh oluvchi 3 ta xodimni chiqaring.
2. **O'rtacha:** Har bir sahifada 20 tadan ma'lumot ko'rsatilsa, 4-sahifaning `LIMIT` va `OFFSET` qiymatlarini yozing.
3. **Qiyin:** Talabalarni avval fakultet bo'yicha o'sish, so'ngra stipendiya bo'yicha kamayish tartibida saralang.

## Qisqacha xulosa
`ORDER BY` va `LIMIT/OFFSET` ma'lumotlarni tartibli va sahifalarga bo'lingan holda tezkor taqdim etish imkonini beradi."""
            },
            {
                "fn": "2.6-update-delete-ozgartirish-ochirish.md",
                "name": "2.6. UPDATE va DELETE (Ma'lumotlarni yangilash va o'chirish)",
                "content": """# 2.6. UPDATE va DELETE (Ma'lumotlarni yangilash va o'chirish)

## Bu darsda nimalarni o'rganasiz
- Qatorlardagi qiymatlarni yangilash (`UPDATE`)
- Qatorlarni o'chirish (`DELETE FROM`)
- Butun jadvalni tezkor tozalash (`TRUNCATE TABLE`)
- `WHERE` shartining hayotiy muhimligi

## Nazariy qism

### UPDATE sintaksisi
```sql
UPDATE jadval_nomi 
SET ustun1 = yangi_qiymat1, ustun2 = yangi_qiymat2
WHERE shart;
```

### DELETE sintaksisi
```sql
DELETE FROM jadval_nomi 
WHERE shart;
```

> 🚨 **MUHIM OGOHLANTIRISH:** Agar `UPDATE` yoki `DELETE` buyrug'ida `WHERE` shartini yozishni unutsangiz, jadvaldagi **BARCHA** qatorlar o'zgaradi yoki o'chib ketadi!

## Amaliy misollar

```sql
-- 1. Aniq bir xodimning maoshini oshirish
UPDATE xodimlar 
SET maosh = 8000000, lavozim = 'Katta dasturchi'
WHERE id = 5;

-- 2. Hamma xodimlarning maoshini 10% ga oshirish
UPDATE xodimlar 
SET maosh = maosh * 1.10;

-- 3. Shart bo'yicha qatorni o'chirish
DELETE FROM talabalar 
WHERE id = 10;

-- 4. O'chirilgan ma'lumotni RETURNING orqali ko'rish
DELETE FROM xodimlar 
WHERE faolmi = FALSE 
RETURNING id, ism, email;

-- 5. TRUNCATE — Jadvalni bir zumda to'liq tozalash va ID ni 1 dan boshlash
TRUNCATE TABLE vaqtinchalik_loglar RESTART IDENTITY;
```

## Keng tarqalgan xatolar

❌ **Noto'g'ri:** `WHERE` siz `DELETE FROM talabalar;` buyrug'ini yuborib, butun bazadagi talabalarni o'chirib yuborish.
✅ **To'g'ri:** Har qanday `UPDATE` va `DELETE` dan oldin xuddi shu shart bilan `SELECT * FROM ... WHERE ...` qilib tekshirib oling.

## Mashq va vazifalar
1. **Oson:** ID si 3 bo'lgan mahsulot narxini 45000 ga o'zgartiring.
2. **O'rtacha:** Yaratilganiga 1 yildan oshgan va statusi 'bekor_qilingan' barcha buyurtmalarni o'chiring.
3. **Qiyin:** `DELETE` va `TRUNCATE` o'rtasidagi 3 ta asosiy farqni ayting.

## Qisqacha xulosa
`UPDATE` va `DELETE` juda ehtiyotkorlik bilan va doimo aniq `WHERE` filtri bilan ishlatilishi lozim."""
            },
            {
                "fn": "2.7-null-qiymatlar-bilan-ishlash.md",
                "name": "2.7. NULL qiymatlar bilan ishlash (IS NULL, IS NOT NULL, COALESCE)",
                "content": """# 2.7. NULL qiymatlar bilan ishlash (IS NULL, IS NOT NULL, COALESCE)

## Bu darsda nimalarni o'rganasiz
- `NULL` nima? (Noma'lumlik / Ma'lumot yo'qligi)
- Uch qiymatli mantiq (Three-Valued Logic: TRUE, FALSE, UNKNOWN)
- `IS NULL` va `IS NOT NULL`
- `COALESCE` funksiyasi (NULL o'rniga zaxira qiymat berish)
- `NULLIF` funksiyasi

## Nazariy qism
`NULL` — bu `0` ham emas, bo'sh matn `''` ham emas. `NULL` — bu **qiymat mavjud emasligi** yoki **noma'lumlik** demakdir.

Shu sababli, `NULL = NULL` ifodasi `FALSE` (aniqrog'i `UNKNOWN`) qaytaradi, chunki ikkita noma'lum narsa bir-biriga tengmi-yo'qmi bilib bo'lmaydi!

### COALESCE funksiyasi
`COALESCE(a, b, c, ...)` — berilgan ro'yxatdan birinchi `NULL` bo'lmagan qiymatni qaytaradi:

```sql
SELECT COALESCE(NULL, NULL, 'Zaxira qiymat'); -- 'Zaxira qiymat' qaytadi
```

## Amaliy misollar

```sql
-- 1. Telefoni ko'rsatilmagan talabalarni topish
SELECT * FROM talabalar 
WHERE telefon IS NULL;

-- 2. Telefoni bor talabalar
SELECT * FROM talabalar 
WHERE telefon IS NOT NULL;

-- 3. Agar telefon NULL bo'lsa, 'Mavjud emas' deb chiqarish
SELECT 
    ism, 
    COALESCE(telefon, 'Raqam kiritilmagan') AS aloqa_telefoni
FROM talabalar;

-- 4. NULLIF: Ikkala qiymat teng bo'lsa NULL qaytaradi (0 ga bo'lish xatosidan saqlanish)
SELECT 100 / NULLIF(qatorlar_soni, 0) FROM statistika;
```

## Keng tarqalgan xatolar

❌ **Noto'g'ri:** `WHERE telefon = NULL;` yoki `WHERE telefon != NULL;`
✅ **To'g'ri:** Doimo **`WHERE telefon IS NULL`** va **`WHERE telefon IS NOT NULL`** ishlatiladi.

## Mashq va vazifalar
1. **Oson:** Manzili (`manzil` ustuni) kiritilmagan barcha xodimlarni toping.
2. **O'rtacha:** Agar xodimning `mukofot_puli` ustuni `NULL` bo'lsa, uni `0` deb hisoblab umumiy daromadni (`maosh + mukofot_puli`) hisoblang.
3. **Qiyin:** Nega `NULL = NULL` sharti hech qachon qator qaytarmaydi?

## Qisqacha xulosa
`NULL` bilan ishlashda doimo `IS NULL` va `COALESCE` funksiyalaridan foydalanish zarur."""
            }
        ]
    },
    {
        "dir": "03-bob-agregatsiya-guruhlash",
        "title": "03. Agregatsiya va Guruhlash",
        "lessons": [
            {
                "fn": "3.1-agregat-funksiyalar-count-sum-avg.md",
                "name": "3.1. Agregat funksiyalar (COUNT, SUM, AVG, MIN, MAX)",
                "content": """# 3.1. Agregat funksiyalar (COUNT, SUM, AVG, MIN, MAX)

## Bu darsda nimalarni o'rganasiz
- Agregat funksiyalar nima va qanday ishlaydi
- `COUNT(*)` va `COUNT(ustun)` farqi
- `SUM()` — Yig'indini hisoblash
- `AVG()` — O'rtacha qiymatni topish
- `MIN()` va `MAX()` — Eng kichik va eng katta qiymatlar

## Nazariy qism
Agregat funksiyalar bir nechta qatorlardagi qiymatlarni qabul qilib, bitta yakuniy qiymat (statistika) hisoblab beradi.

| Funksiya | Vazifasi | Izoh |
|---|---|---|
| `COUNT(*)` | Barcha qatorlar soni | NULL bo'lgan qatorlarni ham sanaydi |
| `COUNT(ustun)` | Ustunda qiymati bor qatorlar soni | NULL larni hisobga olmaydi |
| `SUM(ustun)` | Ustundagi sonlarning umumiy yig'indisi | Faqat sonli ustunlar uchun |
| `AVG(ustun)` | Ustundagi o'rtacha arifmetik qiymat | `SUM / COUNT` |
| `MIN(ustun)` | Eng kichik qiymat | Son, matn va sanalarda ishlaydi |
| `MAX(ustun)` | Eng katta qiymat | Son, matn va sanalarda ishlaydi |

## Amaliy misollar

```sql
-- 1. Jami talabalar soni
SELECT COUNT(*) AS jami_talabalar FROM talabalar;

-- 2. Umumiy oylik maosh fondi va o'rtacha maosh
SELECT 
    SUM(maosh) AS jami_maosh_fondi,
    ROUND(AVG(maosh), 2) AS ortacha_maosh,
    MIN(maosh) AS eng_kam_maosh,
    MAX(maosh) AS eng_kop_maosh
FROM xodimlar;

-- 3. Shart bilan birga agregatsiya
SELECT COUNT(*) AS a_lochi_talabalar 
FROM talabalar 
WHERE baho = 5;
```

## Keng tarqalgan xatolar

❌ **Noto'g'ri:** `SELECT ism, AVG(maosh) FROM xodimlar;` (Ism har xil, lekin AVG bitta son qaytaradi — `GROUP BY` siz xato beradi).
✅ **To'g'ri:** Agregat funksiya bilan boshqa ustunlar birga kelsa, `GROUP BY` ishlatilishi shart.

## Mashq va vazifalar
1. **Oson:** Do'kondagi barcha mahsulotlar soni va ularning umumiy narxini hisoblang.
2. **O'rtacha:** Eng birinchi ro'yxatdan o'tgan (`MIN(yaratilgan_sana)`) foydalanuvchi sanasini toping.
3. **Qiyin:** Nega `COUNT(*)` va `COUNT(telefon)` natijasi har xil bo'lishi mumkin?

## Qisqacha xulosa
Agregat funksiyalar hisobotlar va tahliliy statistikalar tuzishda asosiy vositadir."""
            },
            {
                "fn": "3.2-group-by-guruhlash.md",
                "name": "3.2. GROUP BY — Guruhlash asoslari",
                "content": """# 3.2. GROUP BY — Guruhlash asoslari

## Bu darsda nimalarni o'rganasiz
- `GROUP BY` ning ishlash mexanizmi
- Har bir guruh uchun alohida statistika hisoblash
- Bir nechta ustunlar bo'yicha guruhlash

## Nazariy qism
`GROUP BY` buyrug'i bir xil qiymatga ega bo'lgan qatorlarni bitta guruhga birlashtiradi. Har bir guruh ustida agregat funksiyalar (`COUNT`, `SUM`, `AVG`) mustaqil ishlaydi.

## Amaliy misollar

```sql
-- 1. Har bir fakultetda nechtadan talaba o'qiydi?
SELECT 
    fakultet_id, 
    COUNT(*) AS talabalar_soni
FROM talabalar
GROUP BY fakultet_id;

-- 2. Har bir lavozimdagi o'rtacha maosh va xodimlar soni
SELECT 
    lavozim,
    COUNT(*) AS ishchilar_soni,
    ROUND(AVG(maosh), 2) AS ortacha_maosh
FROM xodimlar
GROUP BY lavozim
ORDER BY ortacha_maosh DESC;

-- 3. Ikki ustun bo'yicha guruhlash (Shahar va Jins)
SELECT 
    shahar, 
    jinsi, 
    COUNT(*) AS miqdor
FROM mijozlar
GROUP BY shahar, jinsi;
```

## Keng tarqalgan xatolar

❌ **Noto'g'ri:** `SELECT` da turgan, lekin agregat funksiyaga olinmagan ustunni `GROUP BY` ga kiritishni unutish (`ERROR: column must appear in the GROUP BY clause`).
✅ **To'g'ri:** `SELECT` da ko'rsatilgan har qanday oddiy ustun `GROUP BY` da ham sanab o'tilishi shart.

## Mashq va vazifalar
1. **Oson:** Har bir toifadagi (kategoriya) mahsulotlar sonini hisoblang.
2. **O'rtacha:** Har bir shahar bo'yicha eng yuqori maoshni aniqlang.
3. **Qiyin:** Buyurtmalar jadvalidan har bir oy bo'yicha tushgan jami summani guruhlang.

## Qisqacha xulosa
`GROUP BY` ma'lumotlarni turkumlarga ajratib, har bir turkum bo'yicha aniq xulosalar chiqarishga xizmat qiladi."""
            },
            {
                "fn": "3.3-having-guruhlarni-filtrlash.md",
                "name": "3.3. HAVING — Guruhlangan ma'lumotlarni filtrlash",
                "content": """# 3.3. HAVING — Guruhlangan ma'lumotlarni filtrlash

## Bu darsda nimalarni o'rganasiz
- `HAVING` va `WHERE` o'rtasidagi asosiy farq
- Guruhlangan natijalarni shart bo'yicha saralash
- `WHERE` + `GROUP BY` + `HAVING` birgalikda qo'llanishi

## Nazariy qism

### WHERE va HAVING farqi:
- **`WHERE`:** Guruhlashdan **OLDIN** har bir alohida qatorni filtrlaydi. Unda agregat funksiyalar (`SUM`, `COUNT`) ishlatib bo'lmaydi.
- **`HAVING`:** Guruhlashdan **KEYIN** hosil bo'lgan guruhlarni filtrlaydi. Unda agregat funksiyalar tekshiriladi.

SQL so'rovining bajarilish tartibi:
`FROM` ➔ `WHERE` ➔ `GROUP BY` ➔ `HAVING` ➔ `SELECT` ➔ `ORDER BY` ➔ `LIMIT`

## Amaliy misollar

```sql
-- 1. Faqat talabalar soni 20 tadan ko'p bo'lgan fakultetlarni chiqarish
SELECT 
    fakultet_id, 
    COUNT(*) AS talabalar_soni
FROM talabalar
GROUP BY fakultet_id
HAVING COUNT(*) > 20;

-- 2. O'rtacha maoshi 8 milliondan yuqori bo'lgan lavozimlar
SELECT 
    lavozim,
    AVG(maosh) AS ortacha_maosh
FROM xodimlar
WHERE faolmi = TRUE -- Avval faol xodimlarni saralaymiz
GROUP BY lavozim
HAVING AVG(maosh) >= 8000000;
```

## Keng tarqalgan xatolar

❌ **Noto'g'ri:** `WHERE COUNT(*) > 5` deb yozish (`ERROR: aggregate functions are not allowed in WHERE`).
✅ **To'g'ri:** Agregat shartlar doimo **`HAVING COUNT(*) > 5`** da yoziladi.

## Mashq va vazifalar
1. **Oson:** Jami narxi 10 milliondan oshgan mahsulot toifalarini `HAVING` orqali chiqaring.
2. **O'rtacha:** Kamida 3 ta xodim ishlaydigan bo'limlarni toping.
3. **Qiyin:** `WHERE` va `HAVING` ning bitta so'rovda birga ishlashini amaliy misolda ko'rsating.

## Qisqacha xulosa
`HAVING` — agregat funksiyalar natijasini filtrlash uchun maxsus yaratilgan vositadir."""
            },
            {
                "fn": "3.4-distinct-unikal-qiymatlar.md",
                "name": "3.4. DISTINCT va SELECT DISTINCT ON",
                "content": """# 3.4. DISTINCT va SELECT DISTINCT ON

## Bu darsda nimalarni o'rganasiz
- `DISTINCT` orqali takrorlanuvchi qatorlarni olib tashlash
- `COUNT(DISTINCT ustun)` — Noyob qiymatlar soni
- PostgreSQL ning maxsus imkoniyati: `SELECT DISTINCT ON`

## Nazariy qism

### 1. DISTINCT
Agar jadvalda bir xil ma'lumotlar qayta-qayta takrorlangan bo'lsa, `DISTINCT` ulardan faqat bittasini (unikal nusxasini) qoldiradi.

### 2. DISTINCT ON (PostgreSQL Exclusives)
PostgreSQL da `DISTINCT ON (ustun)` yordamida berilgan ustun bo'yicha har bir guruhdan birinchi qatorni tanlab olish mumkin.

## Amaliy misollar

```sql
-- 1. Talabalarimiz qaysi shaharlardan ekanini ko'rish (Takrorlanishlarsiz)
SELECT DISTINCT shahar FROM talabalar;

-- 2. Nechta turli xil lavozim borligini sanash
SELECT COUNT(DISTINCT lavozim) AS turli_lavozimlar_soni FROM xodimlar;

-- 3. DISTINCT ON: Har bir bo'limdan eng ko'p maosh oluvchi 1 tadan xodimni olish!
SELECT DISTINCT ON (bolim_id) 
    bolim_id, 
    ism, 
    maosh 
FROM xodimlar 
ORDER BY bolim_id, maosh DESC;
```

## Keng tarqalgan xatolar

❌ **Noto'g'ri:** `DISTINCT ON` ishlatganda, `ORDER BY` ning birinchi ustuni `DISTINCT ON` dagi ustun bilan bir xil bo'lmasligi.
✅ **To'g'ri:** `DISTINCT ON (bolim_id)` bo'lsa, `ORDER BY bolim_id, ...` bilan boshlanishi shart.

## Mashq va vazifalar
1. **Oson:** Buyurtma bergan barcha mijozlarning unikal ID larini chiqaring.
2. **O'rtacha:** Har bir talabaning eng oxirgi olgan bahosini `DISTINCT ON` orqali toping.
3. **Qiyin:** `GROUP BY` va `DISTINCT` o'rtasidagi o'xshashlik va farqlarni ayting.

## Qisqacha xulosa
`DISTINCT` takrorlanishlarni tozalash, `DISTINCT ON` esa guruhlarning eng sara qatorlarini olish uchun ajoyib qulaylikdir."""
            }
        ]
    },
    {
        "dir": "04-bob-joins-va-toplamlar",
        "title": "04. Jadvallarni Birlashtirish (JOINS) va To'plamlar",
        "lessons": [
            {
                "fn": "4.1-inner-join-mos-birlashtirish.md",
                "name": "4.1. INNER JOIN — Mos keluvchi qatorlarni birlashtirish",
                "content": """# 4.1. INNER JOIN — Mos keluvchi qatorlarni birlashtirish

## Bu darsda nimalarni o'rganasiz
- `JOIN` tushunchasi va relyatsion modelning kuchi
- `INNER JOIN` ishlash prinsipi va Venn diagrammasi
- `ON` sharti orqali jadvallarni bog'lash
- Jadvallarga taxallus (Table Aliases) berish

## Nazariy qism
Relyatsion bazalarda ma'lumotlar turli jadvallarga bo'lingan bo'ladi (masalan, Talabalar va Fakultetlar). Ularni bitta so'rovda birlashtirib ko'rish uchun **JOIN** ishlatiladi.

**INNER JOIN** — faqat ikkala jadvalda ham o'zaro mos keluvchi (kesishuvdagi) qatorlarni qaytaradi.

## Amaliy misollar

```sql
-- Talaba ismi va u o'qiydigan fakultet nomini bitta jadvalda ko'rish
SELECT 
    t.id AS talaba_id,
    t.ism,
    t.familiya,
    f.nomi AS fakultet_nomi
FROM talabalar AS t
INNER JOIN fakultetlar AS f ON t.fakultet_id = f.id;

-- 3 ta jadvalni birlashtirish: Talaba, Fakultet va Guruh
SELECT 
    t.ism,
    f.nomi AS fakultet,
    g.nomi AS guruh
FROM talabalar t
INNER JOIN fakultetlar f ON t.fakultet_id = f.id
INNER JOIN guruhlar g ON t.guruh_id = g.id;
```

## Keng tarqalgan xatolar

❌ **Noto'g'ri:** Ikkala jadvalda bir xil nomli ustun bo'lsa (masalan `id` yoki `nomi`), jadval taxallusini ko'rsatmasdan `SELECT id, nomi` deb yozish (`ERROR: column reference is ambiguous`).
✅ **To'g'ri:** Doimo jadval taxallusi bilan aniq ko'rsating: `SELECT t.id, f.nomi`.

## Mashq va vazifalar
1. **Oson:** `buyurtmalar` va `mijozlar` jadvallarini `mijoz_id` orqali `INNER JOIN` qiling.
2. **O'rtacha:** Mahsulot nomi, uning toifasi nomi va yetkazib beruvchi kompaniya nomini chiqaring.
3. **Qiyin:** `INNER JOIN` da fakultetga biriktirilmagan (`fakultet_id IS NULL`) talabalar nima sababdan chiqmay qolishini tushuntiring.

## Qisqacha xulosa
`INNER JOIN` — faqat ikkala tomonda ham mavjud bo'lgan to'liq bog'liq ma'lumotlarni chiqaradi."""
            },
            {
                "fn": "4.2-left-right-join-tashqi-birlashuv.md",
                "name": "4.2. LEFT JOIN va RIGHT JOIN (Tashqi birlashuv)",
                "content": """# 4.2. LEFT JOIN va RIGHT JOIN (Tashqi birlashuv)",

## Bu darsda nimalarni o'rganasiz
- `LEFT JOIN` (LEFT OUTER JOIN) ishlash prinsipi
- `RIGHT JOIN` va ularning farqi
- Nega `LEFT JOIN` eng ko'p ishlatiladigan tashqi birlashuv hisoblanadi
- Mos kelmagan qatorlarda `NULL` hosil bo'lishi

## Nazariy qism

### LEFT JOIN
Chapdagi jadvalning **BARCHA** qatorlarini oladi. O'ngdagi jadvaldan esa faqat mos kelganlarini birlashtiradi. Agar o'ng jadvalda mos qator topilmasa, uning o'rniga `NULL` qiymatlar qo'yiladi.

> 💡 **Foydasi:** Hali birorta ham xarid qilmagan mijozlarni, yoki hali hech qanday talabasi yo'q bo'sh fakultetlarni topishda juda qo'l keladi!

## Amaliy misollar

```sql
-- 1. Barcha fakultetlar va ularning talabalari (Talabasi yo'q fakultetlar ham chiqadi!)
SELECT 
    f.nomi AS fakultet_nomi,
    t.ism AS talaba_ismi
FROM fakultetlar f
LEFT JOIN talabalar t ON f.id = t.fakultet_id;

-- 2. Hali birorta ham buyurtma bermagan yangi mijozlarni topish
SELECT 
    m.id, 
    m.ism, 
    m.email
FROM mijozlar m
LEFT JOIN buyurtmalar b ON m.id = b.mijoz_id
WHERE b.id IS NULL; -- Buyurtmasi yo'qlar
```

## Keng tarqalgan xatolar

❌ **Noto'g'ri:** `LEFT JOIN` qilingan o'ng jadval ustunini `WHERE` da tekshirib, bilmasdan `INNER JOIN` ga aylantirib qo'yish (`WHERE b.status = 'bajarildi'`).
✅ **To'g'ri:** Agar o'ng jadval shartini tekshirmoqchi bo'lsangiz, shartni `ON` ichiga yozing yoki `WHERE (b.status = 'bajarildi' OR b.id IS NULL)`.

## Mashq va vazifalar
1. **Oson:** Barcha mualliflar va ularning kitoblarini `LEFT JOIN` qiling (kitobi yo'q mualliflar ham chiqsin).
2. **O'rtacha:** Birorta ham xodimi mavjud bo'lmagan bo'limlarni toping.
3. **Qiyin:** Nega amaliyotda `RIGHT JOIN` o'rniga jadvallar o'rnini almashtirib `LEFT JOIN` ishlatish qulayroq hisoblanadi?

## Qisqacha xulosa
`LEFT JOIN` — asosiy jadvaldagi barcha qatorlarni saqlab qolgan holda qo'shimcha ma'lumotlarni ulash uchun eng yaxshi vositadir."""
            },
            {
                "fn": "4.3-full-outer-join-cross-join.md",
                "name": "4.3. FULL OUTER JOIN va CROSS JOIN",
                "content": """# 4.3. FULL OUTER JOIN va CROSS JOIN

## Bu darsda nimalarni o'rganasiz
- `FULL OUTER JOIN` — Har ikkala jadvalning barcha qatorlarini saqlash
- `CROSS JOIN` — Dekart ko'paytmasi (Cartesian product)
- Qachon va qaysi vaziyatlarda bu turlar qo'llaniladi

## Nazariy qism

### FULL OUTER JOIN
Har ikkala jadvaldan barcha qatorlarni oladi. Bir-biriga mos kelganlari birlashadi, mos kelmagan joylarga esa `NULL` qo'yiladi.

### CROSS JOIN
Birinchi jadvaldagi har bir qatorni ikkinchi jadvaldagi har bir qator bilan juftlab chiqadi.
Natijadagi qatorlar soni = `N * M` (A jadvaldagi qatorlar soni ko'paytirilgan B jadvaldagi qatorlar soni).

## Amaliy misollar

```sql
-- 1. FULL JOIN: Barcha talabalar va barcha fakultetlar (bog'lanmaganlari ham)
SELECT 
    t.ism, 
    f.nomi AS fakultet
FROM talabalar t
FULL OUTER JOIN fakultetlar f ON t.fakultet_id = f.id;

-- 2. CROSS JOIN: Mahsulot ranglari va o'lchamlari kombinatsiyasini hosil qilish
-- Ranglar: Qizil, Ko'k (2 ta)
-- O'lchamlar: S, M, L (3 ta)
-- Jami: 2 * 3 = 6 ta kombinatsiya
SELECT 
    r.rang_nomi,
    o.olcham_nomi
FROM ranglar r
CROSS JOIN olchamlar o;
```

## Keng tarqalgan xatolar

❌ **Noto'g'ri:** Katta hajmli ikkita jadvalni `CROSS JOIN` qilish (masalan, 100 000 x 100 000 = 10 milliard qator hosil bo'lib, server xotirasi to'lib qoladi).
✅ **To'g'ri:** `CROSS JOIN` faqat kichik parametrlar matritsasini yaratishda qo'llaniladi.

## Mashq va vazifalar
1. **Oson:** Hafta kunlari (7 ta) va smenalar (3 ta) o'rtasida `CROSS JOIN` orqali to'liq jadval tuzing.
2. **O'rtacha:** `FULL OUTER JOIN` orqali faqat ikkala tomondan ham bir-biriga mos kelmagan qatorlarni toping.
3. **Qiyin:** Barcha JOIN turlarini jamlovchi qisqa jadval chizing.

## Qisqacha xulosa
`FULL JOIN` to'liq taqqoslash uchun, `CROSS JOIN` esa barcha mumkin bo'lgan variantlar kombinatsiyasini tuzish uchun xizmat qiladi."""
            },
            {
                "fn": "4.4-anti-join-va-semi-join.md",
                "name": "4.4. ANTI JOIN va SEMI JOIN tushunchasi",
                "content": """# 4.4. ANTI JOIN va SEMI JOIN tushunchasi

## Bu darsda nimalarni o'rganasiz
- `SEMI JOIN` (Mavjudlikni tekshirish — `EXISTS` / `IN`)
- `ANTI JOIN` (Mavjud emaslikni aniqlash — `NOT EXISTS` / `LEFT JOIN ... WHERE IS NULL`)
- Katta hajmli ma'lumotlarda samaradorlik (Performance)

## Nazariy qism
SQL da `SEMI JOIN` va `ANTI JOIN` deb nomlanuvchi to'g'ridan-to'g'ri kalit so'z yo'q, lekin ular mantiqiy usul sifatida ishlatiladi:
- **SEMI JOIN:** Ikkinchi jadvalda kamida bitta mos qatori bor bo'lgan qatorlarni olish (lekin ikkinchi jadval ustunlarini qaytarmasdan).
- **ANTI JOIN:** Ikkinchi jadvalda birorta ham mos qatori **bo'lmagan** qatorlarni topish.

## Amaliy misollar

```sql
-- 1. SEMI JOIN (EXISTS yordamida) — Kamida 1 marta buyurtma bergan mijozlar
SELECT * FROM mijozlar m
WHERE EXISTS (
    SELECT 1 FROM buyurtmalar b WHERE b.mijoz_id = m.id
);

-- 2. ANTI JOIN (NOT EXISTS yordamida) — Hech qachon buyurtma bermagan mijozlar
SELECT * FROM mijozlar m
WHERE NOT EXISTS (
    SELECT 1 FROM buyurtmalar b WHERE b.mijoz_id = m.id
);

-- 3. ANTI JOIN (LEFT JOIN + IS NULL usuli)
SELECT m.*
FROM mijozlar m
LEFT JOIN buyurtmalar b ON m.id = b.mijoz_id
WHERE b.id IS NULL;
```

## Keng tarqalgan xatolar

❌ **Noto'g'ri:** `NOT IN (SELECT mijoz_id FROM buyurtmalar)` usulida ichki so'rovda bitta dona `NULL` bo'lsa, butun so'rov bo'sh natija qaytarishi (SQL NULL tuzog'i).
✅ **To'g'ri:** ANTI JOIN uchun doimo **`NOT EXISTS`** yoki **`LEFT JOIN ... WHERE IS NULL`** ishlatish xavfsiz va tezroqdir.

## Mashq va vazifalar
1. **Oson:** Hali birorta darsga qatnashmagan talabalarni `NOT EXISTS` bilan toping.
2. **O'rtacha:** Kamida bitta kitob sotib olgan xaridorlarni `EXISTS` orqali chiqaring.
3. **Qiyin:** Nega `NOT IN` da `NULL` bo'lsa butun natija yo'qolishini tushuntiring.

## Qisqacha xulosa
`EXISTS` va `NOT EXISTS` — relyatsion bazalarda ma'lumotlar mavjudligi yoki yo'qligini tekshirishning eng ishonchli usulidir."""
            },
            {
                "fn": "4.5-toplam-amallari-union-intersect-except.md",
                "name": "4.5. To'plam amallari (UNION, UNION ALL, INTERSECT, EXCEPT)",
                "content": """# 4.5. To'plam amallari (UNION, UNION ALL, INTERSECT, EXCEPT)

## Bu darsda nimalarni o'rganasiz
- To'plam amallari (Set Operations) nima
- `UNION` va `UNION ALL` (Birlashtirish va takrorlarni saqlash)
- `INTERSECT` (Kesishtirish)
- `EXCEPT` (Ayirish / Farqni topish)
- To'plam amallarining asosiy qoidalari

## Nazariy qism
To'plam amallari ikkita yoki undan ortiq `SELECT` so'rovlari natijasini bitta natijaga birlashtiradi.

### Qoidalar:
1. Har bir `SELECT` da ustunlar soni **teng** bo'lishi shart.
2. Mos ustunlarning ma'lumot turlari bir-biriga **mos kelishi** shart.

| Amal | Vazifasi |
|---|---|
| `UNION` | Ikkala so'rov natijasini birlashtiradi va takrorlangan qatorlarni o'chiradi |
| `UNION ALL` | Barcha qatorlarni birlashtiradi (takrorlarni ham saqlaydi — **Tezroq**) |
| `INTERSECT` | Faqat ikkala so'rovda ham mavjud bo'lgan umumiy qatorlarni qoldiradi |
| `EXCEPT` | Birinchi so'rovda bor, lekin ikkinchi so'rovda yo'q qatorlarni qaytaradi |

## Amaliy misollar

```sql
-- 1. Barcha mijozlar va xodimlarning telefon raqamlari ro'yxati (Unikal)
SELECT ism, telefon FROM mijozlar
UNION
SELECT ism, telefon FROM xodimlar;

-- 2. UNION ALL — Tezkor birlashtirish (dublikatlarni tozalamaydi)
SELECT ism, 'Mijoz' AS toifa FROM mijozlar
UNION ALL
SELECT ism, 'Xodim' AS toifa FROM xodimlar;

-- 3. INTERSECT — Ham talaba, ham xodim bo'lgan shaxslar
SELECT email FROM talabalar
INTERSECT
SELECT email FROM xodimlar;

-- 4. EXCEPT — Toshkentda yashovchi, lekin xarid qilmagan mijozlar
SELECT id FROM mijozlar WHERE shahar = 'Toshkent'
EXCEPT
SELECT mijoz_id FROM buyurtmalar;
```

## Keng tarqalgan xatolar

❌ **Noto'g'ri:** Takrorlanmaslik shart bo'lmagan joyda `UNION` ishlatish (Chunki `UNION` ortiqcha saralash va dublikat qidirish bilan serverni sekinlashtiradi).
✅ **To'g'ri:** Agar dublikatlar bo'lmasa yoki ularning borligi xalaqit bermasa, doimo **`UNION ALL`** ishlating.

## Mashq va vazifalar
1. **Oson:** 2025 va 2026-yilgi arxiv jadvallarini `UNION ALL` bilan birlashtiring.
2. **O'rtacha:** Faqat A kursda o'qiydigan, lekin B kursda o'qimaydigan talabalarni `EXCEPT` bilan toping.
3. **Qiyin:** Ikkala omborda ham mavjud bo'lgan mahsulotlarni `INTERSECT` orqali aniqlang.

## Qisqacha xulosa
To'plam amallari bir xil strukturali so'rovlarni birlashtirish, kesishtirish va ayirish uchun qulay matematik vositalardir."""
            }
        ]
    },
    {
        "dir": "05-bob-ichki-sorovlar-funksiyalar-view",
        "title": "05. Ichki so'rovlar, Funksiyalar va View",
        "lessons": [
            {
                "fn": "5.1-subqueries-ichki-sorovlar.md",
                "name": "5.1. Subqueries (Ichki so'rovlar: WHERE, FROM, SELECT)",
                "content": """# 5.1. Subqueries (Ichki so'rovlar: WHERE, FROM, SELECT)

## Bu darsda nimalarni o'rganasiz
- Subquery (Ichki so'rov) tushunchasi
- `WHERE` bandidagi skalyar va ko'p qatorli subquerylar
- `FROM` bandidagi subquery (Derived Tables)
- `SELECT` ustunida subquery ishlatish
- Korrelyatsiyalangan (Correlated) ichki so'rovlar

## Nazariy qism
**Subquery** — boshqa bir SQL so'rovi ichiga qavs `(...)` ichida yozilgan ichki SQL so'rovidir.

## Amaliy misollar

```sql
-- 1. O'rtacha maoshdan ko'p maosh oluvchi xodimlarni topish (WHERE dagi subquery)
SELECT ism, maosh 
FROM xodimlar 
WHERE maosh > (SELECT AVG(maosh) FROM xodimlar);

-- 2. FROM bandida subquery (Hosil qilingan jadval)
SELECT 
    fakultet_id, 
    ortacha_baho 
FROM (
    SELECT fakultet_id, AVG(baho) AS ortacha_baho 
    FROM talabalar 
    GROUP BY fakultet_id
) AS fak_statistika
WHERE ortacha_baho > 4.0;

-- 3. Har bir xodimning o'z bo'limidagi o'rtacha maoshdan farqi (Correlated Subquery)
SELECT 
    x.ism,
    x.maosh,
    x.bolim_id,
    (SELECT ROUND(AVG(maosh), 2) FROM xodimlar WHERE bolim_id = x.bolim_id) AS bolim_ortacha
FROM xodimlar x;
```

## Keng tarqalgan xatolar

❌ **Noto'g'ri:** Skalyar operator (`=`, `>`, `<`) ishlatilganda, ichki so'rov bir nechta qator qaytarishi (`ERROR: more than one row returned by a subquery used as an expression`).
✅ **To'g'ri:** Ko'p qator qaytsa `IN`, `ANY`, `ALL` operatorlari ishlatiladi.

## Mashq va vazifalar
1. **Oson:** Eng qimmat mahsulot narxiga teng bo'lgan barcha mahsulotlarni subquery orqali toping.
2. **O'rtacha:** Hech bo'lmaganda bitta 5 baho olgan talabalar ro'yxatini subquery bilan chiqaring.
3. **Qiyin:** Correlated subquery nima uchun oddiy subqueryga qaraganda sekinroq ishlashini tushuntiring.

## Qisqacha xulosa
Subquerylar ko'p bosqichli mantiqiy hisob-kitoblarni bitta so'rovda bajarishga yordam beradi."""
            },
            {
                "fn": "5.2-cte-with-va-rekursiv-cte.md",
                "name": "5.2. Common Table Expressions (WITH / CTE) va Rekursiv CTE",
                "content": """# 5.2. Common Table Expressions (WITH / CTE) va Rekursiv CTE

## Bu darsda nimalarni o'rganasiz
- CTE (`WITH` bandi) nima va uning afzalliklari
- Murakkab subquerylarni o'qishli formatga keltirish
- Rekursiv CTE (`WITH RECURSIVE`) tushunchasi
- Ierarxik ma'lumotlar (Daraxtsimon strukturalar, xodim-rahbar, kategoriyalar)

## Nazariy qism
**CTE (Common Table Expression)** — asosiy SQL so'rovi davomida vaqtinchalik mavjud bo'ladigan nomlangan natijalar to'plamidir. U `WITH` kalit so'zi bilan boshlanadi.

Afzalliklari:
- Murakkab ichma-ich so'rovlarni nihoyatda o'qishli va tushunarli qiladi.
- Bir necha marta qayta ishlatish mumkin.
- Rekursiv daraxtlarni (Menyular, Kategoriyalar) oson aylanib chiqadi.

## Amaliy misollar

```sql
-- 1. Oddiy CTE misoli
WITH yuqori_maoshlilar AS (
    SELECT * FROM xodimlar WHERE maosh > 10000000
),
toshkentliklar AS (
    SELECT * FROM yuqori_maoshlilar WHERE shahar = 'Toshkent'
)
SELECT ism, lavozim, maosh FROM toshkentliklar;

-- 2. RECURSIVE CTE: 1 dan 10 gacha sonlarni generatsiya qilish
WITH RECURSIVE sonlar AS (
    SELECT 1 AS n -- Boshlang'ich qadam (Anchor member)
    UNION ALL
    SELECT n + 1 FROM sonlar WHERE n < 10 -- Rekursiv qadam
)
SELECT * FROM sonlar;

-- 3. Rekursiv CTE: Xodimlar ierarxiyasi (Kim kimga rahbar)
WITH RECURSIVE xodim_daraxti AS (
    SELECT id, ism, rahbar_id, 1 AS daraja
    FROM xodimlar WHERE rahbar_id IS NULL -- Bosh direktor
    UNION ALL
    SELECT x.id, x.ism, x.rahbar_id, d.daraja + 1
    FROM xodimlar x
    INNER JOIN xodim_daraxti d ON x.rahbar_id = d.id
)
SELECT * FROM xodim_daraxti ORDER BY daraja;
```

## Keng tarqalgan xatolar

❌ **Noto'g'ri:** `WITH RECURSIVE` da to'xtash shartini (`WHERE n < 10`) qo'yishni unutib, cheksiz sikl (infinite loop) hosil qilish.
✅ **To'g'ri:** Rekursiv qadamda har doim qat'iy to'xtash sharti bo'lishi shart.

## Mashq va vazifalar
1. **Oson:** O'rtacha bahosi 4 dan yuqori bo'lgan talabalarni CTE yordamida ajratib oling.
2. **O'rtacha:** Rekursiv CTE yordamida joriy oyning barcha kunlari ro'yxatini generatsiya qiling.
3. **Qiyin:** Ko'p bosqichli kategoriya daraxtini (Masalan: Elektronika -> Telefonlar -> Smartfonlar) rekursiv CTE bilan chiqaring.

## Qisqacha xulosa
CTE — zamonaviy SQL da toza, o'qilishi oson va ierarxik so'rovlar yozishning eng professional usulidir."""
            },
            {
                "fn": "5.3-window-functions-oynali-funksiyalar.md",
                "name": "5.3. Window Functions (ROW_NUMBER, RANK, DENSE_RANK, OVER, PARTITION BY)",
                "content": """# 5.3. Window Functions (ROW_NUMBER, RANK, DENSE_RANK, OVER, PARTITION BY)

## Bu darsda nimalarni o'rganasiz
- Window (Oynali) funksiyalar nima va ularning `GROUP BY` dan farqi
- `OVER()` va `PARTITION BY` bandlari
- Reyting funksiyalari: `ROW_NUMBER()`, `RANK()`, `DENSE_RANK()`
- Siljish funksiyalari: `LAG()`, `LEAD()`
- Jamg'arib boruvchi yig'indi (Running total)

## Nazariy qism
Oynali funksiyalar qatorlarni bitta qatorga qisqartirib yubormasdan (**qatorlar sonini saqlagan holda**), ma'lum bir darcha (oyna) ichida hisob-kitoblarni amalga oshiradi.

## Amaliy misollar

```sql
-- 1. Har bir bo'lim ichida xodimlarga maosh bo'yicha o'rin berish
SELECT 
    ism,
    bolim_id,
    maosh,
    ROW_NUMBER() OVER(PARTITION BY bolim_id ORDER BY maosh DESC) AS qator_raqami,
    RANK() OVER(PARTITION BY bolim_id ORDER BY maosh DESC) AS orin_rank,
    DENSE_RANK() OVER(PARTITION BY bolim_id ORDER BY maosh DESC) AS orin_dense
FROM xodimlar;

-- 2. Jamg'arib boruvchi yig'indi (Running Total)
SELECT 
    sana,
    summa,
    SUM(summa) OVER(ORDER BY sana) AS jami_jamgarilgan_summa
FROM tushumlar;

-- 3. LAG va LEAD: Oldingi va keyingi qator qiymatini ko'rish
SELECT 
    oy,
    savdo_summasi,
    LAG(savdo_summasi, 1) OVER(ORDER BY oy) AS otgan_oydagi_savdo,
    savdo_summasi - LAG(savdo_summasi, 1) OVER(ORDER BY oy) AS oylik_osish
FROM oylik_savdo;
```

## Keng tarqalgan xatolar

❌ **Noto'g'ri:** `WHERE` bandida to'g'ridan-to'g'ri `ROW_NUMBER() = 1` deb yozish (Oynali funksiyalar `WHERE` dan keyin ishlaydi).
✅ **To'g'ri:** Oynali funksiya natijasini filtrlash uchun uni **CTE** yoki **Subquery** ichiga o'rab, keyin `WHERE qator_raqami = 1` qilinadi.

## Mashq va vazifalar
1. **Oson:** Barcha talabalarni kirish ballari bo'yicha 1 dan boshlab tartib raqam bilan chiqaring.
2. **O'rtacha:** Har bir fakultetdagi eng yuqori ball to'plagan 1-o'rindagi talabalarni CTE + `ROW_NUMBER()` orqali toping.
3. **Qiyin:** `RANK()` va `DENSE_RANK()` orasidagi farqni misolda ko'rsating.

## Qisqacha xulosa
Window funksiyalari — analitika, reytinglar va moliyaviy hisobotlar tuzishda tengsiz qudratli instrumentdir."""
            },
            {
                "fn": "5.4-view-va-materialized-view.md",
                "name": "5.4. View va Materialized View",
                "content": """# 5.4. View va Materialized View

## Bu darsda nimalarni o'rganasiz
- View (Virtual jadval) nima va nega kerak
- `CREATE VIEW` va `DROP VIEW`
- Materialized View (Xotirada saqlanuvchi ko'rinish)
- `REFRESH MATERIALIZED VIEW` orqali yangilash
- Qachon oddiy View, qachon Materialized View tanlanadi

## Nazariy qism

### 1. View (Oddiy ko'rinish)
View — bu saqlab qo'yilgan SQL so'rovidir. U diskda alohida ma'lumot saqlamaydi (virtual). Har safar View chaqirilganda, uning orqasidagi SQL so'rovi noldan bajariladi.

Afzalliklari:
- Murakkab JOIN so'rovlarni oddiy jadvaldek chaqirish imkoniyati.
- Xavfsizlik: Foydalanuvchiga faqat ruxsat berilgan ustunlarni ko'rsatish (masalan parollarni yashirib).

### 2. Materialized View
Materialized View so'rov natijasini **jismonan diskda saqlaydi**. Shuning uchun u milliardlab qatorli murakkab hisobotlarni ham 1 millisekundda qaytaradi. Lekin asosiy jadval o'zgarganda, u avtomatik o'zgarmaydi — uni `REFRESH` qilish kerak.

## Amaliy misollar

```sql
-- 1. Oddiy View yaratish
CREATE OR REPLACE VIEW talabalar_toliq_malumot AS
SELECT 
    t.id,
    t.ism || ' ' || t.familiya AS toliq_ism,
    f.nomi AS fakultet_nomi,
    t.stipendiya
FROM talabalar t
JOIN fakultetlar f ON t.fakultet_id = f.id;

-- View dan foydalanish
SELECT * FROM talabalar_toliq_malumot WHERE stipendiya > 1000000;

-- 2. Materialized View yaratish (Oylik og'ir hisobot uchun)
CREATE MATERIALIZED VIEW oylik_savdo_hisoboti AS
SELECT 
    DATE_TRUNC('month', yaratilgan_vaqt) AS oy,
    COUNT(*) AS buyurtmalar_soni,
    SUM(summa) AS umumiy_tushum
FROM buyurtmalar
GROUP BY 1;

-- Materialized View ma'lumotlarini yangilash
REFRESH MATERIALIZED VIEW oylik_savdo_hisoboti;
```

## Keng tarqalgan xatolar

❌ **Noto'g'ri:** Har soniyada yangilanib turadigan o'zgaruvchan ma'lumotlar uchun Materialized View ishlatish (Kesh eskirib qoladi).
✅ **To'g'ri:** Real-time ma'lumotlar uchun oddiy **View**, og'ir analitik hisobotlar uchun esa **Materialized View** ishlatiladi.

## Mashq va vazifalar
1. **Oson:** Xodimlarning ismi va bo'limi nomini birlashtiruvchi `xodimlar_view` yarating.
2. **O'rtacha:** Foydalanuvchilarning maxfiy parollari va tokenlarini yashiruvchi xavfsiz View yarating.
3. **Qiyin:** `REFRESH MATERIALIZED VIEW CONCURRENTLY` nima va uning afzalligi nimada?

## Qisqacha xulosa
View — kodni soddalashtirish va xavfsizlik uchun, Materialized View esa yuqori tezlik va kesh hisobotlar uchun xizmat qiladi."""
            },
            {
                "fn": "5.5-protseduralar-va-funksiyalar-plpgsql.md",
                "name": "5.5. Foydalanuvchi funksiyalari va Stored Procedures (PL/pgSQL)",
                "content": """# 5.5. Foydalanuvchi funksiyalari va Stored Procedures (PL/pgSQL)

## Bu darsda nimalarni o'rganasiz
- PL/pgSQL dasturlash tili asoslari
- Maxsus Funksiya (`CREATE FUNCTION`) yaratish
- Saqlanuvchi protsedura (`CREATE PROCEDURE`) yaratish
- Funksiya va Protsedura o'rtasidagi farq
- O'zgaruvchilar, `IF/ELSE` va `LOOP` sikllari

## Nazariy qism
**PL/pgSQL** — PostgreSQL ichiga o'rnatilgan protsedurali dasturlash tili bo'lib, uning yordamida to'g'ridan-to'g'ri baza ichida o'zgaruvchilar, shartlar, sikllar va murakkab biznes-mantiqni yozish mumkin.

### Funksiya va Protsedura farqi:
- **Function:** Doimo qiymat qaytaradi (`RETURNS`), `SELECT` ichida chaqiriladi.
- **Procedure:** PostgreSQL 11+ da qo'shilgan, tranzaksiyalarni (`COMMIT/ROLLBACK`) boshqara oladi, `CALL` bilan chaqiriladi.

## Amaliy misollar

```sql
-- 1. Oddiy SQL funksiya (QQS hisoblash)
CREATE OR REPLACE FUNCTION hisobla_qqs(narx NUMERIC)
RETURNS NUMERIC AS $$
BEGIN
    RETURN ROUND(narx * 0.12, 2);
END;
$$ LANGUAGE plpgsql;

-- Funksiyani chaqirish
SELECT nomi, narx, hisobla_qqs(narx) AS qqs_miqdori FROM mahsulotlar;

-- 2. Shartli mantiqqa ega PL/pgSQL funksiya
CREATE OR REPLACE FUNCTION talaba_darajasi(baho INT)
RETURNS TEXT AS $$
BEGIN
    IF baho = 5 THEN
        RETURN 'A\'lochi';
    ELSIF baho = 4 THEN
        RETURN 'Yaxshi';
    ELSE
        RETURN 'Qoniqarli';
    END IF;
END;
$$ LANGUAGE plpgsql;

-- 3. Stored Procedure (Balans o'tkazish tranzaksiyasi bilan)
CREATE OR REPLACE PROCEDURE pul_otkazish(
    jonatuvchi_id INT,
    qabul_qiluvchi_id INT,
    summa NUMERIC
)
AS $$
BEGIN
    UPDATE hisoblar SET balans = balans - summa WHERE id = jonatuvchi_id;
    UPDATE hisoblar SET balans = balans + summa WHERE id = qabul_qiluvchi_id;
    COMMIT;
END;
$$ LANGUAGE plpgsql;

-- Protsedurani chaqirish
CALL pul_otkazish(1, 2, 500000);
```

## Keng tarqalgan xatolar

❌ **Noto'g'ri:** Protsedurani `SELECT pul_otkazish(...)` deb chaqirish.
✅ **To'g'ri:** Protseduralar faqat **`CALL protsedura_nomi(...)`** orqali chaqiriladi.

## Mashq va vazifalar
1. **Oson:** Berilgan sonning kvadratini qaytaruvchi oddiy funksiya yozing.
2. **O'rtacha:** Foydalanuvchining tug'ilgan yili berilganda uning yoshini hisoblab beruvchi funksiya tuzing.
3. **Qiyin:** Xodimga mukofot puli yozuvchi va uning statusini yangilovchi `CALL yangi_mukofot(...)` protsedurasini yarating.

## Qisqacha xulosa
PL/pgSQL baza darajasida yuqori tezlikda ishlovchi murakkab mantiq va avtomatlashtirish imkoniyatini taqdim etadi."""
            }
        ]
    },
    {
        "dir": "06-bob-tranzaksiyalar-indekslar-xavfsizlik",
        "title": "06. Tranzaksiyalar, Indekslar va Xavfsizlik",
        "lessons": [
            {
                "fn": "6.1-tranzaksiyalar-va-acid.md",
                "name": "6.1. Tranzaksiyalar va ACID (BEGIN, COMMIT, ROLLBACK, SAVEPOINT)",
                "content": """# 6.1. Tranzaksiyalar va ACID (BEGIN, COMMIT, ROLLBACK, SAVEPOINT)

## Bu darsda nimalarni o'rganasiz
- Tranzaksiya tushunchasi va ACID tamoyillari
- `BEGIN`, `COMMIT`, `ROLLBACK` buyruqlari
- `SAVEPOINT` — oraliq saqlash nuqtalari
- Izolyatsiya darajalari (Transaction Isolation Levels)

## Nazariy qism

### ACID nima?
1. **Atomicity (Bo'linmaslik):** Barcha amallar yo to'liq bajariladi, yoki bittasi o'xshamasa hammasi bekor qilinadi ("Hammasi yoki hech narsa").
2. **Consistency (Muvofiqlik):** Baza barcha qoidalar va cheklovlarga mos holatda qoladi.
3. **Isolation (Yakkalanish):** Bir vaqtda ishlayotgan tranzaksiyalar bir-biriga xalaqit bermaydi.
4. **Durability (Chidamlilik):** Muvaffaqiyatli yakunlangan ma'lumotlar server o'chib qolsa ham yo'qolmaydi.

## Amaliy misollar

Klassik bank o'tkazmasi misoli (Pul yechildi, lekin ikkinchi tomonga yetib bormasdan xato bo'lsa, pul qaytarilishi shart):

```sql
-- Tranzaksiyani boshlash
BEGIN;

-- 1-amal: Alining hisobidan 100 000 so'm yechish
UPDATE hisoblar 
SET balans = balans - 100000 
WHERE id = 1;

-- Oraliq saqlash nuqtasi
SAVEPOINT pul_yechildi;

-- 2-amal: Valining hisobiga 100 000 so'm qo'shish
UPDATE hisoblar 
SET balans = balans + 100000 
WHERE id = 2;

-- Agar hammasi muvaffaqiyatli bo'lsa — tasdiqlash
COMMIT;

-- Agar biror joyda xato bo'lsa — barcha o'zgarishlarni bekor qilish
-- ROLLBACK;
```

## Keng tarqalgan xatolar

❌ **Noto'g'ri:** Ko'p bosqichli moliyaviy operatsiyalarni tranzaksiyasiz oddiy alohida so'rovlar sifatida yuborish (Server o'chsa, pul havoda qolib ketadi).
✅ **To'g'ri:** Bog'liq bir nechta o'zgartirishlar doimo `BEGIN ... COMMIT` blokiga olinishi shart.

## Mashq va vazifalar
1. **Oson:** `BEGIN` qilib yangi qator qo'shing, so'ngra `ROLLBACK` qilib qator bazaga yozilmaganini tekshiring.
2. **O'rtacha:** `SAVEPOINT` ning `ROLLBACK TO SAVEPOINT` bilan ishlashini amalda ko'rsating.
3. **Qiyin:** PostgreSQL da 4 ta izolyatsiya darajasini (Read Committed, Repeatable Read, Serializable) tushuntirib bering.

## Qisqacha xulosa
Tranzaksiyalar — ma'lumotlar yaxlitligi va ishonchliligining eng muhim kafolatidir."""
            },
            {
                "fn": "6.2-indekslar-va-explain-analyze.md",
                "name": "6.2. Indekslar (B-Tree, Hash, GIN, GiST) va EXPLAIN ANALYZE",
                "content": """# 6.2. Indekslar (B-Tree, Hash, GIN, GiST) va EXPLAIN ANALYZE

## Bu darsda nimalarni o'rganasiz
- Indeks nima va u qidiruvni qanday tezlashtiradi (Kitob mundarijasi misoli)
- Indeks turlari: B-Tree (Standart), Hash, GIN (JSON/Matn uchun), GiST
- `CREATE INDEX` va `DROP INDEX`
- So'rovlar tezligini o'lchash: `EXPLAIN ANALYZE`
- Seq Scan (Sekvensial skanerlash) vs Index Scan

## Nazariy qism
Indeks — jadvaldagi qatorlarni qidirishni millionlab marta tezlashtirish uchun mo'ljallangan maxsus yordamchi ma'lumotlar tuzilmasidir.

Indekssiz baza barcha 10 million qatorni birma-bir o'qib chiqadi (`Seq Scan` — sekin). Indeks bilan esa daraxt bo'ylab bir necha mikrosekundda topadi (`Index Scan` — juda tez).

## Amaliy misollar

```sql
-- 1. Standart B-Tree indeks yaratish
CREATE INDEX idx_talabalar_email ON talabalar(email);

-- 2. Bir nechta ustunga kompozit indeks
CREATE INDEX idx_xodimlar_bolim_maosh ON xodimlar(bolim_id, maosh);

-- 3. Qisman indeks (Partial Index — faqat faol foydalanuvchilar uchun)
CREATE INDEX idx_faol_foydalanuvchilar ON foydalanuvchilar(email) WHERE faolmi = TRUE;

-- 4. GIN indeks (JSONB ustunlar ichidan chaqmoqdek tez qidirish)
CREATE INDEX idx_tovarlar_xususiyatlar ON tovarlar USING GIN (xususiyatlar);

-- 5. So'rov samaradorligini tahlil qilish
EXPLAIN ANALYZE 
SELECT * FROM talabalar WHERE email = 'ali@example.com';
```

## Keng tarqalgan xatolar

❌ **Noto'g'ri:** Jadvaldagi har bitta ustunga ketma-ket indeks qo'yib tashlash.
✅ **To'g'ri:** Indekslar `SELECT` ni tezlashtiradi, lekin `INSERT/UPDATE/DELETE` ni sekinlashtiradi va diskda joy oladi. Faqat `WHERE`, `JOIN` va `ORDER BY` da ko'p ishlatiladigan ustunlarga indeks qo'yiladi.

## Mashq va vazifalar
1. **Oson:** `foydalanuvchilar` jadvalining `telefon` ustuniga indeks yarating.
2. **O'rtacha:** `EXPLAIN ANALYZE` natijasida `Execution Time` va `Planning Time` nima ekanini aniqlang.
3. **Qiyin:** GIN indeksining B-Tree indeksidan asosiy farqini tushuntiring.

## Qisqacha xulosa
To'g'ri qo'yilgan indekslar millionlab foydalanuvchili tizimlarda ham so'rovlarning bir zumda bajarilishini ta'minlaydi."""
            },
            {
                "fn": "6.3-triggerlar-va-avtomatlashtirish.md",
                "name": "6.3. Triggers (Triggerlar) va Avtomatlashtirish",
                "content": """# 6.3. Triggers (Triggerlar) va Avtomatlashtirish

## Bu darsda nimalarni o'rganasiz
- Trigger nima? (Baza hodisalariga avtomatik reaksiya)
- `BEFORE` va `AFTER` triggerlar
- `NEW` va `OLD` maxsus obyektlari
- Audit log (O'zgarishlar tarixini avtomatik yozib borish) yaratish

## Nazariy qism
**Trigger** — jadvalda ma'lum bir amal (`INSERT`, `UPDATE`, `DELETE`) sodir bo'lganda avtomatik ravishda ishga tushuvchi maxsus funksiyadir.

- `BEFORE`: Amal bajarilishidan oldin (Ma'lumotni tekshirish yoki o'zgartirish uchun).
- `AFTER`: Amal muvaffaqiyatli bajarilgandan keyin (Log yozish yoki boshqa jadvalni yangilash uchun).

## Amaliy misollar

```sql
-- 1. Avtomatik updated_at vaqtini yangilovchi trigger funksiyasi
CREATE OR REPLACE FUNCTION yangila_ozgarish_vaqti()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 2. Triggerni jadvalga bog'lash
CREATE TRIGGER trg_xodimlar_updated_at
BEFORE UPDATE ON xodimlar
FOR EACH ROW
EXECUTE FUNCTION yangila_ozgarish_vaqti();

-- 3. Audit Log triggeri (Kim qachon qaysi maoshni o'zgartirganini saqlash)
CREATE TABLE maosh_audit_log (
    xodim_id INT,
    eski_maosh NUMERIC,
    yangi_maosh NUMERIC,
    ozgargan_vaqt TIMESTAMPTZ DEFAULT NOW(),
    ozgartirgan_foydalanuvchi TEXT DEFAULT CURRENT_USER
);

CREATE OR REPLACE FUNCTION log_maosh_ozgarishi()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.maosh != NEW.maosh THEN
        INSERT INTO maosh_audit_log (xodim_id, eski_maosh, yangi_maosh)
        VALUES (OLD.id, OLD.maosh, NEW.maosh);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_maosh_audit
AFTER UPDATE ON xodimlar
FOR EACH ROW
EXECUTE FUNCTION log_maosh_ozgarishi();
```

## Keng tarqalgan xatolar

❌ **Noto'g'ri:** `BEFORE` trigger funksiyasida `RETURN NEW;` yozishni unutish (Bunday holda qator `NULL` bo'lib qoladi va jadvalga yozilmaydi).
✅ **To'g'ri:** `BEFORE INSERT/UPDATE` triggerlari doimo `RETURN NEW;` qaytarishi shart.

## Mashq va vazifalar
1. **Oson:** Har safar yangi xodim qo'shilganda konsolga xabar chiqaruvchi yoki log yozuvchi trigger tuzing.
2. **O'rtacha:** Foydalanuvchi o'chirilganda (`DELETE`), uning ma'lumotlarini `arxiv_foydalanuvchilar` jadvaliga ko'chirib qo'yuvchi `AFTER DELETE` triggeri yozing.
3. **Qiyin:** `OLD` va `NEW` o'zgaruvchilari qaysi amallarda mavjud bo'lishini jadvalda ko'rsating.

## Qisqacha xulosa
Triggerlar ma'lumotlar bazasi darajasida to'liq avtomatlashtirilgan xavfsiz audit va biznes-qoidalarni yaratishga xizmat qiladi."""
            },
            {
                "fn": "6.4-json-va-jsonb-bilan-ishlash.md",
                "name": "6.4. JSON va JSONB ma'lumotlar bilan ishlash",
                "content": """# 6.4. JSON va JSONB ma'lumotlar bilan ishlash

## Bu darsda nimalarni o'rganasiz
- Relyatsion bazada NoSQL imkoniyatlari
- `JSON` va `JSONB` farqlari (Binary JSON ustunligi)
- JSON operatorlari: `->`, `->>`, `#>`, `#>>`, `?`, `@>`
- JSONB ichidagi ma'lumotlarni qidirish va yangilash

## Nazariy qism
PostgreSQL o'zining ajoyib **JSONB** turi tufayli MongoDB kabi hujjatga yo'naltirilgan NoSQL bazalarining o'rnini to'liq bosa oladi.

| Operator | Maqsadi | Natija turi |
|---|---|---|
| `->` | Kalit bo'yicha qiymatni olish | `JSON/JSONB` |
| `->>` | Kalit bo'yicha qiymatni olish | Oddiy `TEXT` |
| `@>` | Chapdagi JSON o'ngdagini o'z ichiga oladimi | `BOOLEAN` |
| `?` | JSON da berilgan kalit mavjudmi | `BOOLEAN` |

## Amaliy misollar

```sql
-- 1. JSONB ustunli jadval yaratish
CREATE TABLE mahsulotlar_nosql (
    id SERIAL PRIMARY KEY,
    nomi VARCHAR(100),
    xususiyatlar JSONB
);

-- 2. JSON ma'lumotlarni kiritish
INSERT INTO mahsulotlar_nosql (nomi, xususiyatlar) VALUES 
('iPhone 15 Pro', '{"ram": "8GB", "xotira": "256GB", "ranglar": ["qora", "oq", "kok"], "kamera": {"asosiy": 48}}'),
('Samsung S24', '{"ram": "12GB", "xotira": "512GB", "ranglar": ["sariq", "qora"], "kamera": {"asosiy": 50}}');

-- 3. JSON ichidan ma'lumot o'qish (->> matn qaytaradi)
SELECT 
    nomi, 
    xususiyatlar->>'ram' AS ram_hajmi,
    xususiyatlar->'kamera'->>'asosiy' AS kamera_mp
FROM mahsulotlar_nosql;

-- 4. JSON ichidagi xususiyat bo'yicha filtrlash
SELECT * FROM mahsulotlar_nosql 
WHERE xususiyatlar->>'ram' = '8GB';

-- 5. JSONB ichida 'qora' rangi bor mahsulotlarni topish (@> operatori)
SELECT * FROM mahsulotlar_nosql 
WHERE xususiyatlar @> '{"ranglar": ["qora"]}';
```

## Keng tarqalgan xatolar

❌ **Noto'g'ri:** JSON qiymatni solishtirishda `->` operatoridan foydalanish (Chunki u qo'shtirnoqli `\"8GB\"` JSON qaytaradi va oddiy `'8GB'` ga teng bo'lmaydi).
✅ **To'g'ri:** Matnli solishtirish uchun doimo **`->>`** operatoridan foydalaning.

## Mashq va vazifalar
1. **Oson:** Foydalanuvchi sozlamalari (`{"til": "uz", "tema": "dark"}`) bo'lgan JSONB ustunli jadval tuzing.
2. **O'rtacha:** Faqat `tema` si `'dark'` bo'lgan foydalanuvchilarni toping.
3. **Qiyin:** JSONB ustuniga GIN indeks qo'yish sintaksisini yozing.

## Qisqacha xulosa
JSONB reliesiya va NoSQL moslashuvchanligini birlashtirgan eng qudratli zamonaviy xususiyatdir."""
            },
            {
                "fn": "6.5-foydalanuvchilar-rollar-va-huquqlar.md",
                "name": "6.5. Foydalanuvchilar, rollar va huquqlar (GRANT, REVOKE, pg_hba.conf)",
                "content": """# 6.5. Foydalanuvchilar, rollar va huquqlar (GRANT, REVOKE, pg_hba.conf)

## Bu darsda nimalarni o'rganasiz
- Rollar va Foydalanuvchilar (`ROLE` vs `USER`)
- `CREATE USER` va `CREATE ROLE`
- Huquqlar berish (`GRANT`) va qaytarib olish (`REVOKE`)
- Xavfsizlik konfiguratsiyasi: `pg_hba.conf` fayli

## Nazariy qism
PostgreSQL da xavfsizlik va ruxsatlar **Role** tushunchasi orqali boshqariladi.

### Huquq turlari:
- `SELECT`, `INSERT`, `UPDATE`, `DELETE` — Jadvallar ustida amallar
- `ALL PRIVILEGES` — Barcha huquqlar

## Amaliy misollar

```sql
-- 1. Yangi loyiha foydalanuvchisini yaratish (Parol bilan)
CREATE USER mening_loyiham WITH PASSWORD 'kuchli_parol_123';

-- 2. Yangi baza yaratish va egasini belgilash
CREATE DATABASE loyiha_db OWNER mening_loyiham;

-- 3. Faqat o'qish huquqiga ega tahlilchi roli (Read-only user)
CREATE USER analitik WITH PASSWORD 'analitik_parol';
GRANT CONNECT ON DATABASE loyiha_db TO analitik;
GRANT USAGE ON SCHEMA public TO analitik;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO analitik;

-- 4. Huquqni bekor qilish
REVOKE DELETE ON ALL TABLES IN SCHEMA public FROM analitik;
```

### pg_hba.conf fayli (Host-Based Authentication)
PostgreSQL serveriga kim qayerdan qanday ulanishini belgilaydi:
```text
# TYPE  DATABASE        USER            ADDRESS                 METHOD
local   all             postgres                                peer
host    all             all             127.0.0.1/32            scram-sha-256
host    loyiha_db       mening_loyiham  0.0.0.0/0               scram-sha-256
```

## Keng tarqalgan xatolar

❌ **Noto'g'ri:** Veb-sayt yoki botni har doim superuser `postgres` nomidan ulab ishlatish.
✅ **To'g'ri:** Har bir loyiha uchun alohida cheklangan huquqli maxsus `user` yarating.

## Mashq va vazifalar
1. **Oson:** `junior_dev` nomli foydalanuvchi yarating.
2. **O'rtacha:** Unga faqat `SELECT` va `INSERT` huquqini bering, `DELETE` qilishni taqiqlang.
3. **Qiyin:** `pg_hba.conf` da `md5`, `scram-sha-256` va `trust` usullarining farqini tushuntiring.

## Qisqacha xulosa
To'g'ri sozlangan rollar va minimal huquqlar printsipi ma'lumotlar bazasi xavfsizligining garovidir."""
            },
            {
                "fn": "6.6-zaxira-nusxa-pg-dump-va-tiklash.md",
                "name": "6.6. Zaxira nusxa olish va tiklash (pg_dump, pg_restore)",
                "content": """# 6.6. Zaxira nusxa olish va tiklash (pg_dump, pg_restore)

## Bu darsda nimalarni o'rganasiz
- Backup (Zaxira nusxa) olishning hayotiy ahamiyati
- `pg_dump` — Bitta bazaning zaxira nusxasini olish
- `pg_dumpall` — Butun serverni zaxiralash
- `psql` va `pg_restore` orqali bazani qayta tiklash
- Avtomatik kunlik zaxiralash (Cron job)

## Nazariy qism
Har qanday professional dasturchi va tizim ma'muri uchun eng muhim qoida — muntazam zaxira nusxa (backup) olishdir.

| Utilit | Vazifasi | Chiqish formati |
|---|---|---|
| `pg_dump` | Bitta ma'lumotlar bazasi zaxirasi | `.sql` (matn) yoki `.dump/.tar` (siqilgan) |
| `pg_dumpall` | Barcha bazalar, foydalanuvchilar va rollar | `.sql` matn |
| `pg_restore` | Custom / Directory formatidagi zaxiralarni tiklash | Baza |

## Amaliy misollar

```bash
# 1. Oddiy SQL formatida zaxira olish (Gzip bilan siqish)
sudo -u postgres pg_dump loyiha_db | gzip > /var/backups/loyiha_$(date +%F).sql.gz

# 2. Siqilgan custom formatda olish (Tavsiya etiladi - eng tez va ixcham)
sudo -u postgres pg_dump -Fc loyiha_db > /var/backups/loyiha.dump

# 3. Zaxiradan tiklash (SQL matn faylidan)
sudo -u postgres psql -d yangi_db < /var/backups/loyiha.sql

# 4. Custom formatdan tiklash (pg_restore orqali)
sudo -u postgres pg_restore -d yangi_db /var/backups/loyiha.dump

# 5. Butun serverni (barcha userlar bilan) zaxiralash
sudo -u postgres pg_dumpall | gzip > /var/backups/all_databases_$(date +%F).sql.gz
```

### Avtomatik kunlik zaxiralash (Cron):
`crontab -e` ga quyidagi qator qo'shiladi (Har kecha soat 03:00 da):
```bash
0 3 * * * sudo -u postgres pg_dump loyiha_db | gzip > /var/backups/db_$(date +\\%Y-\\%m-\\%d).sql.gz
```

## Keng tarqalgan xatolar

❌ **Noto'g'ri:** Zaxira olib qo'yib, uni hech qachon test bazada qayta tiklab ko'rmaslik (Zaxira fayli buzilgan bo'lsa, avariya paytida fojia yuz beradi).
✅ **To'g'ri:** Olingan zaxira nusxalarni vaqti-vaqti bilan alohida sinov serverida tiklab, ishlab turganini tekshirib turing.

## Mashq va vazifalar
1. **Oson:** O'z bazangizning zaxira nusxasini `pg_dump` yordamida `.sql` faylga saqlang.
2. **O'rtacha:** Yangi bo'sh baza yarating va boya olingan zaxirani unga muvaffaqiyatli tiklang.
3. **Qiyin:** Faqat bitta jadvalning o'zinigina zaxiraga olish buyrug'ini yozing (`-t` parametri).

## Qisqacha xulosa
`pg_dump` va `pg_restore` — ma'lumotlar yo'qolishidan himoyalovchi eng ishonchli va professional vositalardir."""
            }
        ]
    }
]

def main():
    print("PostgreSQL darsligi fayllarini yaratish boshlandi...")
    total_lessons = 0

    # Create mundarija
    mundarija_lines = [
        "# PostgreSQL darsligi — Barcha mavzular (to'liq, 7 ta bo'lim, 36 ta dars)",
        "",
        "_Ushbu darslik noldan (PostgreSQL nima ekanidan) tortib, eng ilg'or DDL/DML, Murakkab JOINlar, CTE, Window Functions, Indekslar, JSONB, Triggerlar va Xavfsizlikkacha bo'lgan to'liq yo'lni qamrab oladi._",
        "",
        "---",
        ""
    ]

    for chap in CHAPTERS:
        chap_dir = os.path.join(BASE_DIR, chap["dir"])
        os.makedirs(chap_dir, exist_ok=True)
        mundarija_lines.append(f"## {chap['title']}\n")
        mundarija_lines.append("| № | Mavzu | Fayl |")
        mundarija_lines.append("|---|---|---|")

        for lesson in chap["lessons"]:
            fn = lesson["fn"]
            fp = os.path.join(chap_dir, fn)
            with open(fp, "w", encoding="utf-8") as f:
                f.write(lesson["content"].strip() + "\n")
            
            num_part = lesson["name"].split()[0]
            title_part = " ".join(lesson["name"].split()[1:])
            mundarija_lines.append(f"| {num_part} | {title_part} | {fn} |")
            total_lessons += 1
            print(f"  ✅ Yaratildi: {chap['dir']}/{fn}")

        mundarija_lines.append("")

    mundarija_lines.append("---")
    mundarija_lines.append(f"\n**Jami: {total_lessons} ta dars** (0.1 dan 6.6 gacha) to'liq, mukammal va professional formatda yaratildi.")

    mundarija_path = os.path.join(BASE_DIR, "00-postgresql-darslik-mundarija.md")
    with open(mundarija_path, "w", encoding="utf-8") as f:
        f.write("\n".join(mundarija_lines) + "\n")

    print(f"\n🎉 Muvaffaqiyatli yakunlandi! Jami {total_lessons} ta dars va mundarija fayli yaratildi.")

if __name__ == '__main__':
    main()
