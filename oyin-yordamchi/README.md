# O'yin yordamchisi

Telefon ekranidagi o'yinni o'qib, qanday yurishni maslahat beradigan Android agent.
Birinchi o'yin — **Durak (Rstgames, podkidnoy)**, lekin tuzilma boshqa o'yinlarni
qo'shishga moslangan.

## Qatlamlar

```
core/          o'yindan mustaqil: Frame, Roi, GameAdapter, Advice, GameRegistry
cards/         karta o'yinlari uchun umumiy: CardCodec (36/52 lik), CardSet
games/durak/   durak qoidalari + Monte-Carlo miya + maslahatchi
app/           Android: ekranni o'qish va overlay          (hali yo'q)
tools/         ishlab chiqish vositalari: kadr ajratish    (hali yo'q)
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

## Hali qilinmagan

- Ekranni o'qish (`vision`) — Rstgames profili, karta namunalari
- Android ilovasi: MediaProjection + overlay
- O'yin kuzatuvi: bitoga ketgan kartalarni eslab borish
- Maslahat barqarorligi: variantlar teng bo'lganda tanlov o'zgarib turadi
