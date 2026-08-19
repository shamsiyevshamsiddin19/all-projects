"""Hujjat turlari uchun AI promptlari.

Sahifa hajmi hisobi: docx_builder formatiga mos (A4, Times New Roman 14,
1.5 interval, standart hoshiyalar) — 1 bet ≈ 300 so'z.

Katta hujjatlar (kurs ishi, diplom, katta referat) bo'laklab yoziladi:
  chunk_intro  → titul + mundarija + kirish
  chunk_body   → har bir bob alohida
  chunk_final  → xulosa + adabiyotlar
Bo'laklash rejasi chunk_plan() dan olinadi.
"""
from __future__ import annotations
from config import LANGS

# TNR 14, 1.5 interval, 2/2/3/1.5 sm hoshiyada 1 bet ≈ 260 so'z (haqiqiy zichlik).
WORDS_PER_PAGE = 260
# So'ralgan betning bir qismini titul + jadval + grafik + interval egallaydi.
# Shu tufayli MATN nishoni betning ~78% iga mo'ljallanadi (aks holda hujjat
# so'ralganidan uzunroq chiqadi — o'lchov: 10 bet buyurtma → 15 bet chiqardi).
_OVERSHOOT = 0.78

_SYSTEM = """Siz O'zbekiston oliy ta'lim muassasalari talabalari uchun akademik \
hujjatlar tayyorlaydigan yuqori malakali ilmiy muharrirsiz.

QAT'IY QOIDALAR:

1. SIFAT — ENG MUHIM TALAB. Hujjat malakali mutaxassis yoki a'lochi talaba \
yozgandek chuqur, mazmunli va puxta bo'lsin — o'qituvchi o'qiganda "zo'r ish \
tayyorlanibdi" deydigan darajada. Har bir xatboshi asosli fikr, aniq ta'rif, tahlil, \
misol yoki dalil bilan to'lsin; quruq gap, takror va suv taqiqlanadi. Mavzuni har \
tomonlama yoriting: nazariy asoslar, tarixiy rivojlanish, zamonaviy holat, \
O'zbekistondagi amaliyot, olimlar qarashlari, aniq misol va raqamlar.

1a. HAJM — SIFAT ORQALI erishiladi, aksi emas. Ko'rsatilgan hajmni mavzuni CHUQUR \
yoritish bilan yeting (har bo'lim kamida 90%). Aniq bet soniga yetaman deb mazmunni \
YUPQALASHTIRMANG yoki mazmunli gapni kesmang — agar chuqur yoritish biroz ko'proq \
joy olsa, mayli. Sifat har doim bet sonidan ustun turadi. Hech qachon "qisqacha \
aytganda" deb yarim yo'lda to'xtamang.

2. FAQAT HUJJAT MATNI. Javob to'g'ridan-to'g'ri hujjatning birinchi qatoridan \
(sarlavha yoki UDK) boshlansin. Quyidagilar QAT'IY TAQIQLANADI:
- Kirish izohi: "Mana sizga...", "Quyida keltirilgan...", "Hujjatni yozaman...".
- Jarayon sharhi: "Yetarli ma'lumot to'plandi", "Endi yozamiz", "Qidiruv qildim".
- O'z-o'ziga sharh: "Hujjat N so'zdan iborat", "so'z soni", "talab bajarildi".
- Yakuniy izoh yoki savol ("Yana nima kerak?").
- Bo'luvchi chiziqlar ("---", "***") — sarlavhalar bo'limlarni ajratadi, chiziq shart emas.

3. TO'LIQLIK. "[...]", "davomi bor", "va hokazo shu tarzda davom ettiriladi" kabi \
to'ldirilmagan joylar taqiqlanadi. Har bir bo'lim boshidan oxirigacha to'liq yozilsin.

4. AKADEMIK USLUB. Rasmiy-ilmiy uslub, aniq terminologiya, mantiqan bog'langan \
xatboshilar (har biri 4-8 gapdan). Suhbat ohangi va o'quvchiga murojaat ishlatilmasin. \
Matn plagiatdan holi, o'z so'zlari bilan yozilgan bo'lsin.

4a. TABIIY, TIRIK YOZUV (juda muhim — sun'iy/mashina yozgani bilinmasin):
- Gap uzunligini XILMA-XIL qiling: qisqa, aniq gaplarni uzun, murakkab gaplar bilan \
  aralashtiring. Hamma gap bir xil uzunlikda va tuzilishda bo'lishi — mashina yozuvining \
  asosiy belgisi. Ba'zan 5-6 so'zli qisqa gap, ba'zan 25+ so'zli murakkab gap yozing.
- Bir xil o'tish iboralarini TAKRORLAMANG. "Bundan tashqari", "Shuni ta'kidlash joizki", \
  "Shu bilan birga", "Ma'lumki" kabilarni har xatboshida qaytarmang — ularni turli \
  ko'rinishlarda bering yoki umuman ishlatmang, fikrlarni tabiiy bog'lang.
- Mukammal simmetriyadan qoching. Har doim "birinchidan/ikkinchidan/uchinchidan" yoki \
  aniq uch parallel banddan iborat ro'yxat yozaverish sun'iy ko'rinadi. Ba'zan sanang, \
  ba'zan oqim matn bilan bering.
- Xatboshilarni turlicha boshlang — hammasi bir xil qolipда ("X — bu...", "X ..hisoblanadi") \
  boshlanmasin.
- Ortiqcha "silliq" bo'lmang: aniq misollar, sanalar, joy nomlari, aniq raqamlar qo'shing \
  (umumiy "ko'plab omillar mavjud" o'rniga aniq omillarni ayting).
- Klishe xulosalardan qoching: "Xulosa qilib aytganda, yuqorida keltirilganlardan \
  ko'rinib turibdiki..." kabi shablon jumlalar o'rniga mazmunli, aniq yakun yozing.
Maqsad — malakali talaba yoki o'qituvchi qo'li bilan yozilgandek tabiiy o'qilishi.

5. ANIQLIK. Faktlar, sanalar va raqamlar haqiqatga mos bo'lsin. Aniq bilmagan \
statistikani to'qimang — "taxminan", "ma'lumotlarga ko'ra" kabi ehtiyotkor \
ifodalardan foydalaning.

6. ADABIYOTLAR realistik bo'lsin: haqiqiy mualliflar, asar/jurnal nomlari, nashriyot \
va yillar. O'zbek, rus va xorijiy manbalar aralash, alifbo tartibida, raqamlangan.

7. FORMATLASH — quyidagi imkoniyatlardan foydalaning:
   - Sarlavhalar: '#', '##', '###'; ro'yxatlar: '-' va '1.'; **qalin** matn.
   - JADVAL — Markdown formatida, jadvaldan OLDIN alohida qatorda qalin izoh:
     **1-jadval. Jadval nomi**
     | Ko'rsatkich | 2022 | 2023 | 2024 |
     |---|---|---|---|
     | Qiymat | 12,4 | 15,8 | 19,2 |
     (2-6 ustun, 3-8 qator; hujayralar ixcham; raqamlar aniq)
   - FORMULA — alohida qatorda $$ ... $$ ichida, LaTeX yozuvida (tavsiya etiladi):
     $$ x_{1,2} = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a} $$
     $$ \\int_0^\\infty e^{-x^2}\\,dx = \\frac{\\sqrt{\\pi}}{2} $$
     $$ \\bar{x} = \\frac{1}{n}\\sum_{i=1}^{n} x_i $$
     Kasrlar \\frac, ildiz \\sqrt, daraja x^2, indeks x_1, yig'indi \\sum,
     integral \\int, yunon harflari \\alpha \\beta \\pi \\sigma \\Delta.
     Formula Word'da haqiqiy tenglama sifatida chiqadi. Oddiy ifodalarni
     Unicode bilan ham yozish mumkin ($$ S = π·r² $$).
     Formuladan keyingi xatboshida belgilar izohi yozilsin (bu yerda r — radius...).
   - GRAFIK/DIAGRAMMA — chart bloki:
     ```chart
     {"type": "bar", "title": "Grafik nomi", "labels": ["2022", "2023", "2024"], "values": [12, 45, 30], "ylabel": "%"}
     ```
     type: "bar" (ustunli), "line" (chiziqli, dinamika uchun) yoki "pie" (doiraviy, ulushlar uchun).
     labels — qisqa (14 belgigacha), values — faqat raqamlar, 3-8 element.
     Grafikdan KEYIN alohida qatorda: **1-rasm. Grafik nomi**
   - HTML, rasm havolalari va boshqa kod bloklari ishlatilmasin.

8. ILMIY APPARAT. Jadval va rasmlar tartib bilan raqamlansin (1-jadval, 2-jadval;
1-rasm, 2-rasm) va matnda havola qilinsin ("1-jadvalda ko'rsatilganidek...",
"2-rasmdan ko'rinib turibdiki..."). Jadval/grafik shunchaki bezak emas — matndagi
tahlil bilan bog'langan bo'lsin: avval ma'lumot, keyin uning izohi."""

