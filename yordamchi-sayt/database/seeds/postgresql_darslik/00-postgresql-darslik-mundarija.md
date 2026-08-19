# PostgreSQL darsligi — Barcha mavzular (to'liq, 7 ta bo'lim, 36 ta dars)

_Ushbu darslik noldan (PostgreSQL nima ekanidan) tortib, eng ilg'or DDL/DML, Murakkab JOINlar, CTE, Window Functions, Indekslar, JSONB, Triggerlar va Xavfsizlikkacha bo'lgan to'liq yo'lni qamrab oladi._

---

## 00. Kirish va O'rnatish

| № | Mavzu | Fayl |
|---|---|---|
| 0.1. | PostgreSQL nima, tarixi va arxitekturasi | 0.1-postgresql-nima-tarixi-arxitekturasi.md |
| 0.2. | PostgreSQL o'rnatish va psql bilan ishlash (Ubuntu & Docker) | 0.2-postgresql-ornatish-psql-ubuntu-docker.md |
| 0.3. | pgAdmin 4 va DBeaver vositalarini sozlash | 0.3-pgadmin-dbeaver-grafik-interfeys.md |

## 01. Baza va Jadvallar (DDL)

| № | Mavzu | Fayl |
|---|---|---|
| 1.1. | CREATE DATABASE va DROP DATABASE (Baza boshqaruvi) | 1.1-create-drop-database.md |
| 1.2. | Ma'lumot turlari (INTEGER, VARCHAR, TEXT, BOOLEAN, DATE, JSONB) | 1.2-malumot-turlari-data-types.md |
| 1.3. | CREATE TABLE va DROP TABLE (Jadval yaratish va o'chirish) | 1.3-create-drop-table.md |
| 1.4. | Cheklovlar (Constraints: PRIMARY KEY, NOT NULL, UNIQUE, CHECK, DEFAULT) | 1.4-constraints-cheklovlar.md |
| 1.5. | ALTER TABLE (Ustun qo'shish, o'chirish va nomini o'zgartirish) | 1.5-alter-table-ustunlarni-boshqarish.md |
| 1.6. | Bog'lanishlar va Tashqi kalit (FOREIGN KEY, ON DELETE CASCADE / SET NULL) | 1.6-foreign-key-boshqa-jadvallar-boglanish.md |

## 02. Ma'lumotlar bilan ishlash (DML)

| № | Mavzu | Fayl |
|---|---|---|
| 2.1. | INSERT INTO — Qator qo'shish va ko'p qatorli kiritish | 2.1-insert-into-qator-qoshish.md |
| 2.2. | SELECT asoslari va ustun tanlash | 2.2-select-asoslari.md |
| 2.3. | WHERE filtrlash va solishtirish operatorlari | 2.3-where-filtr-solishtirish.md |
| 2.4. | Mantiqiy operatorlar (AND, OR, NOT, IN, BETWEEN, LIKE, ILIKE) | 2.4-mantiqiy-operatorlar-and-or-in-like.md |
| 2.5. | Tartiblash va Cheklash (ORDER BY, LIMIT, OFFSET, FETCH) | 2.5-order-by-limit-offset.md |
| 2.6. | UPDATE va DELETE (Ma'lumotlarni yangilash va o'chirish) | 2.6-update-delete-ozgartirish-ochirish.md |
| 2.7. | NULL qiymatlar bilan ishlash (IS NULL, IS NOT NULL, COALESCE) | 2.7-null-qiymatlar-bilan-ishlash.md |

## 03. Agregatsiya va Guruhlash

| № | Mavzu | Fayl |
|---|---|---|
| 3.1. | Agregat funksiyalar (COUNT, SUM, AVG, MIN, MAX) | 3.1-agregat-funksiyalar-count-sum-avg.md |
| 3.2. | GROUP BY — Guruhlash asoslari | 3.2-group-by-guruhlash.md |
| 3.3. | HAVING — Guruhlangan ma'lumotlarni filtrlash | 3.3-having-guruhlarni-filtrlash.md |
| 3.4. | DISTINCT va SELECT DISTINCT ON | 3.4-distinct-unikal-qiymatlar.md |

## 04. Jadvallarni Birlashtirish (JOINS) va To'plamlar

| № | Mavzu | Fayl |
|---|---|---|
| 4.1. | INNER JOIN — Mos keluvchi qatorlarni birlashtirish | 4.1-inner-join-mos-birlashtirish.md |
| 4.2. | LEFT JOIN va RIGHT JOIN (Tashqi birlashuv) | 4.2-left-right-join-tashqi-birlashuv.md |
| 4.3. | FULL OUTER JOIN va CROSS JOIN | 4.3-full-outer-join-cross-join.md |
| 4.4. | ANTI JOIN va SEMI JOIN tushunchasi | 4.4-anti-join-va-semi-join.md |
| 4.5. | To'plam amallari (UNION, UNION ALL, INTERSECT, EXCEPT) | 4.5-toplam-amallari-union-intersect-except.md |

## 05. Ichki so'rovlar, Funksiyalar va View

| № | Mavzu | Fayl |
|---|---|---|
| 5.1. | Subqueries (Ichki so'rovlar: WHERE, FROM, SELECT) | 5.1-subqueries-ichki-sorovlar.md |
| 5.2. | Common Table Expressions (WITH / CTE) va Rekursiv CTE | 5.2-cte-with-va-rekursiv-cte.md |
| 5.3. | Window Functions (ROW_NUMBER, RANK, DENSE_RANK, OVER, PARTITION BY) | 5.3-window-functions-oynali-funksiyalar.md |
| 5.4. | View va Materialized View | 5.4-view-va-materialized-view.md |
| 5.5. | Foydalanuvchi funksiyalari va Stored Procedures (PL/pgSQL) | 5.5-protseduralar-va-funksiyalar-plpgsql.md |

## 06. Tranzaksiyalar, Indekslar va Xavfsizlik

| № | Mavzu | Fayl |
|---|---|---|
| 6.1. | Tranzaksiyalar va ACID (BEGIN, COMMIT, ROLLBACK, SAVEPOINT) | 6.1-tranzaksiyalar-va-acid.md |
| 6.2. | Indekslar (B-Tree, Hash, GIN, GiST) va EXPLAIN ANALYZE | 6.2-indekslar-va-explain-analyze.md |
| 6.3. | Triggers (Triggerlar) va Avtomatlashtirish | 6.3-triggerlar-va-avtomatlashtirish.md |
| 6.4. | JSON va JSONB ma'lumotlar bilan ishlash | 6.4-json-va-jsonb-bilan-ishlash.md |
| 6.5. | Foydalanuvchilar, rollar va huquqlar (GRANT, REVOKE, pg_hba.conf) | 6.5-foydalanuvchilar-rollar-va-huquqlar.md |
| 6.6. | Zaxira nusxa olish va tiklash (pg_dump, pg_restore) | 6.6-zaxira-nusxa-pg-dump-va-tiklash.md |

---

**Jami: 36 ta dars** (0.1 dan 6.6 gacha) to'liq, mukammal va professional formatda yaratildi.
