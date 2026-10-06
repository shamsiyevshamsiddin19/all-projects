# -*- coding: utf-8 -*-
"""Sport mashqlarini tiklash — 2026-08-17 server falokatidan keyin.

Eski serverdagi `sport_exercises` jadvali yo'qoldi (zaxira JSON'da faqat
`sport_log_v1` bor edi — mashqlar ro'yxati emas). Bu skript har bir
kategoriya uchun standart mashqlar to'plamini qayta yaratadi.

Log'dan aniq TIKLANGAN nomlar (eski nomi bilan bir xil saqlangan):
  turnik : "Pull up", "Klassik tortilish"
  brus   : "Brusda cho'kish"
  futbol : "Dribbling (To'pni olib yurish)", "Shooting (Zarbalar)"
Qolganlari eski nomlari noma'lum — standart nomlar bilan qo'shildi.

`press` bu skriptda YO'Q — u `press_exercises.py` orqali tiklangan.
Qayta ishga tushirilsa xavfsiz: bir xil nom ikkinchi marta qo'shilmaydi.

progress_mode hamma joyda 'manual' — hech narsa avtomatik oshmaydi.
Kerakli mashqni saytda 'daily' ga o'zgartirish mumkin.
"""
import sys
sys.path.insert(0, '/opt/yordamchi/Yordamchisayt/backend_py')
from app import db

OT, OK = 'global', 'shared'

