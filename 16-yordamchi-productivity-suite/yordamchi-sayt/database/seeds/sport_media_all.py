# -*- coding: utf-8 -*-
"""Tiklangan sport mashqlariga YouTube darsligi va rasm qo'shadi.

`press_media.py` bilan BIR XIL yondashuv (o'sha fayldagi izohga qarang):
rasm sifatida videoning O'Z old ko'rinishi ishlatiladi — u har doim aynan
o'sha mashqni ko'rsatadi, chunki video bilan bitta manbadan keladi.
Mashqqa mos kelmaydigan umumiy "zal fotosurati" qo'yishdan to'g'riroq.

Barcha 90 ta video ID si YouTube qidiruvidan olinib, oEmbed orqali
BITTALAB tekshirilgan (mavjud + sarlavhasi mavzuga mos).
Qayta ishga tushirilsa xavfsiz — nusxa qo'shilmaydi.

`press` bu yerda YO'Q — u `press_media.py` bilan to'ldirilgan.
"""
import sys
sys.path.insert(0, '/opt/yordamchi/Yordamchisayt/backend_py')
from app import db

OT, OK = 'global', 'shared'

# kategoriya -> { mashq nomi: (video ID, kanal) }
VIDEOS = {
'turnik': {
  "Pull up":                     ("eGo4IYlbE5g",  "Calisthenicmovement"),
  "Klassik tortilish":           ("iBtL9nX2qOs",  "CHRIS HERIA"),
  "Chin-up (teskari ushlash)":   ("TaP1Znk_X9c",  "Micha Schulz"),
  "Keng ushlab tortilish":       ("bHC16skSN6Q",  "Alex Leonidas"),
  "Avstraliya tortilishi":       ("5W8F6MzZ8Rk",  "Andrew Alinda"),
  "Turnikda osilib turish":      ("ShkBXOGK7A8",  "FitnessFAQs"),
},
'brus': {
  "Brusda cho'kish":                 ("2z8JmcrW-As",  "Calisthenicmovement"),
  "Brusda oyoq ko'tarish":           ("S2QVHl6DoNo",  "Simonster Strength"),
  "Brusda tayanib turish":           ("_vPttkLHZMw",  "Calixpert"),
  "Teskari cho'kish (skameykada)":   ("0326dy_-CzM",  "LIVESTRONG"),
  "Brusda sekin tushish":            ("l41SoWZiowI",  "FitnessFAQs"),
},
'ajimaniya': {
  "Klassik ajimaniya":           ("IODxDxX7oi4",  "Calisthenicmovement"),
  "Keng qo'l bilan ajimaniya":   ("QwTW7DXBw5w",  "Upright Health"),
  "Olmos (tor) ajimaniya":       ("kGhDnFwMY3E",  "Minus The Gym"),
  "Oyoq balandda ajimaniya":     ("O7dVvwEK9J4",  "The Health Alchemist"),
  "Pike ajimaniya":              ("4AQA40fqMa0",  "Rajan Sharma"),
  "Sakrab ajimaniya":            ("FRo3b_Pfw3M",  "Howcast"),
},
'full': {
  "Burpi":                         ("NCqbpkoiyXE",  "Nuffield Health"),
  "Og'irliksiz o'tirib turish":    ("8uoaYwS6iFM",  "IU Health"),
  "Vipad (lunge)":                 ("ASdqJoDPMHA",  "Fitness For Transformation"),
  "Alpinist (mountain climber)":   ("cnyTQDSE884",  "Well+Good"),
  "Sakrab o'tirib turish":         ("BRfxI2Es2lE",  "PureGym"),
  "Ayiq yurishi (bear crawl)":     ("Ee1BQNI6zN4",  "BSR Physical Therapy"),
},
'grud': {
  "Yotib shtanga ko'tarish":         ("4Y2ZdHCOXok",  "Jeremy Ethier"),
  "Qiya skameykada ko'tarish":       ("SrqOu55lrYU",  "ScottHermanFitness"),
  "Gantel bilan yoyish":             ("Nhvz9EzdJ4U",  "PureGym"),
  "Ko'krak uchun brusda cho'kish":   ("2z8JmcrW-As",  "Calisthenicmovement"),
  "Og'irlik bilan ajimaniya":        ("xZRBXI7we44",  "Andrew Alinda"),
},
'bitseps': {
  "Shtanga bilan bukish":                  ("ZQWL7omZh94",  "Testosterone Nation"),
  "Gantel bilan navbatma-navbat bukish":   ("sAq_ocpRh_I",  "ScottHermanFitness"),
  "Bolg'a (hammer) bukish":                ("8XLxfXROrTo",  "ScottHermanFitness"),
  "Skott skameykasida bukish":             ("9WDQqgiwQEY",  "One Minute Tutorial"),
  "Turnikda teskari ushlab tortilish":     ("dYDJpuDiJGc",  "ATHLEAN-X™"),
},
'triseps': {
  "Fransuzcha ko'tarish":              ("tj81tVq3wLo",  "FIT.nl"),
  "Blokda ip bilan tushirish":         ("-xa-6cQaZKY",  "Renaissance Periodization"),
  "Olmos ajimaniya":                   ("8wobhrjg_yg",  "Brian Syuki "),
  "Skameykada teskari cho'kish":       ("0326dy_-CzM",  "LIVESTRONG"),
  "Bosh orqasidan gantel ko'tarish":   ("-Vyt2QdsR7E",  "ScottHermanFitness"),
},
'orqa': {
  "Stanovoy tortish (deadlift)":       ("XxWcirHIwVo",  "Jeremy Ethier"),
  "Egilib shtanga tortish":            ("qXrTDQG1oUQ",  "Moorefitcoach"),
  "Yuqori blok tortish":               ("SALxEARiMkw",  "ATHLEAN-X™"),
  "Gorizontal blok tortish":           ("vwHG9Jfu4sw",  "Max Euceda"),
  "Gantel bilan bir qo'lda tortish":   ("gfUg6qWohTk",  "ATHLEAN-X™"),
  "Giperekstenziya":                   ("H8Swl1N-uis",  "Squat University"),
},
'yelka': {
  "Armeycha ko'tarish":           ("KP1sYz2VICk",  "Max Euceda"),
  "Gantel bilan yon ko'tarish":   ("PzsMitRdI_8",  "Max Euceda"),
  "Old ko'tarish":                ("-t7fuZ0KhDA",  "ScottHermanFitness"),
  "Egilib yon ko'tarish":         ("p1yQnTNE808",  "ChadMollickDotCom"),
  "Shrug (trapetsiya)":           ("zfAHfyTB_Ao",  "Renaissance Periodization"),
  "Arnold press":                 ("ris9tKqMwgU",  "ATHLEAN-X™"),
},
'oyoq': {
  "Shtanga bilan o'tirib turish":   ("gcNh17Ckjgg",  "Jeremy Ethier"),
  "Og'irliksiz chuqur o'tirish":    ("Zc7c-N2z3OY",  "noBODYKNOWme Strength & Mobility Trainer 4 Humans"),
  "Bolg'archa vipad":               ("vgn7bSXkgkA",  "Denvyr | Tall Girl Nutritionist"),
  "Rumin tortishi":                 ("5zmlnbWb-g4",  "ATHLEAN-X™"),
  "Boldir ko'tarish":               ("k8ipHzKeAkQ",  "Children's Hospital Colorado"),
  "Devor bo'ylab o'tirish":         ("cWTZ8Am1Ee0",  "Medbridge"),
},
'kardio': {
  "Yugurish":                   ("_kGESn8ArrU",  "Global Triathlon Network"),
  "Arqon sakrash":              ("IFgQfVQT_68",  "Kyle Easter"),
  "Interval yugurish (HIIT)":   ("2YogM9wXAJg",  "Mark's Daily Apple"),
  "Velosiped":                  ("c0gw_UG1zZM",  "Global Cycling Network"),
  "Tez yurish":                 ("EpvXcGONfkk",  "SIKANA English"),
},
'armwresling': {
  "Bilak bukish (wrist curl)":        ("3VLTzIrnb5g",  "PureGym"),
  "Teskari bilak bukish":             ("FW7URAaC-vE",  "ScottHermanFitness"),
  "Bolg'a bukish":                    ("BRVDS6HVR9Q",  "Buff Dudes Workouts"),
  "Pronatsiya (bilakni burash)":      ("orzxvTg8yPQ",  "Voice of Armwrestling"),
  "Ushlash kuchi (grip hold)":        ("9WL_1dOt82w",  "The Red Delta Project"),
  "Stol ustida armrestling mashqi":   ("Y28nhJjHzc0",  "Voice of Armwrestling"),
},
'futbol': {
  "Dribbling (To'pni olib yurish)":    ("vnngDOCy9C8",  "Kreider Academy"),
  "Pass berish (Uzatish)":             ("oIpRuzvsU80",  "Unisport"),
  "Shooting (Zarbalar)":               ("s21Hf39-h64",  "Unisport"),
  "To'pni to'xtatish (First touch)":   ("DZGi1JTMFzY",  "Unisport"),
  "Jonglyorlik (Juggling)":            ("5PQgz2SUPdk",  "Daniel Meyn Football"),
  "Konus orasida slalom":              ("d01bxcf-VhQ",  "Prolific Soccer"),
  "Boshdan zarba (Header)":            ("Fyp4M70M6Hw",  "Unisport"),
  "Tezlik (Sprint)":                   ("nBhUfMx0fq8",  "Pierre's Elite Performance"),
},
'voleybol': {
  "Pas (yuqoridan uzatish)":   ("lEkr3qgIDlI",  "Elevate Yourself"),
  "Priyom (pastdan qabul)":    ("siDVtYyRG_M",  "SIKANA English"),
  "Podacha (Serve)":           ("au3QYrvsy9k",  "Better at Beach Volleyball"),
  "Hujum zarbasi (Spike)":     ("vVRXPxYsZR4",  "Coach Artie"),
  "Blok":                      ("wiBXhCDLj-o",  "VC 'Zenit-Kazan'"),
},
'badminton': {
  "Clear (uzun zarba)":         ("xRv1JLg4NMM",  "Badminton Insight"),
  "Drop shot":                  ("u--taRfMoTs",  "Badminton Insight"),
  "Smash":                      ("vGD-VU0sAc8",  "Aylex Badminton Academy"),
  "Podacha (Serve)":            ("ZlPxYx7VRGA",  "Badminton Insight"),
  "Oyoq harakati (Footwork)":   ("fBa08o5GEqw",  "Badminton Insight"),
},
'basketbol': {
  "Dribbling":                      ("oADaM2L1YLc",  "ILoveBasketballTV"),
  "Bir joydan otish (Jump shot)":   ("UcnB9e5O5NY",  "ILoveBasketballTV"),
  "Shtrafnoy otish (Free throw)":   ("iW2VFzBiaQo",  "SIKANA English"),
  "Lay-up":                         ("d0z7QqblJaM",  "Get Handles Basketball"),
  "Pass berish":                    ("m2sI6P7UQFw",  "THINCPRO Basketball"),
},
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
    for cat, items in VIDEOS.items():
        for name, (vid, chan) in items.items():
            row = db.fetch_one(
                "SELECT id FROM sport_exercises WHERE owner_type=:ot AND owner_key=:ok "
                "AND category=:c AND lower(trim(name))=lower(trim(:n)) AND is_deleted=0 LIMIT 1",
                {"ot": OT, "ok": OK, "c": cat, "n": name},
            )
            if not row:
                print("  ! MASHQ TOPILMADI: %s / %s" % (cat, name))
                missing += 1
                continue
            ex_id = int(row["id"])
            img = "https://img.youtube.com/vi/%s/hqdefault.jpg" % vid
            vurl = "https://www.youtube.com/watch?v=%s" % vid
            a = add_media(ex_id, img, "image")
            b = add_media(ex_id, vurl, "video")
            if a or b:
                added += 1
            else:
                skipped += 1

    db.execute(
        "INSERT INTO sport_sync_meta (owner_type, owner_key, meta_key, meta_value) "
        "VALUES (:ot,:ok,'last_global_update', to_char(clock_timestamp(),'YYYY-MM-DD HH24:MI:SS.US')) "
        "ON CONFLICT (owner_type, owner_key, meta_key) DO UPDATE SET "
        "meta_value = to_char(clock_timestamp(),'YYYY-MM-DD HH24:MI:SS.US'), "
        "updated_at = CURRENT_TIMESTAMP",
        {"ot": OT, "ok": OK},
    )

    print("qo'shildi: %d,  o'tkazildi: %d,  topilmadi: %d" % (added, skipped, missing))
    n = db.fetch_one(
        "SELECT count(*) c FROM sport_exercises e "
        "LEFT JOIN sport_media m ON m.exercise_id = e.id "
        "WHERE e.is_deleted = 0 AND m.id IS NULL")["c"]
    print("Hali mediasiz mashq:", n)


if __name__ == "__main__":
    main()