_LANG_NOTE = {
    "uz": "Butun hujjat FAQAT o'zbek tilida (lotin alifbosida) yozilsin.",
    "ru": "Весь документ должен быть написан ТОЛЬКО на русском языке.",
    "en": "Write the ENTIRE document in English only.",
}


def _lang(language: str) -> str:
    return _LANG_NOTE.get(language, _LANG_NOTE["uz"])


def _w(pages: float) -> int:
    """Bet ulushini so'z soniga aylantiradi (kalibrlangan)."""
    return max(100, int(round(pages * WORDS_PER_PAGE * _OVERSHOOT, -1)))


def _hajm(pages: int) -> str:
    total = int(pages * WORDS_PER_PAGE * _OVERSHOOT)
    return (f"UMUMIY HAJM: {pages} bet ≈ {total} so'z "
            f"(Times New Roman 14, 1.5 interval hisobida). "
            f"Bu QAT'IY talab — tayyor matn {int(total * 0.9)} so'zdan kam bo'lmasin.")


# ─────────────────────── Fanga xos talablar ───────────────────────

_SUBJECT_HINTS: list[tuple[tuple[str, ...], str]] = [
    (("matemat", "algebra", "geometr", "analiz", "ehtimol", "statistika fani", "математик", "math"),
     "Har asosiy tushuncha uchun ta'rif, formula ($$...$$) va YECHILGAN MISOL keltiring. "
     "Teoremalarni bayon qilib, isbot g'oyasini ko'rsating. Kamida 4-6 ta formula bo'lsin."),
    (("fizika", "mexanika", "termodinamika", "optika", "elektr", "физик", "physics"),
     "Qonunlarni formulalar ($$...$$) bilan yozing, kattaliklar birliklarini (SI) ko'rsating. "
     "Kamida 3-5 ta formula, fizik kattaliklar jadvali va tajriba natijalari grafigi bo'lsin."),
    (("kimyo", "ximiya", "biokimyo", "химия", "chemistry"),
     "Reaksiya tenglamalarini yozing (masalan: 2H₂ + O₂ → 2H₂O), moddalar xossalarini "
     "jadvalda taqqoslang. Kamida 3-4 ta tenglama/formula bo'lsin."),
    (("informatika", "dastur", "axborot", "kompyuter", "kiber", "sun'iy intellekt", "suniy intellekt",
      "программ", "информатик", "computer", "software", "it "),
     "Algoritmlarni raqamli ro'yxatda bosqichma-bosqich yozing, texnologiyalarni jadvalda "
     "taqqoslang, soha statistikasini grafik bilan ko'rsating. Kod o'rniga algoritm bayoni yozilsin."),
    (("iqtisod", "moliya", "buxgalter", "bank", "soliq", "marketing", "menejment", "biznes",
      "эконом", "финанс", "econom", "finance", "business"),
     "Statistik ma'lumotlarni jadvallarda, dinamikani chiziqli/ustunli grafikda, tarkibni doiraviy "
     "diagrammada ko'rsating. Iqtisodiy formulalar ($$...$$: o'sish sur'ati, rentabellik, ROI) "
     "ishlating. O'zbekiston Statistika agentligi ma'lumotlariga tayangan realistik raqamlar keltiring."),
    (("huquq", "yurid", "qonun", "право", "law", "jinoyat", "fuqarolik"),
     "O'zbekiston Respublikasi qonunlariga aniq havola qiling (qonun nomi, qabul qilingan yili, "
     "tegishli moddalar). Xorijiy tajribani jadvalda taqqoslang. Atamalarni yuridik aniq ishlating."),
    (("tarix", "histor", "истори", "arxeolog"),
     "Sanalar va davrlarni aniq keltiring, muhim voqealar xronologiyasini jadvalda bering, "
     "tarixiy shaxslar va manbalarga tayaning."),
    (("tibbiyot", "medits", "biolog", "anatom", "fiziolog", "farmatsev", "медицин", "biolog"),
     "Tasniflarni jadvalda bering, lotincha atamalarni qavsda ko'rsating, statistik "
     "ma'lumotlarni (kasallanish, samaradorlik) grafik bilan tasvirlab tahlil qiling."),
    (("pedagog", "psixolog", "ta'lim", "talim", "metodika", "педагог", "психолог", "educat"),
     "Metod va yondashuvlarni jadvalda taqqoslang, tajriba-sinov natijalarini grafikda ko'rsating, "
     "olimlarning (jumladan o'zbek pedagog/psixologlari) qarashlariga tayaning."),
    (("til", "adabiyot", "lingvist", "filolog", "tilshunos", "язык", "литератур", "linguist"),
     "Til/matn misollarini keltirib tahlil qiling, hodisalarni jadvalda taqqoslang, "
     "asarlardan qisqa iqtiboslar keltiring (muallif va asar nomi bilan)."),
    (("ekolog", "geograf", "tuproq", "agro", "qishloq"),
     "Hududiy/tabiiy ma'lumotlarni jadvalda bering, ko'rsatkichlar dinamikasini grafikda "
     "ko'rsating, O'zbekiston misollariga tayaning."),
]


