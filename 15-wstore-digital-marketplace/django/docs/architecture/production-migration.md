# WStore production migratsiyasi va maxfiy ma'lumotlar rejasi

Bu hujjat productionda ma'lumot yo'qotmasdan ishlash tartibini belgilaydi.

## Production holati — 2026-11-11

- WStore production bazasi PostgreSQL **16.15** ga o'tkazildi.
- PostgreSQL faqat `127.0.0.1:5432` da tinglaydi; alohida, cheklangan
  `wstore_app` foydalanuvchisi ishlatiladi.
- Cutoverdan oldingi SQLite nusxasi va yakuniy export tiklash uchun serverda
  saqlangan. Ular tasdiqlangan retention davri tugamaguncha o'chirilmaydi.
- Rehearsal va yakuniy importda asosiy jadval hisoblari mos keldi:
  foydalanuvchi 7, mahsulot 21, buyurtma 2, Click tranzaksiya 9, pul yechish
  so'rovi 1.

## Hozirgi holat va xavf

`core.User.card_number` hamda `orders.Withdrawal.card_number` karta raqamini
ochiq matn ko'rinishida saqlaydi. Bu holat qabul qilinmaydi. Karta raqamini
bir martada yangi fieldga ko'chirish yoki ustunni o'chirish mavjud payoutlarni
uzib qo'yishi mumkin, shuning uchun quyidagi kengaytirish–ko'chirish–qisqartirish
usuli majburiy.

## Kerakli secretlar

Production `.env` ga alohida, 32-baytli Fernet kaliti kiritiladi:

```text
FIELD_ENCRYPTION_KEY=<base64-url-safe-fernet-key>
```

Kalit parol menejerida saqlanadi, Git va backup chatlarga yozilmaydi. Kalit
bo'lmasa yangi maxfiy to'lov ma'lumotini saqlash rad etiladi. Kalit
rotatsiyasi keyingi alohida change-management bosqichida amalga oshiriladi.

## Bosqichlar

1. **Expand.** `encrypted_card_number` va faqat qidirish/ko'rsatish uchun
   `card_last4` ustunlari qo'shiladi. Eski ustun o'chirilmaydi.
2. **Dual-write.** Yangi profil va pul yechish so'rovlari faqat shifrlangan
   qiymat hamda oxirgi 4 raqamni yozadi. Admin faqat maskalangan raqamni
   ko'radi; `search_fields` dan karta raqami olib tashlanadi.
3. **Backfill.** Avval staging backup nusxasida, keyin productionda
   boshqaruv buyrug'i eski qiymatlarni batch bilan shifrlaydi. Har batchda
   audit hisoboti: o'qilgan, yangilangan, xato yozuvlar. Xato bo'lsa jarayon
   to'xtaydi; eski ustun rollback uchun qoladi.
4. **Read switch.** Payout operatori faqat shifrlangan qiymatni ochadi.
   Bir haftalik kuzatuv davrida decrypt xatolari, backlog va payout holatlari
   kuzatiladi.
5. **Contract.** Tasdiqlangan backup va staging rehearsalidan keyin eski
   ochiq-matn ustunlari olib tashlanadi. Bu qaytmas migratsiya alohida pull
   request va release oynasida bajariladi.

## Release tartibi

1. Production DB backup olinadi va tiklash sinovi stagingda o'tkaziladi.
2. `manage.py check --deploy`, migratsiya rejasi va testlar CI da yashil
   bo'ladi.
3. Kod canary workerga chiqariladi; error log va payment callbacklar kuzatiladi.
4. Keyin migratsiya batchlari ishga tushiriladi. Har batchdan keyin payout
   namunasi operator tomonidan tekshiriladi.
5. Muammo bo'lsa ilova eski o'qish yo'liga qaytariladi; eski ustunlar hali
   saqlangani uchun ma'lumot yo'qolmaydi.

## PostgreSQL o'tishi

SQLite faqat lokal tezkor testlar uchun qoladi. Production PostgreSQLga
ko'chirilganda avval read-only backup, staging restore, `migrate --plan`,
smoke test va callback replay tekshiruvi bajariladi. `Order`/`ClickTransaction`
uchun idempotency va qator blokirovkasi PostgreSQLda parallel checkout bilan
alohida load-test qilinadi.
