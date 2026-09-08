# -*- coding: utf-8 -*-
"""Prisedaniye (squat) — og'irlikdan O'Z VAZNI bilan TAKRORGA o'tkaziladi.

NOMI ATAYLAB O'ZGARMAYDI: `activity_log` da shu nom bilan yozuv bor va
Boostday↔Sport bog'lanishi ham nom bo'yicha ishlaydi — nom o'zgarsa
tarix uzilib qolardi.
"""
import sys
sys.path.insert(0, '/opt/yordamchi/Yordamchisayt/backend_py')
from app import db

EX_ID = 58

DESC = """**Ishlaydigan mushaklar:** to'rt boshli son (kvadritseps), dumba, orqa son, bel (stabilizator)

## Bajarish
1. Oyoq yelka kengligida, panja biroz tashqariga qaragan.
2. Qo'lni oldinga cho'zing yoki ko'krak oldida qovushtiring — muvozanat uchun.
3. Chuqur nafas olib qorinni qattiq qiling.
4. Chanoqni orqaga surib pastga cho'king — **tizza panja yo'nalishida** harakatlansin.
5. Son yerga parallel yoki pastroq bo'lsin.
6. Tovon bilan yerni itarib turing, tepada dumbani siqing.

## Tipik xatolar
- Tovonni yerdan uzish
- Tizzani ichkariga qulatish
- Belni yumaloqlash (butt wink)
- Yarim cho'kish — eng ko'p uchraydigan xato

## Nafas
Pastga tushayotganda nafasni ushlang, ko'tarilgach chiqaring.

## Og'irlashtirish (o'z vazni bilan)
Takror ko'payib mashq yengil kelsa, og'irlik qo'shish shart emas —
harakatni QIYINLASHTIRING:
1. **Sekin tushish** — pastga 3-4 soniyada
2. **Pastda ushlab turish** — eng past nuqtada 2-3 soniya
3. **Bolgar cho'kishi** — orqa oyoq balandlikda (bir oyoqqa yuk)
4. **Sakrab cho'kish** — portlovchi kuch uchun
5. **Pistolet (bir oyoqda)** — eng og'iri

> **Maslahat:** Chuqurlik cheklangan bo'lsa — bu ko'pincha **to'piq harakatchanligi** muammosi. Tovon ostiga kichik balandlik qo'yib ko'ring.

> **Eslatma:** Bu mashq o'z vazni bilan bajariladi — o'sish og'irlikda emas, TAKRORDA hisoblanadi."""


def main():
    before = db.fetch_one(
        "SELECT name, progress_type, weight, increase_amount, set_count, rep_count "
        "FROM sport_exercises WHERE id = :i", {"i": EX_ID})
    if not before:
        print("XATO: id", EX_ID, "topilmadi"); return
    print("OLDIN:", dict(before))

    db.execute(
        "UPDATE sport_exercises SET progress_type = 'reps', weight = 0, "
        "increase_amount = 2, set_count = 4, rep_count = 20, description = :d, "
        "updated_at = CURRENT_TIMESTAMP WHERE id = :i",
        {"i": EX_ID, "d": DESC},
    )

    after = db.fetch_one(
        "SELECT name, progress_type, weight, increase_amount, set_count, rep_count "
        "FROM sport_exercises WHERE id = :i", {"i": EX_ID})
    print("KEYIN:", dict(after))

    # Sayt yangilanishni sezishi uchun sinxronlash belgisini yangilaymiz
    row = db.fetch_one("SELECT owner_type, owner_key FROM sport_exercises WHERE id = :i", {"i": EX_ID})
    db.execute(
        "INSERT INTO sport_sync_meta (owner_type, owner_key, meta_key, meta_value) "
        "VALUES (:ot, :ok, 'last_global_update', to_char(clock_timestamp(), 'YYYY-MM-DD HH24:MI:SS.US')) "
        "ON CONFLICT (owner_type, owner_key, meta_key) DO UPDATE "
        "SET meta_value = to_char(clock_timestamp(), 'YYYY-MM-DD HH24:MI:SS.US'), "
        "updated_at = CURRENT_TIMESTAMP",
        {"ot": row["owner_type"], "ok": row["owner_key"]},
    )
    print("sinxronlash belgisi yangilandi")


if __name__ == "__main__":
    main()