def _subject_hint(subject: str) -> str:
    s = (subject or "").lower()
    for keys, hint in _SUBJECT_HINTS:
        if any(k in s for k in keys):
            return hint
    return ("Mavzuga mos joylarda ma'lumotlarni jadvalda tizimlashtiring va "
            "kamida bitta diagramma bilan tasvirlab tahlil qiling.")


def _visuals(doc_type: str, pages: int, subject: str) -> str:
    """Hujjat turiga qarab vizual elementlar kvotasi + fanga xos talab.

    Har jadval/grafik bet egallaydi — shuning uchun kvotalar mo''tadil
    (ortiqcha vizual hujjatni so'ralganidan uzun qiladi)."""
    if pages >= 40:
        quota = "3-4 ta jadval va 2 ta diagramma"
    elif pages >= 20:
        quota = "2-3 ta jadval va 1-2 ta diagramma"
    elif pages >= 12:
        quota = "1-2 ta jadval va 1 ta diagramma"
    else:
        quota = "1 ta jadval va (mavzuga mos bo'lsa) 1 ta diagramma"
    return (f"VIZUAL ELEMENTLAR: butun hujjatda {quota} bo'lishi kerak "
            f"(izohlari va matnda havolasi bilan).\n"
            f"FANGA XOS TALABLAR: {_subject_hint(subject)}")


# ─────────────────────────── Bir martalik promptlar ───────────────────────────

def referat(topic: str, subject: str, author: str, group: str,
            language: str, pages: int) -> tuple[str, str]:
    til = LANGS.get(language, "O'zbek")
    k, b, x = _w(pages * 0.12), _w(pages * 0.24), _w(pages * 0.10)
    user = f"""Mavzu: {topic}
Fan: {subject}
Talaba: {author}
Guruh: {group}
Til: {til}
{_hajm(pages)}
{_lang(language)}
{_visuals('referat', pages, subject)}

Titul varag'i alohida tayyorlanadi — uni YOZMANG. Hujjatni to'g'ridan-to'g'ri
mundarijadan boshlang. Quyidagi ANIQ tuzilmada, har bo'limga ko'rsatilgan hajmda yozing:

## Mundarija
(barcha bo'limlar sarlavhalari, taxminiy bet raqamlari bilan)
## Kirish
(~{k} so'z: mavzuning dolzarbligi, maqsad va vazifalar)
## Asosiy qism
### 1. [mavzuga mos aniq sarlavha o'ylab toping]
(~{b} so'z)
### 2. [aniq sarlavha]
(~{b} so'z)
### 3. [aniq sarlavha]
(~{b} so'z)
## Xulosa
(~{x} so'z: asosiy natijalar, vazifalar bo'yicha yakunlar)
## Foydalanilgan adabiyotlar
(kamida 10 ta manba, APA formatida, raqamlangan)"""
    return _SYSTEM, user


