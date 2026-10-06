# -*- coding: utf-8 -*-
"""Press kategoriyasiga "Rolik" (ab wheel) mashqini qo'shadi + video havolasi.

Qayta ishga tushirilsa xavfsiz: mashq ham, media ham nusxalanmaydi.
"""
import sys
sys.path.insert(0, '/opt/yordamchi/Yordamchisayt/backend_py')
from app import db

OT, OK, CAT = 'global', 'shared', 'press'

NAME = "Rolik (ab wheel)"
DESC = """**Ishlaydigan mushaklar:** to'g'ri qorin, ko'ndalang qorin, keng orqa mushagi, yelka, bel stabilizatorlari

## Bajarish
1. Tizzada turing (tizza ostiga yumshoq narsa qo'ying).
2. Rolikni yelka kengligida, tizza oldida ushlang.
3. Qorinni siqing, dumbani biroz ichkariga buring — **bel yumaloqlanmasin ham, egilmasin ham**.
4. Rolikni oldinga sekin yumalatib, tanani cho'zing.
5. Bel egila boshlagan nuqtada TO'XTANG — bu sizning hozirgi chegarangiz.
6. Qorin kuchi bilan qaytib keling.

## Tipik xatolar
- **Belni solintirish** — eng xavfli xato, bel og'rig'iga olib keladi
- Juda uzoqqa yumalatish (kuch yetmagan holda)
- Qo'l kuchi bilan tortish, qorinni ishlatmaslik
- Tez va nazoratsiz harakat

> **Maslahat:** Boshlashda devordan 30-40 sm narida turing — rolik devorga tegib to'xtaydi va uzoqqa ketib qolmaysiz. Kuch ortgan sari devordan uzoqlashing.

> **Diqqat:** Beli og'riydiganlar avval `Planka` va `O'lik qo'ng'iz` bilan poydevor yarating. Rolik — qorin mashqlarining eng og'irlaridan."""

VIDEO = "https://www.youtube.com/watch?v=ikkOq5mHaho"
IMAGE = "assets/img/sport/ex/press-1.webp"


def main():
    row = db.fetch_one(
        "SELECT id FROM sport_exercises WHERE owner_type=:ot AND owner_key=:ok "
        "AND category=:c AND lower(trim(name))=lower(trim(:n)) AND is_deleted=0 LIMIT 1",
        {"ot": OT, "ok": OK, "c": CAT, "n": NAME},
    )
    if row:
        ex_id = int(row["id"])
        print("Mashq allaqachon bor, id =", ex_id)
    else:
        ex_id = db.execute_returning_id(
            "INSERT INTO sport_exercises (owner_type, owner_key, category, name, description, "
            "weight, increase_amount, set_count, rep_count, progress_type, progress_mode, is_deleted) "
            "VALUES (:ot,:ok,:c,:n,:d, 0, 1, 3, 8, 'reps', 'manual', 0)",
            {"ot": OT, "ok": OK, "c": CAT, "n": NAME, "d": DESC},
        )
        print("Mashq qo'shildi, id =", ex_id)

    for path, ftype in ((IMAGE, "image"), (VIDEO, "video")):
        have = db.fetch_one(
            "SELECT id FROM sport_media WHERE exercise_id=:e AND file_path=:p LIMIT 1",
            {"e": ex_id, "p": path},
        )
        if have:
            print("  media bor:", path)
            continue
        db.execute(
            "INSERT INTO sport_media (exercise_id, file_path, file_type, sort_order) "
            "VALUES (:e,:p,:t,0)", {"e": ex_id, "p": path, "t": ftype},
        )
        print("  media qo'shildi:", path)

    n = db.fetch_one(
        "SELECT count(*) c FROM sport_exercises WHERE owner_type=:ot AND owner_key=:ok "
        "AND category=:cat AND is_deleted=0", {"ot": OT, "ok": OK, "cat": CAT})["c"]
    print("Jami 'press' mashqlari:", n)


if __name__ == "__main__":
    main()