# (nom, progress_type, set, takror, oshirish, tavsif)
DATA = {

'turnik': [
 ("Pull up", "reps", 4, 8, 1, """**Ishlaydigan mushaklar:** eng keng orqa mushagi (latissimus), yelka orqasi, bitseps, panja

**Bajarish:**
1. Turnikni yelka kengligidan biroz kengroq, kaft o'zingdan teskari ushla.
2. Yelka pichoqlarini pastga va orqaga tort — keyin tirsakni bukib tortil.
3. Iyak turnikdan oshsin, yuqorida yarim soniya ushlab tur.
4. Pastga NAZORAT bilan tush (2 soniya), qo'l to'liq yozilsin.

**Xatolar:** tepish/silkinish bilan tortilish, yarim amplituda, pastda yelkani "o'lik" holda bo'shatib qo'yish."""),

 ("Klassik tortilish", "reps", 4, 6, 1, """**Ishlaydigan mushaklar:** orqa (latissimus), yelka orqasi, bitseps, o'rta trapetsiya

**Bajarish:**
1. Ushlash — aynan yelka kengligida, kaft o'zingdan teskari.
2. Tanani taxta kabi tik saqla, oyoqni oldinga chiqarma.
3. Ko'krakni turnikka olib borgandek tortil.
4. Pastga sekin tush, har takror to'liq yozilishdan boshlansin.

**Xatolar:** bo'yinni cho'zish (iyakni tepaga otish), nafasni ushlab qolish."""),

 ("Chin-up (teskari ushlash)", "reps", 3, 8, 1, """**Ishlaydigan mushaklar:** bitseps (asosiy), orqa, yelka oldi

**Bajarish:**
1. Kaft o'zingga qaragan holda, yelka kengligida ushla.
2. Tirsakni tanaga yaqin tut va ko'krakni turnikka tort.
3. Yuqorida bitsepsni siqib, 1 soniya ushla.
4. Sekin tush.

**Nima uchun:** klassik tortilishdan yengilroq — tortilish soni kam bo'lsa shu bilan boshlash yaxshi."""),

 ("Keng ushlab tortilish", "reps", 3, 6, 1, """**Ishlaydigan mushaklar:** latissimusning tashqi qismi (orqa kengligi), yelka orqasi

**Bajarish:**
1. Yelkadan ancha keng ushla, kaft oldinga qaragan.
2. Tirsakni yon tomonga, pastga tortadigandek harakat qil.
3. Ko'krakning yuqori qismini turnikka yaqinlashtir.
4. Amplituda kichikroq bo'ladi — bu normal.

**Xatolar:** bitseps bilan tortish (tirsakni oldinga olib kelish)."""),

 ("Avstraliya tortilishi", "reps", 3, 12, 2, """**Ishlaydigan mushaklar:** o'rta orqa, romboidlar, yelka orqasi, bitseps

**Bajarish:**
1. Past turnik (bel balandligida) tagiga yot, ustidan ushla.
2. Tovon yerda, tana to'g'ri chiziq — bel egilmasin.
3. Ko'krakni turnikka tort, yelka pichoqlarini siq.
4. Sekin tush.

**Nima uchun:** to'liq tortilishga tayyorgarlik + orqa "qalinligi" uchun."""),

 ("Turnikda osilib turish", "time", 3, 30, 5, """**Ishlaydigan mushaklar:** panja va bilak (grip), yelka kamari, ko'ndalang qorin

**Bajarish:**
1. Turnikni yelka kengligida ushla, oyoq yerdan uzilsin.
2. Yelkani "quloqqa" ko'tarma — pastga tortib faol ushla.
3. Belni bo'shatib osil, tinch nafas ol.
4. Vaqt tugaguncha ushla.

**Foydasi:** grip kuchini oshiradi (tortilish soni ham ortadi), umurtqani cho'zadi."""),
],

'brus': [
 ("Brusda cho'kish", "reps", 4, 8, 1, """**Ishlaydigan mushaklar:** ko'krakning pastki qismi, triseps, oldingi delta

**Bajarish:**
1. Brusga chiq, qo'l to'liq yozilgan, tana tik.
2. Tirsakni orqaga bukib tush — yelka tirsak sathiga yetsin.
3. Tirsakni yon tomonga ochib yuborma (45° dan ortiq emas).
4. Kaftga tayanib tepaga ko'tar, yuqorida tirsakni "qulflab" tashlama.

**Xatolar:** juda chuqur tushish (yelkaga zarar), silkinib ko'tarilish.

**Ko'krak uchun:** tanani biroz oldinga eg. **Triseps uchun:** tik tur."""),

 ("Brusda oyoq ko'tarish", "reps", 3, 12, 2, """**Ishlaydigan mushaklar:** pastki qorin, son bukuvchilari, yelka stabilizatorlari

**Bajarish:**
1. Brusda qo'lga tayanib tur, tana osilib turadi.
2. Bukilgan (yengilroq) yoki to'g'ri (og'irroq) oyoqni 90° gacha ko'tar.
3. Yuqorida chanoqni biroz yuqoriga bur.
4. Sekin tushir — silkinib qolma.

**Xatolar:** oyoqni otib ko'tarish, belni orqaga egish."""),

 ("Brusda tayanib turish", "time", 3, 30, 5, """**Ishlaydigan mushaklar:** yelka kamari, triseps, ko'ndalang qorin

**Bajarish:**
1. Brusga chiq, qo'l to'liq yozilgan.
2. Yelkani pastga tort (quloqqa ko'tarma), ko'krakni och.
3. Qorinni tort, oyoqni birlashtir.
4. Vaqt tugaguncha qimirlamay tur.

**Nima uchun:** cho'kish mashqiga xavfsiz poydevor, yelka barqarorligi."""),

 ("Teskari cho'kish (skameykada)", "reps", 3, 15, 2, """**Ishlaydigan mushaklar:** triseps (asosiy), oldingi delta

**Bajarish:**
1. Skameyka/stul chetiga orqa bilan tayan, kaft chekkada.
2. Tovonni oldinga qo'y, chanoqni skameyka yonidan tushir.
3. Tirsakni orqaga bukib 90° gacha tush.
4. Trisepsni siqib ko'tar.

**Xatolar:** tirsakni yon tomonga ochish, chanoqni skameykadan uzoqlashtirish (yelkaga zo'r)."""),

 ("Brusda sekin tushish", "reps", 3, 5, 1, """**Ishlaydigan mushaklar:** ko'krak, triseps — ekssentrik (cho'zilish) rejimida

**Bajarish:**
1. Brusning tepasiga sakrab yoki oyoq bilan chiqib ol.
2. FAQAT pastga tushish bosqichini bajar — 4-5 soniya davomida.
3. Pastda to'xta, oyoq bilan yana tepaga chiq.
4. Takrorla.

**Nima uchun:** hali to'liq cho'ka olmasang, kuch shu mashq bilan tez ortadi."""),
],

'ajimaniya': [
 ("Klassik ajimaniya", "reps", 4, 15, 2, """**Ishlaydigan mushaklar:** ko'krak, triseps, oldingi delta, ko'ndalang qorin

**Bajarish:**
1. Kaft yelkadan biroz keng, barmoq oldinga.
2. Tana boshdan tovongacha to'g'ri chiziq — chanoq osilib tushmasin.
3. Ko'krak yerga 2-3 sm qolguncha tush, tirsak 45° burchakda.
4. Kaft bilan yerni itarib ko'tar.

**Xatolar:** belni egib qo'yish, tirsakni 90° yon tomonga ochish, boshni oldinga cho'zish."""),

 ("Keng qo'l bilan ajimaniya", "reps", 3, 12, 2, """**Ishlaydigan mushaklar:** ko'krak (tashqi qismi) — asosiy urg'u

**Bajarish:**
1. Kaftni yelkadan ancha kengroq qo'y.
2. Tushganda ko'krakda cho'zilishni his qil.
3. Amplituda klassikdan kichikroq bo'ladi.
4. Yuqorida ko'krakni siq.

**Xatolar:** juda keng qo'yish — yelka bo'g'imiga zarar."""),

 ("Olmos (tor) ajimaniya", "reps", 3, 10, 2, """**Ishlaydigan mushaklar:** triseps (asosiy), ko'krakning ichki qismi

**Bajarish:**
1. Kaftni ko'krak ostida birlashtir — bosh barmoq va ko'rsatkich barmoq "olmos" hosil qilsin.
2. Tirsakni tanaga yaqin tutib tush.
3. Ko'krak kaftga tegsin.
4. Trisepsni siqib ko'tar.

**Xatolar:** tirsakni yon tomonga ochib yuborish — mashq ma'nosini yo'qotadi."""),

 ("Oyoq balandda ajimaniya", "reps", 3, 12, 2, """**Ishlaydigan mushaklar:** ko'krakning yuqori qismi, yelka

**Bajarish:**
1. Oyoqni skameyka/stulga qo'y (30-50 sm).
2. Kaft yerda, yelkadan keng.
3. Tush va ko'tar — tana to'g'ri chiziqda qolsin.
4. Qanchalik baland bo'lsa, shunchalik og'ir.

**Xatolar:** chanoqni yuqoriga ko'tarish (yuk yo'qoladi)."""),

 ("Pike ajimaniya", "reps", 3, 10, 1, """**Ishlaydigan mushaklar:** yelka (asosiy), triseps, yuqori ko'krak

**Bajarish:**
1. Planka holatidan chanoqni tepaga ko'tar — tana "V" harfi shaklida.
2. Boshni kaft orasiga tushir.
3. Tirsakni bukib, bosh tepasi yerga yaqinlashsin.
4. Yelka bilan itarib ko'tar.

**Nima uchun:** turgan holda tayanib ajimaniyaga (handstand push-up) tayyorgarlik."""),

 ("Sakrab ajimaniya", "reps", 3, 8, 1, """**Ishlaydigan mushaklar:** ko'krak, triseps — portlovchi (plyometrik) kuch

**Bajarish:**
1. Klassik ajimaniya holatidan pastga tush.
2. Kuch bilan itarib kaftni yerdan uzil.
3. Yumshoq qo'nib, darrov keyingi takrorga o't.
4. Charchagach to'xta — texnika buzilishi bilan foyda tugaydi.

**Ogohlantirish:** bilak/yelka og'riq bo'lsa bu mashqni qilma."""),
],

'full': [
 ("Burpi", "reps", 4, 12, 2, """**Ishlaydigan mushaklar:** deyarli butun tana + yurak-qon tomir tizimi

**Bajarish:**
1. Tik turgan holatdan cho'kkalab, kaftni yerga qo'y.
2. Oyoqni orqaga otib planka holatiga o't, bitta ajimaniya qil.
3. Oyoqni kaftga tortib qaytar.
4. Yuqoriga sakra, qo'lni bosh uzra ko'tar.

**Xatolar:** belni egib planka qilish, oxirgi sakrashni tashlab yuborish."""),

 ("Og'irliksiz o'tirib turish", "reps", 4, 20, 3, """**Ishlaydigan mushaklar:** son oldi (kvadritseps), dumba, orqa yuza

**Bajarish:**
1. Oyoq yelka kengligida, barmoq biroz tashqariga.
2. Chanoqni orqaga olib tush — tizza barmoq yo'nalishida.
3. Son yer bilan parallel bo'lguncha (yoki pastroq) tush.
4. Tovonga tayanib tepaga chiq.

**Xatolar:** tovonni yerdan uzish, tizzani ichkariga yiqitish, belni yumaloqlash."""),

 ("Vipad (lunge)", "reps", 3, 12, 2, """**Ishlaydigan mushaklar:** kvadritseps, dumba, muvozanat mushaklari

**Bajarish:**
1. Bir oyoq bilan katta qadam tashla.
2. Orqa tizza yerga yaqinlashguncha tush, ikkala tizza 90°.
3. Old tovonga tayanib turib ket.
4. Oyoqni almashtir. Har ikki oyoq = 1 takror.

**Xatolar:** old tizzani barmoqdan uzoq oldinga chiqarish, tanani oldinga egish."""),

 ("Alpinist (mountain climber)", "reps", 3, 30, 5, """**Ishlaydigan mushaklar:** qorin, yelka, oyoq + kardio

**Bajarish:**
1. Planka holati, kaft yelka ostida.
2. Bir tizzani ko'krakka tez tort.
3. Almashtir — yugurgandek harakat.
4. Chanoq tepaga sakramasin.

**Xatolar:** chanoqni ko'tarib yuborish, qo'lni oldinga surish."""),

 ("Sakrab o'tirib turish", "reps", 3, 12, 2, """**Ishlaydigan mushaklar:** kvadritseps, dumba, boldir — portlovchi kuch

**Bajarish:**
1. Oddiy o'tirib turish holatiga tush.
2. Pastdan kuch bilan yuqoriga sakra.
3. Tizzani biroz bukib YUMSHOQ qo'n.
4. Darrov keyingi takrorga tush.

**Ogohlantirish:** tizza og'riq bo'lsa qilma, qattiq yerda kamroq qil."""),

 ("Ayiq yurishi (bear crawl)", "time", 3, 30, 5, """**Ishlaydigan mushaklar:** yelka, qorin, oyoq — butun tana muvofiqligi

**Bajarish:**
1. To'rt oyoqlab tur, tizza yerdan 3-5 sm ko'tarilgan.
2. Orqadagi qo'l va qarama-qarshi oyoqni bir vaqtda oldinga surib yur.
3. Chanoq baland ko'tarilmasin, orqa parallel qolsin.
4. Oldinga va orqaga yur.

**Nima uchun:** qorin va yelkani bir vaqtda ishlatadi, koordinatsiyani oshiradi."""),
],

'grud': [
 ("Yotib shtanga ko'tarish", "weight", 4, 8, 2.5, """**Ishlaydigan mushaklar:** ko'krak (asosiy), triseps, oldingi delta

**Bajarish:**
1. Skameykada yot — bosh, yelka, dumba tegib tursin.
2. Shtangani yelkadan kengroq ushla, yelka pichoqlarini siq.
3. Ko'krakning o'rtasiga nazorat bilan tushir.
4. Yuqoriga itar, tirsakni to'liq qulflama.

**Xavfsizlik:** og'ir vazn bilan albatta yordamchi yoki cheklagich bilan ishla."""),

 ("Qiya skameykada ko'tarish", "weight", 3, 10, 2.5, """**Ishlaydigan mushaklar:** ko'krakning YUQORI qismi, oldingi delta

**Bajarish:**
1. Skameykani 30-45° ga ko'tar (undan tikroq — yelkaga o'tadi).
2. Shtanga/gantelni ko'krakning yuqori qismiga tushir.
3. Yuqoriga itar, tepada ko'krakni siq.
4. Sekin tushir.

**Xatolar:** juda tik burchak — yuk yelkaga ketadi."""),

 ("Gantel bilan yoyish", "weight", 3, 12, 1, """**Ishlaydigan mushaklar:** ko'krak (cho'zilish orqali), oldingi delta

**Bajarish:**
1. Skameykada yot, gantelni ko'krak ustida ushla, tirsak biroz bukilgan.
2. Qo'lni yon tomonga yoy — ko'krakda cho'zilishni his qil.
3. Tirsak burchagi butun harakat davomida O'ZGARMASIN.
4. Ko'krakni siqib qaytar (quchoqlagandek).

**Xatolar:** og'ir vazn olish — bu mashq izolyatsiya, vazn kichik bo'ladi."""),

 ("Ko'krak uchun brusda cho'kish", "reps", 3, 10, 1, """**Ishlaydigan mushaklar:** ko'krakning pastki qismi, triseps

**Bajarish:**
1. Brusga chiq, tanani oldinga 20-30° eg.
2. Tirsakni biroz yon tomonga ochib tush.
3. Ko'krakda cho'zilish sezilguncha tush.
4. Ko'krak bilan itarib ko'tar.

**Farqi:** tik holatda — triseps, oldinga engashganda — ko'krak."""),

 ("Og'irlik bilan ajimaniya", "reps", 3, 12, 2, """**Ishlaydigan mushaklar:** ko'krak, triseps, qorin

**Bajarish:**
1. Orqaga (yelka pichoqlari orasiga) og'irlik — disk yoki ryukzak qo'y.
2. Odatdagi ajimaniyani bajar.
3. Tana to'g'ri chiziqda qolsin.
4. Nazorat bilan tush, kuch bilan ko'tar.

**Nima uchun:** oddiy ajimaniya yengil bo'lib qolganda kuchni oshiradi."""),
],

'bitseps': [
 ("Shtanga bilan bukish", "weight", 4, 10, 2.5, """**Ishlaydigan mushaklar:** bitseps (ikki boshli), bilak

**Bajarish:**
1. Tik tur, shtangani yelka kengligida pastdan ushla.
2. Tirsakni tanaga yopishtir — u qimirlamasin.
3. Shtangani yuqoriga bukib ko'tar, tepada 1 soniya siq.
4. Sekin (2-3 soniya) tushir.

**Xatolar:** bel bilan silkinish, tirsakni oldinga chiqarish."""),

 ("Gantel bilan navbatma-navbat bukish", "weight", 3, 12, 1, """**Ishlaydigan mushaklar:** bitseps, yelka-bilak (brachialis)

**Bajarish:**
1. Gantelni ikki yonda ushla, kaft oldinga.
2. Bir qo'lni bukib ko'tar, tepada bilakni biroz burab siq.
3. Sekin tushir, keyin ikkinchi qo'l.
4. Tirsak butun vaqt qimirlamasin.

**Nima uchun:** har bir qo'lga alohida diqqat — nomutanosiblikni tuzatadi."""),

 ("Bolg'a (hammer) bukish", "weight", 3, 12, 1, """**Ishlaydigan mushaklar:** brachialis, brachioradialis (bilak) + bitseps

**Bajarish:**
1. Gantelni "bolg'a" kabi ushla — kaft bir-biriga qaragan.
2. Bilakni burmasdan yuqoriga ko'tar.
3. Tepada 1 soniya ushla.
4. Sekin tushir.

**Nima uchun:** qo'lning qalinligi va grip kuchini oshiradi (armrestlingga foydali)."""),

 ("Skott skameykasida bukish", "weight", 3, 10, 1, """**Ishlaydigan mushaklar:** bitseps (pastki qismi) — to'liq izolyatsiya

**Bajarish:**
1. Tirsakni qiya taxtaga to'liq qo'y.
2. Qo'lni sekin yoz — lekin oxirigacha "tashlab" yuborma.
3. Bukib ko'tar, tepada siq.
4. Nazorat bilan tushir.

**Ogohlantirish:** pastda keskin yozilish — tirsak jarohati sababi."""),

 ("Turnikda teskari ushlab tortilish", "reps", 3, 8, 1, """**Ishlaydigan mushaklar:** bitseps + orqa

**Bajarish:**
1. Turnikni kaft o'zingga qaragan, yelka kengligidan tor ushla.
2. Tirsakni tanaga yaqin tutib tortil.
3. Iyak turnikdan oshsin.
4. Sekin tush.

**Nima uchun:** bitsepsni o'z og'irliging bilan ishlatadi — eng kuchli variantlardan biri."""),
],

'triseps': [
 ("Fransuzcha ko'tarish", "weight", 3, 12, 1, """**Ishlaydigan mushaklar:** triseps (ayniqsa uzun boshi)

**Bajarish:**
1. Skameykada yot, shtanga/gantelni ko'krak ustida ushla.
2. FAQAT tirsakni bukib, vaznni peshona orqasiga tushir.
3. Yelka (tirsakdan tepasi) qimirlamasin.
4. Trisepsni siqib qaytar.

**Xatolar:** yelkani ham harakatlantirish — u presga aylanadi."""),

 ("Blokda ip bilan tushirish", "weight", 3, 15, 2.5, """**Ishlaydigan mushaklar:** triseps (lateral va medial boshlari)

**Bajarish:**
1. Yuqori blokka ip biriktir, tirsakni tanaga yopishtir.
2. Pastga itar, oxirida ipni yon tomonga yoy.
3. Pastda 1 soniya siq.
4. Sekin qaytar — tirsak qimirlamasin.

**Xatolar:** tana bilan bosish, tirsakni oldinga surish."""),

 ("Olmos ajimaniya", "reps", 3, 12, 2, """**Ishlaydigan mushaklar:** triseps, ko'krakning ichki qismi

**Bajarish:**
1. Kaftni ko'krak ostida "olmos" shaklida birlashtir.
2. Tirsakni tanaga yaqin tutib tush.
3. Ko'krak kaftga tegsin.
4. Itarib ko'tar, tepada trisepsni siq.

**Xatolar:** tirsakni yon tomonga ochish."""),

 ("Skameykada teskari cho'kish", "reps", 3, 15, 2, """**Ishlaydigan mushaklar:** triseps, oldingi delta

**Bajarish:**
1. Skameyka chetiga orqa bilan tayan.
2. Chanoqni tushir, tirsak 90° gacha buksin.
3. Tirsakni orqaga — yon tomonga emas.
4. Trisepsni siqib ko'tar.

**Og'irlashtirish:** oyoqni to'g'ri qil yoki songa disk qo'y."""),

 ("Bosh orqasidan gantel ko'tarish", "weight", 3, 12, 1, """**Ishlaydigan mushaklar:** trisepsning uzun boshi (qo'lning pastki-orqa qismi)

**Bajarish:**
1. Bitta gantelni ikki qo'llab bosh uzra ushla.
2. Tirsakni bukib bosh orqasiga tushir.
3. Tirsak yuqoriga qaragan va qimirlamas holda tursin.
4. Tepaga ko'tarib siq.

**Xatolar:** tirsakni yon tomonga yoyib yuborish, belni orqaga egish."""),
],

'orqa': [
 ("Stanovoy tortish (deadlift)", "weight", 4, 6, 5, """**Ishlaydigan mushaklar:** butun orqa zanjiri — bel, dumba, son orqasi, trapetsiya

**Bajarish:**
1. Shtanga oyoq o'rtasida, oyoq chanoq kengligida.
2. Chanoqni orqaga olib engash, bel TO'G'RI (yumaloqlanmasin).
3. Ko'krakni och, shtangani oyoqqa yaqin tutib turib ket.
4. Tepada chanoqni oldinga siq, orqaga egilma.

**Xavfsizlik:** eng jiddiy mashq — texnikani yengil vazn bilan mustahkamla, keyin og'irlashtir."""),

 ("Egilib shtanga tortish", "weight", 4, 10, 2.5, """**Ishlaydigan mushaklar:** latissimus, romboidlar, o'rta trapetsiya, yelka orqasi

**Bajarish:**
1. 45° engash, bel to'g'ri, tizza biroz bukilgan.
2. Shtangani qorinning pastiga tort.
3. Yelka pichoqlarini bir-biriga siq.
4. Sekin tushir.

**Xatolar:** tanani ko'tarib silkinish, belni yumaloqlash."""),

 ("Yuqori blok tortish", "weight", 3, 12, 2.5, """**Ishlaydigan mushaklar:** latissimus (orqa kengligi), bitseps

**Bajarish:**
1. Tutqichni keng ushla, sonni valik ostiga mahkamla.
2. Ko'krakni ochib, tutqichni ko'krak yuqorisiga tort.
3. Tirsakni pastga va orqaga yo'nalt.
4. Nazorat bilan qaytar — yelka tepaga cho'zilsin.

**Xatolar:** bo'yin orqasiga tortish (yelka bo'g'imiga zararli)."""),

 ("Gorizontal blok tortish", "weight", 3, 12, 2.5, """**Ishlaydigan mushaklar:** o'rta orqa (qalinlik), romboidlar, latissimus

**Bajarish:**
1. O'tir, oyoqni tayanchga qo'y, bel to'g'ri.
2. Tutqichni qoringa tort, tirsak tanaga yaqin.
3. Yelka pichoqlarini siq, 1 soniya ushla.
4. Sekin qaytar.

**Xatolar:** tana bilan orqaga tashlanib tortish."""),

 ("Gantel bilan bir qo'lda tortish", "weight", 3, 12, 1, """**Ishlaydigan mushaklar:** latissimus (har tomon alohida), o'rta orqa

**Bajarish:**
1. Bir tizza va bir kaftni skameykaga qo'y, orqa parallel.
2. Gantelni yerdan chanoqqa tomon tort.
3. Tirsakni tanaga yaqin tut, tepada siq.
4. To'liq cho'zilguncha tushir.

**Xatolar:** tanani burab tortish."""),

 ("Giperekstenziya", "reps", 3, 15, 2, """**Ishlaydigan mushaklar:** bel yozuvchilari, dumba, son orqasi

**Bajarish:**
1. Trenajyorga chanoq bilan tayan, tovon mahkamlangan.
2. Belni to'g'ri saqlab pastga engash.
3. Dumbani siqib tanani tekis chiziqqa ko'tar.
4. Orqaga OSHIRIB egilma.

**Nima uchun:** belni mustahkamlaydi — deadliftga poydevor."""),
],

'yelka': [
 ("Armeycha ko'tarish", "weight", 4, 8, 2.5, """**Ishlaydigan mushaklar:** oldingi va o'rta delta, triseps, yuqori ko'krak

**Bajarish:**
1. Tik tur, shtangani ko'krak yuqorisida yelka kengligida ushla.
2. Qorin va dumbani tort — bel egilmasin.
3. Boshdan tepaga itar, oxirida bosh biroz oldinga o'tsin.
4. Nazorat bilan tushir.

**Xatolar:** belni orqaga egib "yotib press" ga aylantirish."""),

 ("Gantel bilan yon ko'tarish", "weight", 4, 15, 1, """**Ishlaydigan mushaklar:** O'RTA delta — yelka kengligini beradi

**Bajarish:**
1. Gantel yonlarda, tirsak biroz bukilgan.
2. Qo'lni yon tomonga yelka sathigacha ko'tar.
3. Kichik barmoq biroz yuqorida bo'lsin.
4. Sekin tushir — pastda "dam olma".

**Xatolar:** og'ir vazn olib silkinish. Vazn kichik, takror ko'p bo'lsin."""),

 ("Old ko'tarish", "weight", 3, 12, 1, """**Ishlaydigan mushaklar:** oldingi delta

**Bajarish:**
1. Gantel/disk son oldida, kaft pastga qaragan.
2. Qo'lni to'g'ri oldinga yelka sathigacha ko'tar.
3. 1 soniya ushla.
4. Sekin tushir.

**Xatolar:** yelkadan baland ko'tarish, tana bilan silkinish."""),

 ("Egilib yon ko'tarish", "weight", 3, 15, 1, """**Ishlaydigan mushaklar:** ORQA delta — ko'pchilik e'tibordan chetda qoldiradi

**Bajarish:**
1. Tanani oldinga eg (parallelga yaqin), bel to'g'ri.
2. Gantelni yon tomonga yoyib ko'tar.
3. Yelka pichoqlarini siqma — faqat delta ishlasin.
4. Sekin tushir.

**Nima uchun:** yelka salomatligi va tik qomat uchun juda muhim."""),

 ("Shrug (trapetsiya)", "weight", 3, 15, 2.5, """**Ishlaydigan mushaklar:** yuqori trapetsiya

**Bajarish:**
1. Shtanga/gantelni yonlarda ushla, qo'l to'g'ri.
2. Yelkani QULOQQA tomon TIK ko'tar.
3. Tepada 1-2 soniya siq.
4. Sekin tushir.

**Xatolar:** yelkani aylantirish (foydasi yo'q, bo'g'imga zarar)."""),

 ("Arnold press", "weight", 3, 12, 1, """**Ishlaydigan mushaklar:** butun delta (oldingi + o'rta), triseps

**Bajarish:**
1. Gantel ko'krak oldida, kaft o'zingga qaragan.
2. Ko'tarayotib bilakni burab och — tepada kaft oldinga qaraydi.
3. Tepada to'liq yoz.
4. Teskari yo'l bilan qaytar.

**Nima uchun:** bitta harakatda yelkaning bir necha boshini ishlatadi."""),
],

'oyoq': [
 ("Shtanga bilan o'tirib turish", "weight", 4, 8, 5, """**Ishlaydigan mushaklar:** kvadritseps, dumba, son orqasi, bel stabilizatorlari

**Bajarish:**
1. Shtangani trapetsiya ustiga qo'y, oyoq yelka kengligida.
2. Chanoqni orqaga olib tush, tizza barmoq yo'nalishida.
3. Son parallel yoki pastroq bo'lguncha tush.
4. Tovonga tayanib turib ket.

**Xatolar:** tizzani ichkariga yiqitish, tovonni uzish, belni yumaloqlash."""),

 ("Og'irliksiz chuqur o'tirish", "reps", 4, 25, 5, """**Ishlaydigan mushaklar:** kvadritseps, dumba, boldir; harakatchanlik

**Bajarish:**
1. Oyoq yelka kengligida, qo'l oldinga cho'zilgan.
2. Iloji boricha chuqur tush.
3. Pastda 1 soniya to'xta.
4. Tekis tepaga chiq.

**Nima uchun:** har kuni qilinadi, tizza va chanoq harakatchanligini saqlaydi."""),

 ("Bolg'archa vipad", "weight", 3, 10, 1, """**Ishlaydigan mushaklar:** kvadritseps, dumba (bir oyoqda — kuchli nomutanosiblikni tuzatadi)

**Bajarish:**
1. Orqa oyoq tovonini skameykaga qo'y.
2. Old oyoq bilan pastga tush — tizza 90°.
3. Tana biroz oldinga engashsin (dumba uchun).
4. Old tovonga tayanib ko'tar.

**Xatolar:** juda yaqin turish (tizzaga zo'r)."""),

 ("Rumin tortishi", "weight", 3, 12, 2.5, """**Ishlaydigan mushaklar:** son orqasi (bitseps femoris), dumba, bel

**Bajarish:**
1. Shtanga son oldida, tizza deyarli to'g'ri (biroz bukilgan).
2. Chanoqni ORQAGA olib engash — shtanga oyoqqa tegib tushsin.
3. Son orqasida cho'zilish sezilgan joyda to'xta.
4. Dumbani siqib turib ket.

**Xatolar:** belni yumaloqlash, tizzani ko'p bukish (deadliftga aylanadi)."""),

 ("Boldir ko'tarish", "weight", 4, 20, 2.5, """**Ishlaydigan mushaklar:** boldir (gastrocnemius, soleus)

**Bajarish:**
1. Zinapoya chetida barmoq bilan tur, tovon osilib tursin.
2. Tovonni pastga tushirib cho'z.
3. Barmoqqa ko'tarilib tepada 2 soniya siq.
4. Sekin tushir.

**Nima uchun:** boldir sekin o'sadi — takror ko'p va sekin bajarilishi kerak."""),

 ("Devor bo'ylab o'tirish", "time", 3, 45, 5, """**Ishlaydigan mushaklar:** kvadritseps (statik chidamlilik)

**Bajarish:**
1. Orqani devorga tira, oyoqni oldinga qo'y.
2. Tizza 90° bo'lguncha sirg'alib tush.
3. Bel devorga tegib tursin.
4. Vaqt tugaguncha ushla.

**Nima uchun:** tizza atrofidagi mushaklarni bo'g'imga zarar bermay mustahkamlaydi."""),
],

'kardio': [
 ("Yugurish", "min", 1, 30, 5, """**Ta'siri:** yurak-qon tomir chidamliligi, o'pka hajmi, kaloriya sarfi

**Bajarish:**
1. 5 daqiqa tez yurish bilan qizib ol.
2. Suhbat qura oladigan tezlikda yugur (zona 2).
3. Qadam qisqa va tez bo'lsin, tovonga qattiq urma.
4. Oxirida 5 daqiqa sekin yurib tinchlan.

**Maslahat:** haftada masofani 10% dan ko'p oshirma."""),

 ("Arqon sakrash", "min", 4, 3, 1, """**Ishlaydigan:** boldir, yelka, koordinatsiya + kuchli kardio

**Bajarish:**
1. Arqonni bilak bilan aylantir — yelka bilan emas.
2. Past sakra (2-3 sm yetarli), barmoqqa qo'n.
3. Tirsakni tanaga yaqin tut.
4. 3 daqiqa — 1 daqiqa dam, takrorla.

**Nima uchun:** 10 daqiqa arqon ≈ 30 daqiqa yugurish."""),

 ("Interval yugurish (HIIT)", "min", 8, 1, 1, """**Ta'siri:** maksimal kislorod iste'moli (VO2max), yog' yoqish

**Bajarish:**
1. 10 daqiqa yengil qizish.
2. 30 soniya maksimal tezlikda yugur.
3. 90 soniya sekin yurish/yugurish bilan tikla.
4. 8 marta takrorla, keyin 10 daqiqa tinchlanish.

**Ogohlantirish:** haftada 2 martadan ko'p qilma — tiklanish kerak."""),

 ("Velosiped", "min", 1, 40, 5, """**Ta'siri:** oyoq chidamliligi, kardio — bo'g'imga zarba bermaydi

**Bajarish:**
1. Egarni to'g'rila — pastda oyoq deyarli to'g'ri bo'lsin.
2. Tekis tezlikda 40 daqiqa yur.
3. Kadans 80-90 aylanish/daqiqa.
4. Oxirida sekinlashtirib tugat.

**Nima uchun:** tizza/oyoq og'rig'i bo'lganda yugurishning eng yaxshi o'rnini bosadi."""),

 ("Tez yurish", "min", 1, 45, 5, """**Ta'siri:** tiklanish, yog' yoqish, kunlik faollik

**Bajarish:**
1. Qadamni uzaytirmasdan tezlashtir.
2. Qo'lni faol harakatlantir.
3. Nafas biroz tezlashsin, lekin gapira olishing kerak.
4. Imkon bo'lsa qiyalikda yur.

**Nima uchun:** eng xavfsiz kardio — har kuni qilinadi, charchatmaydi."""),
],

'armwresling': [
 ("Bilak bukish (wrist curl)", "weight", 4, 15, 1, """**Ishlaydigan mushaklar:** bilak bukuvchilari — armrestlingda eng muhim guruh

**Bajarish:**
1. Tirsakni tizzaga yoki skameykaga qo'y, kaft yuqoriga.
2. Gantelni faqat bilak bilan pastga tushir (barmoq ochilsin).
3. Barmoqni yumib, bilakni yuqoriga bukib ko'tar.
4. Tepada 1 soniya siq.

**Xatolar:** tirsakni ko'tarish — bitseps ishga tushib ketadi."""),

 ("Teskari bilak bukish", "weight", 3, 15, 1, """**Ishlaydigan mushaklar:** bilak yozuvchilari — bo'g'im barqarorligi

**Bajarish:**
1. Tirsakni tayanchga qo'y, kaft PASTGA qaragan.
2. Bilakni yuqoriga bukib ko'tar.
3. Sekin tushir.
4. Vazn kichik bo'lsin — bu nozik mushaklar.

**Nima uchun:** bukuvchilar bilan muvozanat — tirsak jarohatining oldini oladi."""),

 ("Bolg'a bukish", "weight", 4, 12, 1, """**Ishlaydigan mushaklar:** brachioradialis — armrestlingda "yon kuch"

**Bajarish:**
1. Gantelni bolg'a kabi ushla (kaft ichkariga).
2. Bilakni burmasdan ko'tar.
3. Tepada siq, sekin tushir.
4. Har ikki qo'lni birga yoki navbatma-navbat.

**Nima uchun:** armrestlingchi bilagining qalinligi asosan shu mushaqdan."""),

 ("Pronatsiya (bilakni burash)", "weight", 3, 15, 1, """**Ishlaydigan mushaklar:** pronator teres — raqib kaftini burish harakati

**Bajarish:**
1. Tirsakni tayanchga qo'y, bir uchida vazn bor tayoqchani ushla.
2. Bilakni ichkariga bur (kaft pastga qarab aylansin).
3. Sekin qaytar.
4. Amplituda to'liq bo'lsin.

**Nima uchun:** armrestlingdagi asosiy g'alaba harakati aynan shu."""),

 ("Ushlash kuchi (grip hold)", "time", 4, 45, 5, """**Ishlaydigan mushaklar:** barmoq bukuvchilari, bilak

**Bajarish:**
1. Og'ir gantel/shtangani ikki qo'lda ushlab tur.
2. Yelkani pastga tort, tanani tik tut.
3. Grip bo'shaguncha ushla.
4. Vaqtni har hafta oshirib bor.

**Nima uchun:** grip — armrestling va tortilishdagi eng ko'p uchraydigan zaif bo'g'in."""),

 ("Stol ustida armrestling mashqi", "reps", 3, 12, 1, """**Ishlaydigan mushaklar:** butun qo'l zanjiri — musobaqa harakatiga eng yaqin

**Bajarish:**
1. Stolda armrestling holatini ol, kamar/rezinani ushla.
2. Bo'g'imni qulflab, yon tomonga tort.
3. Tirsak stoldan uzilmasin.
4. Sekin qaytar, ikkala qo'lda bajar.

**Xavfsizlik:** yelkani hech qachon burma — humerus sinishining asosiy sababi."""),
],

'futbol': [
 ("Dribbling (To'pni olib yurish)", "reps", 3, 10, 1, """**Nimani rivojlantiradi:** to'p nazorati, oyoq tezligi, boshni ko'tarib o'ynash

**Mashq:**
1. 8-10 ta konusni 1 metr oraliqda tik.
2. To'pni oyoqning ichki va tashqi qismi bilan slalom qil.
3. To'p oyoqdan 50 sm dan uzoqlashmasin.
4. Har o'tishda tezlikni oshirib bor.

**Maslahat:** har 2-3 tegishda boshni ko'tarib qara — o'yinda eng muhimi shu."""),

 ("Pass berish (Uzatish)", "reps", 4, 20, 2, """**Nimani rivojlantiradi:** uzatish aniqligi, kuchni o'lchash

**Mashq:**
1. Devor yoki sherikdan 8-10 metr uzoqlikda tur.
2. Oyoqning ICHKI qismi bilan urib uzat.
3. Tayanch oyoq to'p yoniga, barmoq nishonga qaragan bo'lsin.
4. Qaytgan to'pni bitta tegish bilan qaytar.

**Xatolar:** barmoq uchi bilan urish, tanani ochmasdan uzatish."""),

 ("Shooting (Zarbalar)", "reps", 5, 10, 1, """**Nimani rivojlantiradi:** zarba kuchi va aniqligi

**Mashq:**
1. Jarima maydoni chetidan darvozaga ur.
2. Tayanch oyoqni to'p yoniga qo'y, tanani biroz oldinga eg.
3. Oyoq usti (shnurok) bilan to'pning o'rtasidan ur.
4. Zarbadan keyin harakatni davom ettir (follow through).

**Mashq rejasi:** 5 seriya — har biri boshqa burchakdan."""),

 ("To'pni to'xtatish (First touch)", "reps", 3, 20, 2, """**Nimani rivojlantiradi:** birinchi tegish sifati — professional o'yinchining asosiy farqi

**Mashq:**
1. To'pni devorga otib qaytar.
2. Kelayotgan to'pni oyoq/son/ko'krak bilan yumshoq to'xtat.
3. To'pni o'zingdan uzoqqa emas, keyingi harakat tomonga yo'nalt.
4. Har xil balandlikda qaytar.

**Maslahat:** to'p tegishida oyoqni biroz orqaga tortsang — to'p "o'lib" qoladi."""),

 ("Jonglyorlik (Juggling)", "reps", 3, 30, 5, """**Nimani rivojlantiradi:** to'p bilan his, muvozanat, ikkala oyoqni ishlata olish

**Mashq:**
1. To'pni yerdan ko'tarib oyoq usti bilan urib tur.
2. To'p ko'krak balandligidan oshmasin.
3. Oyoqni almashtirib bor.
4. Keyin son va bosh bilan aralashtir.

**Maqsad:** yiqilmasdan 30, keyin 50, keyin 100 marta."""),

 ("Konus orasida slalom", "reps", 4, 8, 1, """**Nimani rivojlantiradi:** chaqqonlik, yo'nalish o'zgartirish tezligi

**Mashq:**
1. 6 ta konusni ziq-zag qilib tik.
2. To'psiz maksimal tezlikda o'tib chiq.
3. Burilishda tanani past tut, qadam qisqa bo'lsin.
4. Keyin to'p bilan takrorla.

**Nima uchun:** o'yindagi harakatlarning 80% i qisqa portlovchi burilishlar."""),

 ("Boshdan zarba (Header)", "reps", 3, 15, 2, """**Nimani rivojlantiradi:** havodagi o'yin, o'zini himoya qila olish

**Mashq:**
1. Sherik to'pni yoysin (yoki devorga otib qaytar).
2. Ko'zni OCHIQ tut, to'pni peshona bilan ur.
3. Bo'yin bilan emas — butun tana bilan oldinga harakatlan.
4. Nishonga yo'naltirib ur.

**Xavfsizlik:** yumshoq to'p bilan boshla, ko'p takrorlama."""),

 ("Tezlik (Sprint)", "reps", 6, 1, 1, """**Nimani rivojlantiradi:** portlovchi tezlik — hujum va himoyaning asosi

**Mashq:**
1. 10 daqiqa qizish (yugurish + cho'zilish).
2. 30 metrni maksimal tezlikda yugur.
3. 90 soniya to'liq dam ol (yurib).
4. 6 marta takrorla.

**Maslahat:** dam yetarli bo'lmasa — bu tezlik emas, chidamlilik mashqiga aylanadi."""),
],

'voleybol': [
 ("Pas (yuqoridan uzatish)", "reps", 4, 25, 5, """**Nimani rivojlantiradi:** aniq uzatish — hujumning boshlanishi

**Mashq:**
1. Devordan 2 metr uzoqda tur.
2. To'pni barmoq uchlari bilan peshona ustida qabul qil.
3. Kaft "savat" shaklida, bosh barmoqlar uchburchak hosil qilsin.
4. Oyoq va qo'l bilan birga itar, devorga uzatib tur.

**Xatolar:** kaft bilan urish (xato), tirsakni yon tomonga ochish."""),

 ("Priyom (pastdan qabul)", "reps", 4, 25, 5, """**Nimani rivojlantiradi:** podacha va hujumni qabul qilish

**Mashq:**
1. Oyoq yelkadan keng, tizza bukilgan, tana past.
2. Qo'lni to'g'ri birlashtir — bilakning tekis qismi bilan qabul qil.
3. Qo'l bilan URMA — oyoq bilan itar.
4. To'pni tik yuqoriga yo'nalt.

**Xatolar:** qo'lni bukish, tik turgan holda qabul qilish."""),

 ("Podacha (Serve)", "reps", 5, 10, 1, """**Nimani rivojlantiradi:** ochko olish imkoniyati — o'yindagi yagona to'liq nazorat qilingan harakat

**Mashq:**
1. Orqa chiziqdan tur, to'pni tik yuqoriga otib qo'y.
2. Qo'lni orqaga tortib, kaftning o'rtasi bilan qattiq ur.
3. To'r ustidan o'tishiga ishonch hosil qil.
4. Maydonning turli burchaklariga yo'nalt.

**Mashq rejasi:** 5 seriya — har seriyada boshqa nishon."""),

 ("Hujum zarbasi (Spike)", "reps", 4, 12, 1, """**Nimani rivojlantiradi:** ochko keltiradigan asosiy zarba

**Mashq:**
1. 3 qadamli yugurish (chap-o'ng-chap, yoki teskari).
2. Ikki qo'lni orqaga yoyib kuchli sakra.
3. Havoda qo'lni orqaga tortib, to'pni tepasidan qattiq ur.
4. Bilakni pastga bukib to'pni maydonga yo'nalt.

**Xatolar:** to'p ostida sakrash (to'p oldida bo'lishi kerak)."""),

 ("Blok", "reps", 4, 15, 2, """**Nimani rivojlantiradi:** himoyaning birinchi qatori

**Mashq:**
1. To'r yonida tur, qo'l ko'krak balandligida tayyor.
2. Yon qadam bilan siljib, ikki oyoqda sakra.
3. Qo'lni to'r ustidan raqib maydoniga uzat, barmoq keng ochilsin.
4. Yumshoq qo'n, darrov o'yinga qayt.

**Xatolar:** to'rga tegish, qo'lni tik yuqoriga ko'tarish (to'p orqaga tushadi)."""),
],

'badminton': [
 ("Clear (uzun zarba)", "reps", 4, 20, 2, """**Nimani rivojlantiradi:** raqibni orqaga surish, vaqt yutish

**Mashq:**
1. Maydon o'rtasida tur, volanni yuqoriga otib qo'y.
2. Raketkani orqaga tortib, to'liq qo'l bilan tepadan ur.
3. Volan raqib maydonining ORQA chizig'iga tushsin.
4. Zarbadan keyin markazga qayt.

**Kalit:** kuch bilakning oxirgi burilishidan chiqadi, yelkadan emas."""),

 ("Drop shot", "reps", 4, 20, 2, """**Nimani rivojlantiradi:** aldov — clear kabi tayyorlanib, yumshoq urish

**Mashq:**
1. Clear zarbasidek to'liq tayyorlan.
2. Tegish paytida bilakni sekinlashtir.
3. Volan to'rning narigi tomoniga yaqin tushsin.
4. Har 3 clear dan keyin 1 drop qil — raqib chalg'iydi.

**Xatolar:** oldindan sekinlashish — raqib payqab qoladi."""),

 ("Smash", "reps", 5, 12, 1, """**Nimani rivojlantiradi:** eng tez va ochko keltiradigan zarba

**Mashq:**
1. Volan tanangdan biroz oldinda va tepada bo'lsin.
2. Tanani burab, to'liq kuch bilan PASTGA ur.
3. Bilakni keskin bukib tugat.
4. Zarbadan keyin darrov markazga qayt.

**Xatolar:** volan bosh ustida bo'lganda urish — burchak yo'qoladi."""),

 ("Podacha (Serve)", "reps", 4, 20, 2, """**Nimani rivojlantiradi:** har rallining boshlanishi — nazorat qilingan yagona zarba

**Mashq:**
1. Qisqa podacha: volan to'rdan sal oshib, oldingi chiziqqa tushsin.
2. Uzun podacha: orqa chiziqqa baland yuborilsin.
3. Ikkalasini bir xil harakat bilan tayyorlab qil.
4. 10 qisqa + 10 uzun.

**Qoida:** zarba bel sathidan pastda bo'lishi shart."""),

 ("Oyoq harakati (Footwork)", "reps", 4, 12, 2, """**Nimani rivojlantiradi:** maydonni qoplash — badmintonda texnikadan ham muhimroq

**Mashq:**
1. Maydonning 6 nuqtasini belgila (2 old, 2 yon, 2 orqa).
2. Markazdan har nuqtaga siljib borib, raketka bilan tegin.
3. Har safar markazga QAYT.
4. Chapla qadam (chassé) ishlat, yugurma.

**Nima uchun:** volanga o'z vaqtida yetib borish — zarbaning yarmi."""),
],

'basketbol': [
 ("Dribbling", "reps", 4, 30, 5, """**Nimani rivojlantiradi:** to'p nazorati, boshni ko'tarib o'ynash

**Mashq:**
1. To'pni barmoq uchlari bilan urib tur (kaft bilan emas).
2. To'p bel sathidan yuqori sakramasin.
3. Boshni ko'tarib, oldinga qarab tur.
4. Chap va o'ng qo'lda navbatma-navbat, keyin almashtirib.

**Xatolar:** to'pga qarab dribbling qilish."""),

 ("Bir joydan otish (Jump shot)", "reps", 5, 15, 2, """**Nimani rivojlantiradi:** asosiy ochko olish usuli

**Mashq:**
1. Oyoq yelka kengligida, otish oyog'i biroz oldinda.
2. To'p barmoqda, tirsak savat ostida to'g'ri chiziqda.
3. Oyoq bilan sakrab, yuqori nuqtada bilakni oldinga bukib ot.
4. Kaft "hovuzga qo'l tashlagandek" osilib qolsin.

**Mashq rejasi:** 5 nuqtadan 15 tadan — jami 75 otish."""),

 ("Shtrafnoy otish (Free throw)", "reps", 5, 10, 1, """**Nimani rivojlantiradi:** bosim ostida barqarorlik

**Mashq:**
1. Har safar BIR XIL tartib: oyoqni joyla, 2 marta urib ol, chuqur nafas.
2. Faqat savatning old halqasiga qara.
3. Bir tekis, sekin harakat bilan ot.
4. 10 tadan 5 seriya — natijani yozib bor.

**Kalit:** shtrafnoy — takrorlanuvchanlik mashqi, kuch mashqi emas."""),

 ("Lay-up", "reps", 4, 20, 2, """**Nimani rivojlantiradi:** savatga yaqin masofadan ochko

**Mashq:**
1. O'ng tomondan: o'ng-chap qadam, chap oyoqda sakra.
2. To'pni o'ng qo'l bilan taxtaning yuqori burchagiga yumshoq tashla.
3. Chap tomondan chap qo'l bilan takrorla.
4. Har tomondan 10 tadan.

**Xatolar:** noto'g'ri oyoqda sakrash, to'pni qattiq urish."""),

 ("Pass berish", "reps", 4, 25, 5, """**Nimani rivojlantiradi:** jamoaviy o'yin tezligi

**Mashq:**
1. Devordan 3 metrda tur.
2. Ko'krak uzatishi: ikki qo'lda ko'krakdan to'g'ri it.
3. Yerdan uzatish: to'p masofaning 2/3 qismida yerga ursin.
4. Har turdan 25 marta, qaytgan to'pni darrov qaytar.

**Kalit:** uzatishdan keyin qo'l barmoqlari tashqariga qaragan bo'lsin."""),
],
}