def mustaqil(topic: str, subject: str, author: str, group: str,
             language: str, pages: int) -> tuple[str, str]:
    k, b, x = _w(pages * 0.13), _w(pages * 0.24), _w(pages * 0.11)
    user = f"""Mavzu: {topic}
Fan: {subject}
Talaba: {author}
Guruh: {group}
{_hajm(pages)}
{_lang(language)}
{_visuals('mustaqil', pages, subject)}

Titul varag'i alohida tayyorlanadi — uni YOZMANG. Hujjatni to'g'ridan-to'g'ri
kirishdan boshlang. Quyidagi ANIQ tuzilmada, har bo'limga ko'rsatilgan hajmda yozing:

## 1. Kirish
(~{k} so'z: dolzarblik, maqsad, vazifalar)
## 2. Asosiy qism
### 2.1 [mavzuga mos aniq sarlavha]
(~{b} so'z)
### 2.2 [aniq sarlavha]
(~{b} so'z)
### 2.3 [aniq sarlavha]
(~{b} so'z)
## 3. Xulosa
(~{x} so'z)
## 4. Foydalanilgan adabiyotlar
(kamida 5 ta manba, raqamlangan)"""
    return _SYSTEM, user


def tezis(topic: str, subject: str, author: str, language: str) -> tuple[str, str]:
    user = f"""Mavzu: {topic}
Fan: {subject}
Muallif: {author}
UMUMIY HAJM: 2 bet — ilmiy konferentsiya tezisi, ixcham (≈ 480-560 so'z).
{_lang(language)}

TEZIS — QISQA MATN JANRI. Jadval va diagramma ISHLATMANG (tezis faqat matndan
iborat, ixcham bo'lishi kerak). Zarur bo'lsa faqat 1-2 muhim raqamni matn ichida
keltiring. Formuladan faqat aniq fanlarda (matematika/fizika) va juda zarur bo'lsa
foydalaning.

ILMIY TEZIS formatida yozing:

# {topic}
**{author}**

## Annotatsiya
(80-120 so'z: tadqiqot mohiyati, metod va asosiy natija)
## Kalit so'zlar
(5-7 ta, vergul bilan)
## Kirish
(~120 so'z: muammoning dolzarbligi va qo'yilishi)
## Asosiy natijalar va muhokama
(~220 so'z: eng muhim natijalar, dalillar bilan)
## Xulosa
(~70 so'z)
## Adabiyotlar
(3-4 ta manba, raqamlangan)"""
    return _SYSTEM, user


def maqola(topic: str, subject: str, author: str, language: str, pages: int) -> tuple[str, str]:
    kirish, adab, met, nat, x = (_w(pages * 0.12), _w(pages * 0.20),
                                 _w(pages * 0.15), _w(pages * 0.30), _w(pages * 0.10))
    user = f"""Mavzu: {topic}
Fan sohasi: {subject}
Muallif: {author}
{_hajm(pages)}
{_lang(language)}
{_visuals('maqola', pages, subject)}

ILMIY MAQOLA formatida, har bo'limga ko'rsatilgan hajmda yozing:

UDK: [sohaga mos haqiqiy UDK raqami]
# {topic}
**{author}**

## Annotatsiya
(100-150 so'z, maqolaning qisqacha mazmuni)
## Kalit so'zlar
(6-8 ta)
## Kirish
(~{kirish} so'z: muammoning qo'yilishi va dolzarbligi)
## Adabiyotlar tahlili
(~{adab} so'z: mavzu bo'yicha mavjud tadqiqotlar sharhi, mualliflar nomi bilan)
## Tadqiqot metodologiyasi
(~{met} so'z: qo'llanilgan metodlar va yondashuvlar)
## Natijalar va muhokama
(~{nat} so'z: asosiy natijalar, tahlil, ilmiy izohlar)
## Xulosa
(~{x} so'z)
## Foydalanilgan adabiyotlar
(kamida 10 ta manba, APA yoki GOST, raqamlangan)"""
    return _SYSTEM, user


def kurs_ishi(topic: str, subject: str, author: str, group: str,
              supervisor: str, language: str, pages: int) -> tuple[str, str]:
    k = _w(pages * 0.10)
    bob1, bob2, bob3 = _w(pages * 0.28), _w(pages * 0.28), _w(pages * 0.19)
    x = _w(pages * 0.08)
    user = f"""Mavzu: {topic}
Fan: {subject}
Talaba: {author}, guruh: {group}
Ilmiy rahbar: {supervisor}
{_hajm(pages)}
{_lang(language)}
{_visuals('kurs', pages, subject)}

Titul varag'i alohida tayyorlanadi — uni YOZMANG. To'liq KURS ISHI
tuzilmasida, mundarijadan boshlab, har qismga ko'rsatilgan hajmda yozing:

## Mundarija
(barcha bob va bo'limlar, taxminiy bet raqamlari bilan)
## Kirish
(~{k} so'z: dolzarblik, maqsad, vazifalar, ob'ekt, predmet, metodlar)
## I BOB. [Nazariy asoslarga mos aniq sarlavha]
### 1.1 / 1.2 / 1.3 [aniq sarlavhali 3 ta bo'lim]
(bob jami ~{bob1} so'z)
## II BOB. [Tahliliy qismga mos aniq sarlavha]
### 2.1 / 2.2 / 2.3 [aniq sarlavhali 3 ta bo'lim]
(bob jami ~{bob2} so'z)
## III BOB. [Takliflar va tavsiyalarga mos sarlavha]
### 3.1 / 3.2 [aniq sarlavhali 2 ta bo'lim]
(bob jami ~{bob3} so'z)
## Xulosa
(~{x} so'z: vazifalar bo'yicha yakunlar va tavsiyalar)
## Foydalanilgan adabiyotlar
(kamida 20 ta manba, GOST formatida, raqamlangan)
## Ilovalar
(mavzuga mos 1-2 ta ilova tavsifi)"""
    return _SYSTEM, user


