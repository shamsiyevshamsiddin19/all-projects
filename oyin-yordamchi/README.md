# O'yin yordamchisi

Telefon ekranidagi o'yinni o'qib, qanday yurishni maslahat beradigan Android agent.
Birinchi o'yin — **Durak (Rstgames, podkidnoy)**, lekin tuzilma boshqa o'yinlarni
qo'shishga moslangan.

## Qatlamlar

```
core/          o'yindan mustaqil: Frame, Roi, GameAdapter, Advice, GameRegistry
cards/         karta o'yinlari uchun umumiy: CardCodec (36/52 lik), CardSet
games/durak/   durak qoidalari + Monte-Carlo miya + maslahatchi
app/           Android: ekranni o'qish va overlay
desktop/       kompyuterda sinash: PNG kadrlarni o'qish va kuzatish
tools/         ishlab chiqish vositalari (Python): kadr ajratish,
               burchak topish, guruhlash, tanish, o'lchov
```

Qoida: **pastki qatlam yuqorisini bilmaydi.** `core` durakni bilmaydi, `cards`
qaysi o'yin ekanini bilmaydi, Android ilovasi esa faqat `core` bilan gaplashadi.

## Yangi o'yin qo'shish

1. `games/<nom>/` moduli ochiladi, `settings.gradle.kts` ga qo'shiladi.
2. `GameAdapter` amalga oshiriladi — uchta narsa:
   - `observe(frame, previous)` — ekrandan holatni o'qish
   - `advise(state)` — maslahat
   - `packageNames` — qaysi Android ilovaga tegishli
3. `GameRegistry.register(...)` qilinadi. Android ilovasiga tegilmaydi.

Karta o'yini bo'lsa `cards` qatlami tayyor: `CardCodec(DECK36 / DECK52)` va
`CardSet` (64 bitli tez to'plam).

## Durak miyasi

Ikki qatlam:

- **`HeuristicBot`** — qoidali, tez, asos sifatida o'lchov uchun.
- **`PimcBot`** — raqib qo'lini noma'lum kartalardan ko'p marta taxmin qilib,
  har variantni o'ynab ko'radi (Perfect Information Monte Carlo).
  Vaqt chegarasi bor (`budgetMillis`) — telefonda kechikmaydi.

Faqat ko'rinadigan ma'lumot ishlatiladi: o'z qo'li, stol, kozir, zaxira soni,
raqiblardagi karta soni, bitoga ketganlar. Shuning uchun simulyatsiyadagi
natija haqiqiy o'yinda ham o'rinli.

## O'lchovlar (2026-10-05)

| Sinov | Natija |
|---|---|
| Qoida sinovi: 10 000 o'yin | 0.7 s, karta yo'qolmadi, tsikl yo'q |
| Monte-Carlo (40 taxmin) vs qoidali, 2 kishi | durak bo'lish **30%** (teng = 50%) |
| Monte-Carlo (150 taxmin) vs qoidali, 2 kishi | durak bo'lish **26.5%** |
| Monte-Carlo (60 taxmin) vs qoidali, 3 kishi | durak bo'lish **17%** (teng = 33%) |

## Buyruqlar

```bash
./gradlew :games:durak:test                          # qoida testlari
./gradlew :games:durak:run --args="10000 3"          # 10 000 o'yin, qoida sinovi
./gradlew :games:durak:benchmark --args="200 3 60"   # Monte-Carlo o'lchovi
./gradlew :games:durak:demo                          # maslahat qanday ko'rinadi
```

## Ekranni o'qish (ko'z)

Zona-zona sozlash o'rniga **karta burchagi** qidiriladi: toza oq fonda
raqam, uning tagida mast. Shu naqsh qo'lda ham, stolda ham, kozir kartada ham
bir xil, shuning uchun bitta mantiq uchalasiga yetadi.

Karta nomlari qo'lda emas, **guruhlash** orqali o'rgatilgan: 2944 ta belgi
o'xshashligiga qarab guruhlanadi, keyin har guruhga bitta nom beriladi.
Shu bilan 36 ta kartani belgilash o'rniga ~50 ta guruh nomlanadi.

Kartadan tashqari yana uch narsa o'qiladi:

- **Zaxira soni** - chap chetdagi oq raqam. Sonning ko'tarilishi (masalan 36)
  yangi o'yin boshlanganini bildiradi.
- **Hodisa pufakchalari** - "I take", "Pass", "Done". Pufakcha joyi KIM ekanini,
  matni esa NIMA bo'lganini aytadi. Bu kuzatuv uchun eng ishonchli manba:
  kartalar harakatidan taxmin qilish shart emas.
- **Kozir masti** - yonboshlab yotgan kozir kartasidan.

O'lchovlar (348 kadr, bitta to'liq 3 kishilik o'yin videosi):

| Mezon | Natija |
|---|---|
| Tanilgan belgi | 2809 ta, noma'lumi **2.2%** |
| Kozir karta to'g'riligi | **199/199 = 100%** (videoda kozir doim 8♣ edi) |
| Bir kadrda takrorlangan karta | **0 ta** |
| O'tkazib yuborish (qo'l / stol) | **0.99% / 0.60%** |
| Zaxira soni | kamayish tartibi buzilmagan, 18 dan 2 gacha |
| Hodisalar | 10 ta hodisa, ishonch 0.97-1.00 |

