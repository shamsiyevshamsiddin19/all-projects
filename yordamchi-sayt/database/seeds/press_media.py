# -*- coding: utf-8 -*-
"""Press mashqlariga YouTube darsligi va rasm (video old ko'rinishi) qo'shadi.

Rasm sifatida videoning O'Z old ko'rinishi (img.youtube.com/vi/<id>/hqdefault.jpg)
ishlatiladi — u har doim aynan o'sha mashqni ko'rsatadi, chunki video bilan
bitta manbadan keladi. Mashqqa mos kelmaydigan umumiy "zal fotosurati"
qo'yishdan ko'ra to'g'riroq.

Barcha video ID lari oEmbed orqali bittalab tekshirilgan (mavjud + mavzuga mos).
Qayta ishga tushirilsa xavfsiz — nusxa qo'shilmaydi.
"""
import sys
sys.path.insert(0, '/opt/yordamchi/Yordamchisayt/backend_py')
from app import db

OT, OK, CAT = 'global', 'shared', 'press'

# mashq nomi -> YouTube video ID
VIDEOS = {
    "Planka":                      "A2b2EmIg0dA",  # E3 Rehab
    "Yon planka":                  "iNbH7_edNI8",  # Runna
    "Vakuum":                      "N9msEniBkbU",  # K's Perfect Fitness TV
    "Krunch":                      "GWIEON0VSaY",  # Glamrs
    "Velosiped krunchi":           "1we3bh9uhqY",  # Tone and Tighten
    "Oyoq ko'tarish (yotib)":      "sY2ZgV2Sj_s",  # FIT.nl
    "Turnikda oyoq ko'tarish":     "EYe6dc_i4L0",  # Zack Henderson
    "Rus burilishi":               "H4tMFJoyAd8",  # Your House Fitness
    "Alpinist":                    "K3Xt4QH4b-U",  # VIGEO
    "Qayiqcha (hollow hold)":      "01iEknlpnVY",  # Adarsh Williams
    "O'lik qo'ng'iz (dead bug)":   "bxn9FBrt4-A",  # NASM
    "Yonga egilish (og'irliksiz)": "wY9nQ-yfRwo",  # Runna
}


def add_media(ex_id, path, ftype):
    have = db.fetch_one(
        "SELECT id FROM sport_media WHERE exercise_id=:e AND file_path=:p LIMIT 1",
        {"e": ex_id, "p": path},
    )
    if have:
        return False
    db.execute(
        "INSERT INTO sport_media (exercise_id, file_path, file_type, sort_order) "
        "VALUES (:e,:p,:t,:s)",
        {"e": ex_id, "p": path, "t": ftype, "s": 0 if ftype == "image" else 1},
    )
    return True


def main():
    added = skipped = missing = 0
    for name, vid in VIDEOS.items():
        row = db.fetch_one(
            "SELECT id FROM sport_exercises WHERE owner_type=:ot AND owner_key=:ok "
            "AND category=:c AND lower(trim(name))=lower(trim(:n)) AND is_deleted=0 LIMIT 1",
            {"ot": OT, "ok": OK, "c": CAT, "n": name},
        )
        if not row:
            print("  ! MASHQ TOPILMADI:", name)
            missing += 1
            continue
        ex_id = int(row["id"])
        img = "https://img.youtube.com/vi/%s/hqdefault.jpg" % vid
        vurl = "https://www.youtube.com/watch?v=%s" % vid
        a = add_media(ex_id, img, "image")
        b = add_media(ex_id, vurl, "video")
        if a or b:
            print("  + %-30s %s" % (name, vid))
            added += 1
        else:
            print("    %-30s (allaqachon bor)" % name)
            skipped += 1

    print()
    print("qo'shildi: %d,  o'tkazildi: %d,  topilmadi: %d" % (added, skipped, missing))
    n = db.fetch_one(
        "SELECT count(*) c FROM sport_exercises e LEFT JOIN sport_media m ON m.exercise_id=e.id "
        "WHERE e.category='press' AND e.is_deleted=0 AND m.id IS NULL")["c"]
    print("press'da hali mediasiz mashq:", n)


if __name__ == "__main__":
    main()