def diplom(topic: str, subject: str, author: str, group: str,
           supervisor: str, language: str, pages: int) -> tuple[str, str]:
    k = _w(pages * 0.08)
    bob1, bob2, bob3 = _w(pages * 0.27), _w(pages * 0.27), _w(pages * 0.21)
    x = _w(pages * 0.08)
    user = f"""Mavzu: {topic}
Yo'nalish: {subject}
Talaba: {author}, guruh: {group}
Ilmiy rahbar: {supervisor}
{_hajm(pages)}
{_lang(language)}
{_visuals('diplom', pages, subject)}

Titul varag'i alohida tayyorlanadi — uni YOZMANG. To'liq BITIRUV MALAKAVIY
ISHI tuzilmasida, annotatsiyadan boshlab, har qismga ko'rsatilgan hajmda yozing:

## Annotatsiya
(o'zbek va rus tillarida, har biri ~120 so'z)
## Mundarija
## Qisqartmalar ro'yxati
## Kirish
(~{k} so'z: dolzarblik, ilmiy yangiligi, maqsad, vazifalar, ob'ekt, predmet, metodlar, amaliy ahamiyati)
## I BOB. [NAZARIY-METODOLOGIK ASOSLARGA MOS SARLAVHA]
### 1.1 / 1.2 / 1.3 [aniq sarlavhali bo'limlar]
(bob jami ~{bob1} so'z)
## II BOB. [TAHLIL VA TADQIQOTGA MOS SARLAVHA]
### 2.1 / 2.2 / 2.3 [aniq sarlavhali bo'limlar]
(bob jami ~{bob2} so'z)
## III BOB. [TAKLIFLAR VA TAVSIYALARGA MOS SARLAVHA]
### 3.1 / 3.2 / 3.3 [aniq sarlavhali bo'limlar]
(bob jami ~{bob3} so'z)
## Xulosa va tavsiyalar
(~{x} so'z)
## Foydalanilgan adabiyotlar
(kamida 30 ta manba, GOST formatida, raqamlangan)
## Ilovalar"""
    return _SYSTEM, user


def slayd(topic: str, subject: str, author: str, slides: int,
          language: str) -> tuple[str, str]:
    sys_sl = """Siz professional taqdimot (prezentatsiya) dizayneri va kontent
yozuvchisiz. Turli maketlardan (layout) foydalanib xilma-xil, professional
taqdimot tuzasiz — zerikarli bir xil "sarlavha + ro'yxat" slaydlar EMAS.

MAKET TURLARI ("layout" maydonida ko'rsating):
- "cover" — FAQAT 1-slayd. title=mavzu nomi, image_query=mavzuga mos
  2-4 ta INGLIZCHA kalit so'z (fon-foto qidirish uchun, masalan
  "artificial intelligence network" yoki "ancient manuscript library").
- "content" — standart: sarlavha + 3-5 ta qisqa mazmunli fikr (points).
- "chart" — ma'lumot/statistika tahlili. "chart" maydoni:
  {"type":"bar yoki line yoki pie","title":"...","labels":["...","..."],
  "values":[raqamlar],"ylabel":"..."} + 1-2 ta qisqa xulosa (points).
- "two_col" — ikki narsani taqqoslash. "columns":
  [{"title":"Chap sarlavha","points":["...","..."]},
   {"title":"O'ng sarlavha","points":["...","..."]}]
- "stat" — bitta muhim raqam/faktni ko'zga tashlash. "value":"78%" (yoki
  raqam), "label":"qisqa izoh (5-8 so'z)".
- "quote" — muhim iqtibos yoki tamoyil. "quote_text":"...",
  "quote_author":"kim aytgan yoki qaysi manba".
- "image" — mavzuga mos illyustrativ fon-foto. title + image_query
  (2-4 ta inglizcha so'z) + 1 ta qisqa points.
- "section" — BO'LIM AJRATUVCHI (katta raqamli sarlavha). Yangi katta
  mavzu/bo'lim boshlanishida ishlating. title=bo'lim nomi + 1 ta qisqa
  points (ixtiyoriy izoh).
- "steps" — JARAYON yoki ALGORITM bosqichlari (3-4 raqamlangan qadam).
  points = har bir bosqich tavsifi (ketma-ket). Algoritm, usul, bosqichli
  jarayon tushuntirilganda ideal.
- "cards" — KATEGORIYALAR / XUSUSIYATLAR / TURLAR (2-4 ta karta).
  points = har bir element (qisqa: 4-12 so'z). Tasnif, tur, afzallik
  sanashda ishlating.
- "timeline" — VAQT O'QI / XRONOLOGIYA / RIVOJLANISH bosqichlari (3-4 ta).
  points = har bir davr/voqea. Tarix, evolyutsiya, kelajak bosqichlari uchun.
- "end" — FAQAT oxirgi slayd. title="Xulosa" yoki "E'tiboringiz uchun
  rahmat!", 2-3 ta asosiy xulosa (points).

QOIDALAR:
- 1-slayd har doim "cover", oxirgi slayd har doim "end".
- XILMA-XILLIK MAJBURIY: kamida 5 xil turdagi layout ishlating. Faqat
  "content" slaydlardan iborat zerikarli taqdimot TAQIQLANADI.
- Qolgan slaydlar orasida KAMIDA bittadan: "chart" (statistika),
  "steps" YOKI "cards" (tuzilma), "two_col" YOKI "stat" (taqqoslash/fakt)
  bo'lsin. Mavzuga mos bo'lsa "section", "timeline", "quote" ham qo'shing.
- Bir xil layout ketma-ket 2 martadan ortiq kelmasin.
- Maketni MAZMUNGA qarab tanlang: algoritm/usul → "steps", tasnif/turlar →
  "cards", tarix/bosqich → "timeline", yirik bo'lim boshi → "section".
- "image_query" FAQAT inglizcha va umumiy, topilishi oson so'zlar —
  mavzuning tarjimasi emas, VIZUAL tasvirlanadigan narsa (masalan mavzu
  "RSA shifrlash algoritmi" bo'lsa image_query="cryptography lock security").
- "points" har biri 6-14 so'z, mazmunli fikr (fakt/ta'rif/misol), shunchaki
  mavzu nomi emas.
- "notes" — ma'ruzachi uchun 1-2 qisqa gap (ixtiyoriy, barcha layoutlarda).
MUHIM: JSON TO'LIQ va YOPIQ bo'lishi shart — oxirgi slaydgacha yozib,
massivni "]" bilan tugating. FAQAT JSON qaytaring — markdown, izohsiz."""

    user = f"""Mavzu: {topic}
Fan: {subject}
Muallif: {author}
Slaydlar soni: {slides} (aynan shuncha bo'lsin)
{_lang(language)}

{slides} ta slayd uchun JSON massiv qaytaring, yuqoridagi maket turlaridan
foydalanib:
[
  {{"slide": 1, "layout": "cover", "title": "{topic}", "image_query": "...", "notes": "..."}},
  {{"slide": 2, "layout": "content", "title": "...", "points": ["...", "..."], "notes": "..."}},
  {{"slide": 3, "layout": "chart", "title": "...", "chart": {{"type": "bar", "title": "...", "labels": ["...", "..."], "values": [10, 20], "ylabel": "..."}}, "points": ["..."]}},
  {{"slide": 4, "layout": "two_col", "title": "...", "columns": [{{"title": "...", "points": ["...", "..."]}}, {{"title": "...", "points": ["...", "..."]}}]}},
  {{"slide": 5, "layout": "steps", "title": "...", "points": ["1-bosqich tavsifi", "2-bosqich", "3-bosqich", "4-bosqich"]}},
  {{"slide": 6, "layout": "cards", "title": "...", "points": ["Birinchi tur", "Ikkinchi tur", "Uchinchi tur", "To'rtinchi tur"]}},
  {{"slide": 7, "layout": "timeline", "title": "...", "points": ["Birinchi davr", "Ikkinchi davr", "Uchinchi davr"]}},
  {{"slide": 8, "layout": "section", "title": "Yangi bo'lim nomi", "points": ["qisqa izoh"]}},
  ...
  {{"slide": {slides}, "layout": "end", "title": "Xulosa", "points": ["...", "...", "..."]}}
]

Mavzuni to'liq qamrab oling, mantiqiy ketma-ketlikda: kirish/muammo →
asosiy tushunchalar → tahlil/statistika/taqqoslash → xulosa."""
    return sys_sl, user


