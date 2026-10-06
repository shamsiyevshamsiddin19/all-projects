# -*- coding: utf-8 -*-
"""Press / Qorin kategoriyasi uchun boshlang'ich mashqlar.

Bir marta ishlatiladi. QAYTA ishga tushirilsa ham xavfsiz: bir xil nomdagi
mashq allaqachon bo'lsa qayta qo'shilmaydi (nusxa chiqmaydi).
"""
import sys
sys.path.insert(0, '/opt/yordamchi/Yordamchisayt/backend_py')
from app import db

OT, OK, CAT = 'global', 'shared', 'press'

# (nom, progress_type, set, takror/soniya, oshirish, tavsif)
EX = [
    ("Planka", "time", 3, 30, 5, """**Ishlaydigan mushaklar:** to'g'ri qorin, ko'ndalang qorin (chuqur qatlam), bel stabilizatorlari

## Bajarish
1. Tirsak yelka ostida, bilak yerda.
2. Oyoq barmoqlariga tayanib tanani ko'taring.
3. Boshdan tovongacha **bitta to'g'ri chiziq** bo'lsin.
4. Qorinni ichga torting, dumbani siqing.
5. Nafasni ushlamang — bir tekis nafas oling.

## Tipik xatolar
- Dumbani yuqoriga ko'tarish (yengillashtiradi)
- Belni pastga solintirish — bel og'riydi
- Boshni yuqoriga ko'tarish

> **Maslahat:** 30 soniyani toza texnika bilan ushlash, 2 daqiqani belni egib ushlashdan foydali. Oson kelsa vaqtni emas, avval texnikani mustahkamlang."""),

    ("Yon planka", "time", 3, 25, 5, """**Ishlaydigan mushaklar:** yon qorin (qiya mushaklar), ko'ndalang qorin, chanoq stabilizatorlari

## Bajarish
1. Yon yotib, tirsakni yelka ostiga qo'ying.
2. Chanoqni ko'taring — tana yonboshdan to'g'ri chiziq.
3. Yuqoridagi qo'lni belga yoki tepaga qo'ying.
4. Vaqt tugagach ikkinchi tomonga o'ting.

## Tipik xatolar
- Chanoqni pastga tushirib qo'yish
- Tanani oldinga/orqaga burish
- Bir tomonni ko'proq ishlatish

> **Maslahat:** Bel chizig'ini ixchamlashtirishda eng foydali mashqlardan — chunki qiya mushaklarni **og'irliksiz** ishlatadi. Har ikki tomonga teng vaqt bering."""),

    ("Vakuum", "time", 3, 15, 3, """**Ishlaydigan mushaklar:** ko'ndalang qorin mushagi (eng chuqur qatlam — tabiiy "korset")

## Bajarish
1. Ochqorin (nonushtagacha) bajarilgani ma'qul.
2. To'liq nafas chiqaring — o'pkani bo'shating.
3. Qorinni **ichkariga va yuqoriga** maksimal torting (qovurg'a ostiga).
4. Nafas olmasdan ushlab turing.
5. Bo'shatib, bir necha marta nafas oling va takrorlang.

## Tipik xatolar
- Nafasni chiqarmasdan qorinni tortish
- To'yib ovqatlangandan keyin bajarish
- Yelkani ko'tarib zo'riqish

> **Maslahat:** Bel chizig'iga eng ko'p ta'sir qiladigan mashq — ko'ndalang mushak korset kabi ishlaydi va qorinni ichkariga tortib turadi. Kuniga 5 daqiqa, muntazam."""),

    ("Krunch", "reps", 3, 20, 2, """**Ishlaydigan mushaklar:** to'g'ri qorin mushagining yuqori qismi

## Bajarish
1. Chalqancha yoting, tizzani buking, tovon yerda.
2. Qo'lni ko'krakka chalishtiring yoki quloq yoniga qo'ying (tortmang).
3. Yelkani yerdan **ko'taring** — bel yerda qolsin.
4. Tepada bir soniya qorinni siqing.
5. Sekin tushing.

## Tipik xatolar
- Bo'yinni qo'l bilan tortish
- To'liq o'tirib olish (bu boshqa mashq)
- Tez va inersiya bilan bajarish

> **Maslahat:** Harakat kichik — 20-30 sm yetarli. Muhimi tezlik emas, mushakning siqilishini his qilish."""),

    ("Velosiped krunchi", "reps", 3, 20, 2, """**Ishlaydigan mushaklar:** to'g'ri qorin, qiya mushaklar

## Bajarish
1. Chalqancha yoting, qo'l quloq yonida.
2. Oyoqni ko'tarib velosipedda yurgandek harakatlantiring.
3. O'ng tirsakni chap tizzaga yaqinlashtiring, keyin almashtiring.
4. Yelka doim yerdan ko'tarilgan holda qolsin.

## Tipik xatolar
- Bo'yinni tortish
- Belni yerdan uzish
- Juda tez — mushak emas, inersiya ishlaydi

> **Maslahat:** Sekin bajaring: bir tomonga 2 soniya. Tezlashsangiz mashq osonlashadi, foydasi kamayadi."""),

    ("Oyoq ko'tarish (yotib)", "reps", 3, 15, 2, """**Ishlaydigan mushaklar:** to'g'ri qorin mushagining pastki qismi, son bukuvchilari

## Bajarish
1. Chalqancha yoting, qo'lni yon tomonga yoki dumba ostiga qo'ying.
2. Oyoqni to'g'ri holda yuqoriga ko'taring (90 gradusgacha).
3. Sekin pastga tushiring, **yerga tegizmang**.
4. Bel butun davomida yerga bosilib tursin.

## Tipik xatolar
- Belning yerdan uzilishi — eng keng tarqalgan xato
- Oyoqni tashlab yuborish
- Tizzani ortiqcha bukish

> **Maslahat:** Bel uzilib ketsa — tizzani biroz buking yoki oyoqni pastroqqacha tushirmang. Bel og'rimasligi shart."""),

    ("Turnikda oyoq ko'tarish", "reps", 3, 10, 1, """**Ishlaydigan mushaklar:** pastki qorin, son bukuvchilari, panja ushlashi

## Bajarish
1. Turnikka osiling, yelka kengligida ushlang.
2. Tebranishni to'xtating.
3. Tizzani ko'krakka torting (yoki to'g'ri oyoqni gorizontalgacha).
4. Sekin tushiring — tashlab yubormang.

## Tipik xatolar
- Tebranib inersiya bilan ko'tarish
- Faqat oyoqni ishlatib qorinni ishlatmaslik
- Pastga tez tashlash

> **Maslahat:** Avval tizza bilan boshlang. Toza 10 ta chiqsa, to'g'ri oyoqqa o'ting — bu ancha og'irroq."""),

    ("Rus burilishi", "reps", 3, 20, 2, """**Ishlaydigan mushaklar:** qiya mushaklar, to'g'ri qorin

## Bajarish
1. O'tirib tizzani buking, tanani orqaga 45 gradus egib turing.
2. Qo'lni ko'krak oldida tuting.
3. Tanani chapga va o'ngga buring — **beldan emas, ko'krak qafasidan**.
4. Har ikki tomon = 1 takror.

## Tipik xatolar
- Faqat qo'lni harakatlantirish, tanani burmaslik
- Belni yumaloqlash
- Og'ir yuk bilan bajarish

> **Maslahat:** Bel ingichka bo'lishini xohlasangiz og'irlik qo'shmang — qiya mushaklar og'irlikdan yo'g'onlashadi va bel kengroq ko'rinadi. Og'irliksiz, ko'p takror qiling."""),

    ("Alpinist", "reps", 3, 30, 3, """**Ishlaydigan mushaklar:** qorin (to'liq), yelka, yurak-qon tomir tizimi

## Bajarish
1. Planka holatida turing, qo'l yelka ostida.
2. Bir tizzani ko'krakka torting.
3. Tez almashtiring — yugurgandek.
4. Chanoq ko'tarilib-tushmasin, tana to'g'ri qolsin.

## Tipik xatolar
- Dumbani yuqoriga ko'tarish
- Oyoqni to'liq tortmaslik
- Qo'lni yelkadan oldinga qo'yish

> **Maslahat:** Ham qorin, ham kardio. Yog' yoqish uchun eng samarali qorin mashqlaridan."""),

    ("Qayiqcha (hollow hold)", "time", 3, 20, 5, """**Ishlaydigan mushaklar:** butun to'g'ri qorin, ko'ndalang qorin

## Bajarish
1. Chalqancha yoting, qo'lni bosh ustiga cho'zing.
2. Yelka va oyoqni yerdan bir vaqtda ko'taring.
3. Bel **yerga bosilib tursin** — bo'shliq qolmasin.
4. Tana "qayiq" shaklida — ushlab turing.

## Tipik xatolar
- Belning yerdan uzilishi
- Oyoqni juda pastga tushirish (bel uziladi)
- Nafasni ushlab qolish

> **Maslahat:** Og'ir kelsa qo'lni yonga yoki tizzani buking. Bel uzilgan holda ushlagandan ko'ra osonroq variantni toza bajargan yaxshi."""),

    ("O'lik qo'ng'iz (dead bug)", "reps", 3, 12, 1, """**Ishlaydigan mushaklar:** ko'ndalang qorin, bel stabilizatorlari

## Bajarish
1. Chalqancha yoting, qo'lni tepaga, tizzani 90 gradus buking.
2. O'ng qo'lni orqaga va chap oyoqni oldinga bir vaqtda cho'zing.
3. Bel yerdan uzilmasin.
4. Qaytaring va tomonni almashtiring.

## Tipik xatolar
- Belning yerdan uzilishi
- Juda tez bajarish
- Nafasni ushlash

> **Maslahat:** Beli og'riydiganlar uchun eng xavfsiz qorin mashqlaridan. Sekin, nazorat bilan."""),

    ("Yonga egilish (og'irliksiz)", "reps", 3, 20, 2, """**Ishlaydigan mushaklar:** qiya mushaklar, bel yon mushaklari

## Bajarish
1. Tik turing, oyoq yelka kengligida.
2. Qo'lni belga yoki bosh orqasiga qo'ying.
3. Tanani yon tomonga eging — oldinga emas.
4. Qaytib, ikkinchi tomonga.

## Tipik xatolar
- Oldinga engashish
- Chanoqni qimirlatish
- **Gantel bilan bajarish**

> **Maslahat:** Bu mashqni ATAYLAB og'irliksiz qildik. Gantel bilan qilinsa qiya mushaklar yo'g'onlashadi va bel chizig'i KENGROQ ko'rinadi — ingichka bel maqsadiga teskari."""),
]