Oxirgi mezonlar qo'lda belgilashsiz o'lchanadi: karta o'z-o'zidan ikkilanmaydi,
g'oyib bo'lib qaytmaydi, zaxira esa ko'paymaydi - bunday hodisaning o'zi xato.
Ikki joyda chiqqan karta "noma'lum" ga chiqariladi: maslahatchiga xato karta
berishdan ko'ra bilmaslik xavfsizroq.

## Kuzatuvchi

Bitta kadr faqat "hozir nima ko'rinyapti" ni aytadi. O'yin uchun tarix kerak:
**bitoga ketgan kartalar ekranda umuman ko'rinmaydi**, lekin ularsiz maslahat zaif.
Shuning uchun ilova o'yinni boshidan kuzatib boradi.

Kuzatuvchi bitta o'yin videosidan shunday jurnal tikladi:

```
   1.5s  kozir 8C
  14.0s  chap oldi: 1 karta
  37.0s  bito: 6D 6S 7C 7D 7H 8H AS QD (jami 8)
  44.5s  ZIDDIYAT: 6D bitodan qaytdi - xato o'qilgan, bitodan chiqarildi
  65.0s  bito: 10D 10S 6D 6H 9D 9H 9S (jami 14)
 134.0s  men oldim: 9 karta
 172.5s  YANGI O'YIN (zaxira 2 -> 36)
```

Uchta narsa o'zini o'zi tekshiradi:

- **Bitoga ketgan karta qaytib kelmaydi.** Kelsa - biror joyda xato o'qilgan;
  kuzatuvchi ko'rinayotganiga ishonib, xulosani tuzatadi.
- **Saqlanish qonuni.** 36 tadan ko'ringanini ayirsak, qolgani raqiblarda.
  160-kadrda: 5 (qo'l) + 2 (stol) + 13 (bito) + 2 (zaxira) + 14 (raqiblar) = 36.
- **Zaxira faqat kamayadi.** Ko'tarilsa - yangi o'yin boshlangan.

Stolda qaysi karta qaysini qoplaganini joylashuv aytadi: qoplagan karta
hujum kartasidan `dx≈0.45h, dy≈0.19h` siljib tushadi va bu juda barqaror.

## Zanjir to'liq ishlaydi

```bash
ARGS=$(python3 tools/maslahat_ber.py 160 hujum | tail -1)
./gradlew :games:durak:maslahat --args="$ARGS"
```

```
kozir ♣ · zaxira 2 · bitoda 13 · hujum
qo'lim: 10♣ J♣ J♦ Q♥ K♣
stol: 6♠/K♠

  >>> BITO BOS
      qo'shimcha karta berish ziyon | 71% omon
```

Ya'ni: haqiqiy o'yin kadri -> kartalar va hodisalar -> kuzatilgan holat
(ko'rinmaydigan bito bilan) -> yurish maslahati.

## Android ilovasi

```bash
./gradlew :app:assembleDebug
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

APK **1.5 MB**, boshqa kutubxonaga tayanmaydi - faqat Android SDK va loyihaning
o'z qatlamlari. **Internet ruxsati yo'q**: ilova hech qayerga hech narsa
yubora olmaydi, hammasi telefon ichida hisoblanadi.

Ikki ruxsat so'raydi: ekran ustida oyna ochish va ekranni o'qish. Ikkalasini
ham foydalanuvchi o'zi tasdiqlaydi. Overlay bosishlarni o'tkazib yuboradi -
o'yinni bloklamaydi va hech narsani bosmaydi.

Ekran sekundiga ikki marta o'qiladi, lekin tahlil faqat ekran **tinchlanganda**
bajariladi: karta uchib kelayotgan paytda o'qilsa holat chalkashadi. Ekran
o'zgarmagan bo'lsa umuman ishlamaydi - batareya uchun.

Tanish 864 piksel kenglikda o'rgatilgan, shuning uchun ekran o'sha kenglikka
keltirib o'qiladi (tizim o'zi kichiklashtiradi).

> Agar `dl.google.com` ga ulanib bo'lmasa, SDK ichidagi vositani ko'rsatish mumkin:
> `-Pandroid.aapt2FromMavenOverride=$ANDROID_HOME/build-tools/36.0.0/aapt2`

## Kotlin va Python bir xil ishlaydi

Ko'z qismi avval Python'da yozilib, keyin Kotlin'ga ko'chirildi. Ko'chirish
taxmin bilan emas, **o'lchov bilan** tasdiqlandi: ikkala versiya o'sha 348 kadrni
o'qib, har birida **bir xil natija** beradi (348/348). Kuzatuvchi ham shunday -
o'yin jurnali qatorma-qator bir xil.

Shablon banki bitta sodda ikkilik formatda saqlanadi va ikkala til ham o'shani
o'qiydi, ya'ni haqiqat bitta joyda. Python vositalari yangi shablon o'rgatish
va Kotlin tarafini ikkinchi amalga oshirish bilan solishtirish uchun qoladi.

## Hali qilinmagan

- **Haqiqiy telefonda sinalmagan** - APK yig'ildi, lekin qurilmada ishlatilmadi

- Ekranni o'qish (`vision`) — Rstgames profili, karta namunalari
- Android ilovasi: MediaProjection + overlay
- O'yin kuzatuvi: bitoga ketgan kartalarni eslab borish
- Maslahat barqarorligi: variantlar teng bo'lganda tanlov o'zgarib turadi