def krasword(topic: str, language: str, count: int = 25) -> tuple[str, str]:
    sys_kr = """Siz krossvord so'zlari generatorisiz.
FAQAT to'g'ri JSON qaytaring — markdown belgilarisiz, izohsiz."""
    user = f"""Mavzu: {topic}
{_lang(language)}

Bu mavzu bo'yicha {count} ta so'z va tarifni JSON da qaytaring:
[
  {{"word": "SOZ", "clue": "Bu so'zning tarifi"}},
  ...
]

Shartlar:
- So'zlar KATTA HARFLARDA, faqat harflardan iborat (bo'sh joy, tire, raqamsiz)
- So'zlar 3-12 harf uzunlikda, bitta so'zdan iborat
- Har bir so'z mavzu bilan bevosita bog'liq
- Tariflar qisqa va aniq (7-15 so'z), so'zning o'zi tarifda qatnashmasin
- So'zlar takrorlanmasin"""
    return sys_kr, user


# ─────────────────────── Bo'laklab generatsiya (katta ishlar) ───────────────────────

# Har tur uchun: hujjat nomi, qism ulushlari, boblar tavsifi, manba talabi
_CHUNK_SPECS = {
    "referat": {
        "title": "REFERAT",
        "intro": 0.13,
        "chapters": [
            ("Asosiy qismning 1-bo'limi (## 1. sarlavha bilan)", 0.25),
            ("Asosiy qismning 2-bo'limi (## 2. sarlavha bilan)", 0.25),
            ("Asosiy qismning 3-bo'limi (## 3. sarlavha bilan)", 0.22),
        ],
        "final": 0.15,
        "sources": "kamida 10 ta manba (APA formatida)",
        "intro_extra": "",
        "kirish_talab": "dolzarblik, maqsad va vazifalar",
    },
    "mustaqil": {
        "title": "MUSTAQIL ISH",
        "intro": 0.13,
        "chapters": [
            ("Asosiy qismning 2.1-bo'limi (### 2.1 sarlavha bilan)", 0.25),
            ("Asosiy qismning 2.2-bo'limi (### 2.2 sarlavha bilan)", 0.25),
            ("Asosiy qismning 2.3-bo'limi (### 2.3 sarlavha bilan)", 0.22),
        ],
        "final": 0.15,
        "sources": "kamida 5 ta manba",
        "intro_extra": "",
        "kirish_talab": "dolzarblik, maqsad va vazifalar",
    },
    "maqola": {
        "title": "ILMIY MAQOLA",
        "intro": 0.17,
        "chapters": [
            ("Adabiyotlar tahlili (## sarlavha bilan)", 0.22),
            ("Tadqiqot metodologiyasi (## sarlavha bilan)", 0.16),
            ("Natijalar va muhokama (## sarlavha bilan)", 0.30),
        ],
        "final": 0.15,
        "sources": "kamida 10 ta manba (APA yoki GOST)",
        "intro_extra": ("Boshlanishda UDK raqami, ## Annotatsiya (100-150 so'z) "
                        "va ## Kalit so'zlar (6-8 ta) ham yozilsin."),
        "kirish_talab": "muammoning qo'yilishi va dolzarbligi",
    },
    "kurs": {
        "title": "KURS ISHI",
        "intro": 0.11,
        "chapters": [
            ("I BOB — nazariy asoslar (## I BOB sarlavhasi, ### 1.1, 1.2, 1.3 bo'limlari bilan)", 0.28),
            ("II BOB — tahliliy qism (## II BOB sarlavhasi, ### 2.1, 2.2, 2.3 bo'limlari bilan)", 0.28),
            ("III BOB — takliflar va tavsiyalar (## III BOB sarlavhasi, ### 3.1, 3.2 bo'limlari bilan)", 0.19),
        ],
        "final": 0.14,
        "sources": "kamida 20 ta manba (GOST formatida)",
        "intro_extra": "",
        "kirish_talab": "dolzarblik, maqsad, vazifalar, ob'ekt, predmet, metodlar",
    },
    "diplom": {
        "title": "BITIRUV MALAKAVIY ISHI",
        "intro": 0.11,
        "chapters": [
            ("I BOB — nazariy-metodologik asoslar (## I BOB sarlavhasi, ### 1.1, 1.2, 1.3 bilan)", 0.26),
            ("II BOB — tahlil va tadqiqot (## II BOB sarlavhasi, ### 2.1, 2.2, 2.3 bilan)", 0.26),
            ("III BOB — takliflar va tavsiyalar (## III BOB sarlavhasi, ### 3.1, 3.2, 3.3 bilan)", 0.22),
        ],
        "final": 0.15,
        "sources": "kamida 30 ta manba (GOST formatida)",
        "intro_extra": ("Boshlanishda ## Annotatsiya (o'zbek va rus tillarida, har biri ~120 so'z) "
                        "va ## Qisqartmalar ro'yxati ham yozilsin."),
        "kirish_talab": ("dolzarblik, ilmiy yangiligi, maqsad, vazifalar, ob'ekt, "
                         "predmet, metodlar, amaliy ahamiyati"),
    },
}