def main():
    grand_added = grand_skipped = 0
    for cat, items in DATA.items():
        added, skipped = [], []
        for i, (name, ptype, sets, reps, inc, desc) in enumerate(items):
            exists = db.fetch_one(
                "SELECT id FROM sport_exercises WHERE owner_type=:ot AND owner_key=:ok "
                "AND category=:c AND lower(trim(name))=lower(trim(:n)) AND is_deleted=0 LIMIT 1",
                {"ot": OT, "ok": OK, "c": cat, "n": name},
            )
            if exists:
                skipped.append(name)
                continue
            db.execute(
                "INSERT INTO sport_exercises (owner_type, owner_key, category, name, description, "
                "weight, increase_amount, set_count, rep_count, progress_type, progress_mode, "
                "sort_order, is_deleted) "
                "VALUES (:ot,:ok,:c,:n,:d, 0, :inc, :s, :r, :pt, 'manual', :so, 0)",
                {"ot": OT, "ok": OK, "c": cat, "n": name, "d": desc,
                 "inc": inc, "s": sets, "r": reps, "pt": ptype, "so": i},
            )
            added.append(name)
        grand_added += len(added)
        grand_skipped += len(skipped)
        print(f"{cat:12} + {len(added):2}  (o'tkazildi {len(skipped)})")

    db.execute(
        "INSERT INTO sport_sync_meta (owner_type, owner_key, meta_key, meta_value) "
        "VALUES (:ot,:ok,'last_global_update', to_char(clock_timestamp(),'YYYY-MM-DD HH24:MI:SS.US')) "
        "ON CONFLICT (owner_type, owner_key, meta_key) DO UPDATE SET "
        "meta_value = to_char(clock_timestamp(),'YYYY-MM-DD HH24:MI:SS.US'), "
        "updated_at = CURRENT_TIMESTAMP",
        {"ot": OT, "ok": OK},
    )
    print(f"\nJAMI qo'shildi: {grand_added},  o'tkazildi: {grand_skipped}")
    total = db.fetch_one(
        "SELECT count(*) c FROM sport_exercises WHERE owner_type=:ot AND owner_key=:ok "
        "AND is_deleted=0", {"ot": OT, "ok": OK})["c"]
    print(f"Bazadagi jami faol mashq: {total}")


if __name__ == "__main__":
    main()
