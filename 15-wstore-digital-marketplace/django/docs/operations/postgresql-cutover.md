# WStore: SQLite dan PostgreSQL ga production cutover

Bu yo'riqnoma faqat rejalashtirilgan release oynasida bajariladi. SQLite
faylini o'chirish, ustiga yozish yoki `DATABASE_URL` ni backup/rehearsalsiz
almashtirish taqiqlanadi.

## Muvaffaqiyat mezonlari

- Ilova yangi PostgreSQL bazasida barcha migratsiyalar bilan ishlaydi.
- Foydalanuvchi, mahsulot, buyurtma, Click tranzaksiya va pul yechish
  yozuvlarining soni SQLite nusxasi bilan mos keladi.
- `healthz`, Google login, katalog, checkout va yuklab olish smoke-testdan
  o'tadi.
- `wstore` xizmatini eski SQLite konfiguratsiyasiga qaytarish mumkin bo'ladi.

## 1. Tayyorlash

1. Past trafik vaqtini belgilang va tashqi to'lov callbacklarini qisqa vaqtga
   kuzatuvga oling.
2. `db.sqlite3` ning fayl darajasidagi nusxasini oling va undan alohida
   PostgreSQL rehearsali qiling.
3. Production `.env` uchun kuchli alohida PostgreSQL foydalanuvchisi va
   parolini yarating. Parol Git, terminal tarixi yoki chatga yozilmaydi.
4. Quyidagi qiymat faqat serverning `.env` fayliga yoziladi:

   ```text
   DATABASE_URL=postgresql://wstore_app:<password>@127.0.0.1:5432/wstore
   ```

   `127.0.0.1` bazani internetga ochmaslik uchun majburiy: PostgreSQL tashqi
   interfeysda tinglamaydi.

## 2. Rehearsal

SQLite va PostgreSQL bir vaqtning o'zida `DATABASE_URL` almashuvi orqali
ishlatiladi. Ushbu buyruqlar avval serverning staging nusxasida bajariladi.

```bash
# SQLite ma'lumotlarini, ruxsat va content-type tizim yozuvlarisiz eksport qiling.
DATABASE_URL='' ./.venv/bin/python manage.py dumpdata \
  --natural-foreign --natural-primary \
  --exclude contenttypes --exclude auth.permission --exclude admin.logentry \
  --output /secure/backup/wstore-data.json

# Bo'sh PostgreSQL bazasiga sxema va ma'lumotlarni yozing.
DATABASE_URL='<postgres-url>' ./.venv/bin/python manage.py migrate --noinput
DATABASE_URL='<postgres-url>' ./.venv/bin/python manage.py loaddata \
  /secure/backup/wstore-data.json
DATABASE_URL='<postgres-url>' ./.venv/bin/python manage.py check --deploy
```

Importdan keyin har bir biznes jadvalidagi satrlar sonini tekshiring:

```bash
DATABASE_URL='' ./.venv/bin/python manage.py shell -c \
  "from core.models import User; from store.models import Product; from orders.models import Order, ClickTransaction, Withdrawal; print(User.objects.count(), Product.objects.count(), Order.objects.count(), ClickTransaction.objects.count(), Withdrawal.objects.count())"
DATABASE_URL='<postgres-url>' ./.venv/bin/python manage.py shell -c \
  "from core.models import User; from store.models import Product; from orders.models import Order, ClickTransaction, Withdrawal; print(User.objects.count(), Product.objects.count(), Order.objects.count(), ClickTransaction.objects.count(), Withdrawal.objects.count())"
```

Hisoblar bir xil bo'lmasa, cutover to'xtatiladi. SQLite ishlab turadi va
farq stagingda aniqlanadi.

## 3. Cutover

1. Qisqa maintenance oynasida yangi checkout va payout so'rovlarini to'xtating.
2. Yangi SQLite backup va exportni oling.
3. Rehearsal buyruqlarini bo'sh production PostgreSQL bazasida takrorlang.
4. Jadval sonlari hamda smoke-testlar teng bo'lgach, `.env` dagi
   `DATABASE_URL` ni PostgreSQL qiymatiga o'zgartiring.
5. `wstore` ni qayta ishga tushiring, `healthz` va real Google-login oqimini
   tekshiring.
6. Keyingi 24 soat davomida error loglar, Click callbacklar va buyurtmalarni
   kuzating.

## Rollback

Muammo aniqlansa, `DATABASE_URL` ni olib tashlang yoki oldingi SQLite
konfiguratsiyasiga qaytaring va `wstore` ni qayta ishga tushiring. SQLite
backup va original `db.sqlite3` cutoverdan keyin kamida 30 kun saqlanadi.
PostgreSQL bazasi rollback paytida o'chirilmaydi: u faqat tekshiruv uchun
saqlanadi.