def chunkable(doc_type: str) -> bool:
    return doc_type in _CHUNK_SPECS


def chunk_plan(doc_type: str, pages: int) -> list[tuple[str, float]]:
    """[(qism nomi, bet soni), ...] — birinchi element intro, oxirgisi final."""
    s = _CHUNK_SPECS[doc_type]
    plan = [("intro", pages * s["intro"])]
    plan += [(label, pages * share) for label, share in s["chapters"]]
    plan += [("final", pages * s["final"])]
    return plan


def chunk_intro(doc_type: str, topic: str, meta: str, language: str,
                pages: int, part_pages: float) -> tuple[str, str]:
    s = _CHUNK_SPECS[doc_type]
    kirish_w = _w(part_pages * 0.7)
    chapters_txt = "\n".join(
        f"  - {label} (~{max(1, round(pages * share))} bet)"
        for label, share in s["chapters"])
    user = f"""{s['title']} tayyorlanmoqda. {_hajm(pages)}
Hujjat bo'lak-bo'lak yoziladi — hozir FAQAT BOSHLANISH QISMINI yozing.

Mavzu: {topic}
{meta}
{_lang(language)}

Titul varag'i alohida tayyorlanadi — uni YOZMANG.
Yozilishi kerak bo'lgan qismlar:
{("1. " + s['intro_extra']) if s['intro_extra'] else "1. (qo'shimcha talab yo'q)"}
2. ## Mundarija — BARCHA bob va bo'limlar uchun mavzuga mos ANIQ sarlavhalar
   o'ylab toping (keyingi qismlar aynan shu mundarija asosida yoziladi).
   Rejalashtirilgan tuzilma:
{chapters_txt}
   Mundarijaga Kirish, Xulosa va Foydalanilgan adabiyotlar ham kiritilsin.
3. ## Kirish (~{kirish_w} so'z): {s['kirish_talab']}.

Boshqa hech qanday bo'lim yozmang — boblar keyingi bosqichlarda yoziladi."""
    return _SYSTEM, user


def chunk_body(doc_type: str, topic: str, language: str, intro_text: str,
               chapter_label: str, part_pages: float,
               done_labels: list[str], subject: str = "") -> tuple[str, str]:
    s = _CHUNK_SPECS[doc_type]
    words = _w(part_pages)
    done = ", ".join(done_labels) if done_labels else "hali yo'q"
    # Tahliliy boblarda (2-bob va keyingilari) jadval/grafik majburiy
    analytic = bool(done_labels)
    visual = ("- Bobda kamida 1 ta jadval VA 1 ta diagramma (```chart```) bo'lsin — "
              "izohi (**N-jadval. ...** / **N-rasm. ...**) va matnda havolasi bilan. "
              "Raqamlashni hujjat bo'yicha davom ettiring."
              if analytic else
              "- Mavzuga mos bo'lsa jadval yoki formula ishlating (izohi bilan).")
    user = f""""{topic}" mavzusidagi {s['title']} bo'lak-bo'lak yozilmoqda.

Hujjatning tasdiqlangan boshlanish qismi (mundarija va kirish):
---
{intro_text}
---

Allaqachon yozilgan qismlar: {done}.

Endi FAQAT quyidagi qismni yozing:
{chapter_label}

HAJM: ~{max(1, round(part_pages))} bet ≈ {words} so'z — QAT'IY talab, kamida {int(words * 0.9)} so'z.
{_lang(language)}
FANGA XOS TALABLAR: {_subject_hint(subject)}

Qoidalar:
- Mundarijadagi tegishli sarlavhalarni AYNAN o'sha ko'rinishda ishlating.
- Javob to'g'ridan-to'g'ri qism sarlavhasidan boshlansin.
- Oldingi qismlar mazmunini takrorlamang, keyingi qismlar mavzusiga kirmang.
- Har bir bo'limni chuqur yoriting: ta'riflar, tahlil, misollar, olimlar fikri.
{visual}"""
    return _SYSTEM, user