def main():
    added, skipped = [], []
    for name, ptype, sets, reps, inc, desc in EX:
        exists = db.fetch_one(
            "SELECT id FROM sport_exercises WHERE owner_type=:ot AND owner_key=:ok "
            "AND category=:c AND lower(trim(name))=lower(trim(:n)) AND is_deleted=0 LIMIT 1",
            {"ot": OT, "ok": OK, "c": CAT, "n": name},
        )
        if exists:
            skipped.append(name)
            continue
        db.execute(
            "INSERT INTO sport_exercises (owner_type, owner_key, category, name, description, "
            "weight, increase_amount, set_count, rep_count, progress_type, progress_mode, is_deleted) "
            "VALUES (:ot,:ok,:c,:n,:d, 0, :inc, :s, :r, :pt, 'manual', 0)",
            {"ot": OT, "ok": OK, "c": CAT, "n": name, "d": desc,
             "inc": inc, "s": sets, "r": reps, "pt": ptype},
        )
        added.append(name)

    print("QO'SHILDI (%d):" % len(added))
    for n in added:
        print("  +", n)
    if skipped:
        print("ALLAQACHON BOR (%d): %s" % (len(skipped), ", ".join(skipped)))
    total = db.fetch_one(
        "SELECT count(*) c FROM sport_exercises WHERE owner_type=:ot AND owner_key=:ok "
        "AND category=:cat AND is_deleted=0", {"ot": OT, "ok": OK, "cat": CAT})["c"]
    print("Jami 'press' kategoriyasida:", total)


if __name__ == "__main__":
    main()
