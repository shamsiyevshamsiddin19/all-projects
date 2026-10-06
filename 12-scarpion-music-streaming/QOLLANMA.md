# SCARPION MUSIC — Foydalanuvchi qo'llanmasi

Ijrochi, albom va qo'shiq qo'shish bo'yicha to'liq yo'riqnoma.

---

## Mundarija

1. [Tizimga kirish](#1-tizimga-kirish)
2. [Ijrochi qo'shish](#2-ijrochi-qoshish)
3. [Albom qo'shish (qo'lda)](#3-albom-qoshish-qolda)
4. [Albomga qo'shiq qo'shish](#4-albomga-qoshiq-qoshish)
5. [Katalogdan tezkor import (tavsiya etiladi)](#5-katalogdan-tezkor-import-tavsiya-etiladi)
6. [Tahrirlash va o'chirish](#6-tahrirlash-va-ochirish)
7. [Egalik qoidalari — kim nimani o'zgartira oladi](#7-egalik-qoidalari--kim-nimani-ozgartira-oladi)
8. [Qidiruv va filtr](#8-qidiruv-va-filtr)
9. [Tez-tez uchraydigan xatoliklar](#9-tez-tez-uchraydigan-xatoliklar)

---

## 1. Tizimga kirish

Sayt **yopiq**: hech narsa ko'rish uchun ham avval tizimga kirish kerak.

1. Sayt ochilganda avtomatik `/kirish/` sahifasiga yo'naltirilasiz.
2. Akkauntingiz yo'q bo'lsa — **"Ro'yxatdan o'tish"** havolasini bosing:
   - Foydalanuvchi nomi (harf, raqam va `@ . + - _` belgilari)
   - E-pochta
   - Parol (kamida 8 ta belgi, faqat raqamdan iborat bo'lmasin)
3. Yoki **"Google bilan kirish"** tugmasi orqali bir bosishda kiring.
4. Ro'yxatdan o'tgach, darhol tizimga kiritilasiz — qayta parol so'ralmaydi.

> Kirgandan keyin qaysi sahifaga borishni xohlagan bo'lsangiz, o'sha yerga qaytarilasiz.

---

## 2. Ijrochi qo'shish

Agar kerakli ijrochi katalogda umuman yo'q bo'lsa (masalan, mahalliy yoki juda yangi ijrochi), uni qo'lda qo'shing.

**Manzil:** yuqori menyu → **"+ IJROCHI"** (yoki to'g'ridan-to'g'ri `/ijrochi/qoshish/`)

| Maydon | Majburiymi? | Izoh |
|---|---|---|
| Ijrochi nomi | ✅ Ha | Katalogdagi bilan bir xil yozing (masalan `Yulduz Usmonova`) |
| Biografiya | Yo'q | Bir necha abzas matn bo'lishi mumkin |
| Rasm | Yo'q | Bo'sh qoldirsangiz, keyinchalik albom import qilinganda TheAudioDB'dan avtomatik topilishga harakat qilinadi |

**"Saqlash"** tugmasini bosing — ijrochi darhol ro'yxatga qo'shiladi va uning sahifasi ochiladi. Bu yozuvning **egasi siz bo'lasiz**.

---

## 3. Albom qo'shish (qo'lda)

**Manzil:** yuqori menyu → **"+ ALBOM"** (yoki `/albom/qoshish/`)

| Maydon | Majburiymi? | Izoh |
|---|---|---|
| Albom nomi | ✅ Ha | |
| Ijrochi | ✅ Ha | Ro'yxatdan tanlanadi. Qidiruvli tanlash mavjud — yozishni boshlang. Kerakli ijrochi ro'yxatda yo'q bo'lsa, avval [2-bo'limdagidek](#2-ijrochi-qoshish) uni qo'shib oling |
| Chiqqan sanasi | Yo'q | Kalendar orqali tanlanadi |
| Muqova | Yo'q | Rasm fayli yuklanadi |
| Janrlar | Yo'q | Bir nechtasini belgilash mumkin (katakchalar) |

**"Saqlash"** dan so'ng albom sahifasi ochiladi — u yerga endi qo'shiqlarni qo'shishingiz mumkin (4-bo'limga qarang).

> **Eslatma:** Bu usulda qo'shiqlar **avtomatik qo'shilmaydi** — har birini qo'lda kiritishingiz kerak bo'ladi. Agar albom mashhur bo'lsa, [5-bo'limdagi](#5-katalogdan-tezkor-import-tavsiya-etiladi) import usuli ancha tezroq — muqova, sana, janr va barcha qo'shiqlarni bir necha soniyada avtomatik olib keladi.

---

## 4. Albomga qo'shiq qo'shish

**Manzil:** Albom sahifasida (`/albom/<ijrochi>/<albom>/`) → **"Qo'shiq qo'shish"** tugmasi
(yoki to'g'ridan-to'g'ri `/albom/<albom-ID>/qoshiq-qoshish/`)

| Maydon | Majburiymi? | Izoh |
|---|---|---|
| Trek raqami | ✅ Ha | Albomdagi tartib raqami (1, 2, 3...). Formaga kirganda avtomatik keyingi bo'sh raqam taklif qilinadi. **Bitta albomda ikkita qo'shiq bir xil raqamda bo'la olmaydi** — mavjud raqam yozilsa xato chiqadi |
| Qo'shiq nomi | ✅ Ha | |
| Davomiyligi (millisekund) | Yo'q | Bilmasangiz **bo'sh qoldiring** — jadvalda shunchaki tire (—) ko'rinadi. To'ldirmoqchi bo'lsangiz: daqiqa×60 + soniya, natijani ×1000 qiling. Masalan **3:35** → (3×60+35)×1000 = **215000** |

**"Saqlash"** dan so'ng albom sahifasiga qaytariladi, yangi qo'shiq ro'yxatda paydo bo'ladi.

> Qo'shiqning alohida egasi bo'lmaydi — u turgan albomning egasi hisoblanadi. Faqat albom egasi (yoki administrator) qo'shiq qo'sha oladi.

---

## 5. Katalogdan tezkor import (tavsiya etiladi)

Bu — mashhur albomlarni qo'shishning **eng tez** yo'li: muqova, chiqqan sana, janrlar, ijrochi rasmi va **barcha qo'shiqlar** bir necha soniyada avtomatik yuklanadi.

**Manzil:** yuqori menyu → **"KATALOG"** (yoki `/import/`)

### Qadamlar

1. Qidiruv katakchasiga albom yoki ijrochi nomini yozing (masalan: `the eminem show`, `Yulduz Usmonova`).
2. **"Qidirish"** tugmasini bosing — topilgan albomlar kartalar shaklida chiqadi (muqova, nomi, ijrochisi, qo'shiqlar soni bilan).
3. Kerakli albom ostidagi **"Import qilish"** tugmasini bosing.
4. Bir necha soniyada albom to'liq (qo'shiqlari bilan) bazaga qo'shiladi va uning sahifasi ochiladi.

### Bilishingiz kerak bo'lgan nozikliklar

- **Bepul va kalitsiz ishlaydi** — sukut bo'yicha Deezer xizmatidan foydalaniladi, 30 soniyalik namuna (tinglash uchun ▶ tugmasi) ham shu yerdan keladi.
- **Ba'zi mashhur albomlar bu yerdan umuman topilmaydi** — bu hududiy litsenziya cheklovi (Deezer'ning o'zida shunday), dasturning xatosi emas. Masalan ba'zi Dua Lipa, Gorillaz, Coldplay, Linkin Park, Ed Sheeran albomlarida faqat singl/jonli yozuvlar chiqadi. Bunday holatda albomni [3-bo'limdagidek](#3-albom-qoshish-qolda) qo'lda qo'shing.
- **Nomlar avtomatik tozalanadi**: `Nevermind (Remastered)` → `Nevermind`, `folklore (deluxe version)` → `folklore`. Faqat oxiridagi qavs ichida "remaster/deluxe/edition/version" kabi so'z bo'lsa olib tashlanadi — `(What's the Story) Morning Glory?` kabi nomlar buzilmaydi.
- **Allaqachon import qilingan albom qayta import qilinmaydi** — tugma bosilsa, mavjud yozuvning o'zi ochiladi, nusxasi yaratilmaydi.
- Import qilingan albom va (agar yangi bo'lsa) ijrochining **egasi — import qilgan siz** bo'lasiz.

### Terminaldan import (ilg'or foydalanuvchilar uchun)

Loyiha papkasida terminal orqali ham import qilish mumkin:

```bash
./venv/bin/python manage.py import_album --search "the eminem show"
./venv/bin/python manage.py import_album 103248
```

Mashhur albomlar ro'yxatini ommaviy yuklash:

```bash
./venv/bin/python manage.py seed_albums --limit 10
```

---

## 6. Tahrirlash va o'chirish

Har bir albom, ijrochi va qo'shiq qatorida (yoki sahifasida) **qalam** (tahrirlash) va **savat** (o'chirish) belgilari bor — faqat sichqoncha ustiga kelganda ko'rinadi.

- **Tahrirlash** — mavjud ma'lumotni o'zgartirish uchun forma ochiladi (xuddi qo'shish formasi kabi, lekin oldindan to'ldirilgan).
- **O'chirish** — bosilganda avval **tasdiqlash sahifasi** chiqadi ("Ha, o'chirish" tugmasi bosilmaguncha hech narsa o'chmaydi). Bu qasddan qilingan — havolani tasodifan ochib qo'yish orqali ma'lumot yo'qolib ketmasin degan maqsadda.

> **Diqqat:** Albomni o'chirsangiz, uning **barcha qo'shiqlari** ham birga o'chadi — bu amalni orqaga qaytarib bo'lmaydi.
>
> Ijrochini o'chirish esa — agar unda hali albomlar bo'lsa — **rad etiladi** ("avval albomlarini o'chiring yoki boshqa ijrochiga o'tkazing" degan xabar bilan). Ijrochini o'chirish uchun avval uning barcha albomlarini o'chiring (yoki boshqa ijrochiga qayta biriktiring).

---

## 7. Egalik qoidalari — kim nimani o'zgartira oladi

| Amal | Kim qila oladi |
|---|---|
| Ko'rish, tinglash, qidirish | Tizimga kirgan **har kim** |
| Yangi albom/ijrochi qo'shish | Har kim (qo'shgan odam egasi bo'ladi) |
| Tahrirlash, o'chirish | Faqat **o'sha yozuvning egasi** |
| Albomga qo'shiq qo'shish | Faqat **shu albomning egasi** |
| Hammasini boshqarish (boshqa birovning yozuvini ham) | Faqat **administrator** |

Boshqa birovning albomini/ijrochisini tahrirlash yoki o'chirishga urinsangiz — "Bu yozuv sizniki emas" degan xabar bilan qaytariladi.

---

## 8. Qidiruv va filtr

- Sahifa yuqorisidagi qidiruv katakchasiga yozishni boshlang — **ikki harfdan boshlab** albom va ijrochi takliflari ro'yxati chiqadi (rasmi bilan). Klaviatura (↑ ↓ Enter Esc) bilan ham boshqarish mumkin.
- Bosh sahifadagi **janr** havolalari orqali faqat shu janrdagi albomlarni ko'rish mumkin.

> Diqqat: bu — saytdagi o'z kataloginigiz bo'yicha qidiruv. Yangi albom **topib import qilish** uchun [5-bo'limdagi](#5-katalogdan-tezkor-import-tavsiya-etiladi) "KATALOG" sahifasidan foydalaning.

---

## 9. Tez-tez uchraydigan xatoliklar

| Xatolik / xabar | Sababi | Yechim |
|---|---|---|
| "Bu albomda N-trek allaqachon mavjud" | Trek raqami boshqa qo'shiqda band | Boshqa raqam kiriting yoki avval eski qo'shiqni tahrirlang |
| "Bu yozuv sizniki emas..." | Boshqa birovning albomi/ijrochisini tahrirlashga urinilgan | Faqat o'z yozuvlaringizni tahrirlashingiz mumkin |
| Import qidiruvida "Hech narsa topilmadi" | Nom xato yozilgan yoki katalogda yo'q | Nomni boshqacha (masalan faqat ijrochi nomi bilan) qayta yozib ko'ring, yoki [3-bo'limdagidek](#3-albom-qoshish-qolda) qo'lda qo'shing |
| Mashhur albom importda umuman chiqmayapti | Hududiy litsenziya cheklovi (Deezer tomonidan) | Qo'lda qo'shing |
| "Bu ijrochini o'chirib bo'lmadi — unda hali albomlar bor" | Ijrochida hali albom(lar) bor | Avval albomlarini o'chiring yoki boshqa ijrochiga o'tkazing, keyin ijrochini o'chiring |
| Ro'yxatdan o'tishda "Bu e-pochta/foydalanuvchi nomi allaqachon band" | Xuddi shu email yoki nom bilan akkaunt bor | Boshqa email/nom tanlang yoki "Kirish" orqali mavjud akkauntingizga kiring |

---

*Loyiha haqida texnik tafsilotlar uchun: [README.md](README.md) va [ARXITEKTURA.md](ARXITEKTURA.md)*