def chunk_extend(doc_type: str, topic: str, language: str,
                 chapter_label: str, chapter_text: str, add_words: int,
                 subject: str = "") -> tuple[str, str]:
    """Qisqa chiqqan bobni chuqurlashtirish (davom ettirish)."""
    s = _CHUNK_SPECS[doc_type]
    no_visual = ("|" not in chapter_text) and ("```chart" not in chapter_text)
    visual = ("\n- Qo'shimchada kamida 1 ta jadval yoki diagramma (```chart```) bo'lsin "
              "(izohi va matnda havolasi bilan)." if no_visual else "")
    user = f""""{topic}" mavzusidagi {s['title']} uchun yozilgan quyidagi qism
({chapter_label}) hajm jihatidan yetarli emas:
---
{chapter_text}
---

Bu qismni DAVOM ETTIRING va chuqurlashtiring: yana ~{add_words} so'z YANGI mazmun qo'shing.
{_lang(language)}
FANGA XOS TALABLAR: {_subject_hint(subject)}

Qoidalar:
- Yuqoridagi matnni takrorlamang va qayta yozmang — faqat yangi mazmun.
- Mavjud bo'limlar doirasida chuqurlashtiring: qo'shimcha tahlil, aniq misollar,
  statistika, olimlar fikri, xorijiy tajriba, O'zbekistondagi holat va amaliyot.
- Javob to'g'ridan-to'g'ri yangi xatboshidan boshlansin (bob sarlavhasini qaytarmang;
  zarur bo'lsa mavjud bo'lim ichiga mos keladigan davom yozing).
- Umumiy xulosa yozmang — bu bob oxiriga qo'shiladigan davom, xulosa alohida yoziladi.{visual}"""
    return _SYSTEM, user


def chunk_final(doc_type: str, topic: str, language: str, intro_text: str,
                part_pages: float, done_labels: list[str]) -> tuple[str, str]:
    s = _CHUNK_SPECS[doc_type]
    x_w = _w(part_pages * 0.6)
    ilova = ("\n## Ilovalar — mavzuga mos 1-2 ta ilova tavsifi."
             if doc_type in ("kurs", "diplom") else "")
    user = f""""{topic}" mavzusidagi {s['title']} bo'lak-bo'lak yozilmoqda.

Hujjatning boshlanish qismi (mundarija va kirish):
---
{intro_text}
---

Yozib bo'lingan qismlar: {", ".join(done_labels)}.

Endi FAQAT YAKUNIY QISMNI yozing:
## Xulosa (~{x_w} so'z) — kirishda qo'yilgan har bir vazifa bo'yicha aniq yakunlar,
asosiy natijalar va amaliy tavsiyalar.
## Foydalanilgan adabiyotlar — {s['sources']}, alifbo tartibida, raqamlangan,
realistik (haqiqiy mualliflar, nashriyotlar, yillar).{ilova}
{_lang(language)}

Javob to'g'ridan-to'g'ri "## Xulosa" sarlavhasidan boshlansin."""
    return _SYSTEM, user


# ─────────────────────── Web search va revizyon ───────────────────────

SEARCH_NOTE = """
INTERNET QIDIRUVI: sizda web_search vositasi bor. Undan foydalaning:
- Adabiyotlar ro'yxati uchun REAL manbalarni toping (kitob/maqola nomi, muallif,
  yil, jurnal yoki URL) va faqat topilganlarini keltiring.
- Statistik ma'lumotlarni rasmiy manbalardan oling (stat.uz, lex.uz, jahon tashkilotlari)
  va manba nomi + yilini matnda ko'rsating.
- Topilmagan ma'lumotni TO'QIMANG — topilmasa, klassik darslik/monografiyalarni yozing.
Qidiruvlar soni cheklangan — eng muhim faktlar uchun ishlating.
MUHIM: qidiruv jarayonini IZOHLAMANG ("ma'lumot topdim", "endi yozaman", "qidiruv
qildim" kabi gaplarni YOZMANG). Qidiruvdan so'ng to'g'ridan-to'g'ri hujjat matnini
(sarlavhadan) boshlang — birinchi qatordayoq."""


def revise(doc_label: str, topic: str, source_text: str, feedback: str,
           language: str) -> tuple[str, str]:
    """Tayyor hujjatni o'qituvchi/foydalanuvchi izohi bo'yicha qayta ishlash."""
    user = f"""Quyida "{topic}" mavzusida tayyorlangan {doc_label} matni bor:
---
{source_text}
---

FOYDALANUVCHI IZOHI (o'qituvchi talabi):
{feedback}

VAZIFA: hujjatni shu izohga ko'ra QAYTA ISHLANG va TO'LIQ YANGILANGAN matnni qaytaring.
{_lang(language)}

Qoidalar:
- Izohga aloqador qismlarnigina o'zgartiring/to'ldiring; qolgan matnni AYNAN saqlang
  (qisqartirmang, qayta yozmang).
- Hujjat tuzilmasi, sarlavhalar, jadval/formula/grafik formatlash qoidalari o'zgarmasin.
- Javob — to'liq hujjat matni, birinchi qatordan boshlab, izohsiz."""
    return _SYSTEM, user
