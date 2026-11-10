# WStore: joriy request oqimi va service-layer maqsadi

Bu qaydnoma faqat `apps/core/api.py` va `apps/orders/views.py` ni o‘qish
asosida yozildi. Dizayn va URL kontraktlari o‘zgarmaydi; maqsad — keyingi
refaktor uchun hozirgi javobgarlik chegaralarini aniq ko‘rsatish.

## 1. Tashqi API oqimi (`apps/core/api.py`)

### Umumiy ketma-ketlik

`Authorization` sarlavhasi → `api_token_required` → JSON/field validatsiyasi →
seller scope bilan ORM → kerak bo‘lsa `transaction.atomic` → `_product_json`
va `JsonResponse`.

- `api_token_required(view)` (`39–68-qatorlar`) Bearer tokenni ajratadi,
  `ApiToken.authenticate()` orqali tekshiradi, foydalanuvchining faol va
  seller ekanini tekshiradi, so‘ng `request.api_token` va `request.api_user`
  ni qo‘yadi. Shu dekorator HTTP xato javoblarini ham o‘zi yaratadi va token
  `last_used` holatini `token.touch()` bilan yozadi.
- `_json_body(request)` (`71–85`) request body hajmini, JSON sintaksisini,
  `Decimal` sonlarini va JSON obyekt ekanini tekshiradi. Parsing xatosini ham
  darhol `JsonResponse`ga aylantiradi.
- `_product_data(data, creating=False)` (`92–154`) mahsulot inputini tozalaydi
  va tekshiradi: matn uzunligi, URL sxemasi, kategoriya mavjudligi, narxning
  chekli/musbat Decimal ekanligi, `tech_stack`/`features` ro‘yxati va create
  uchun majburiy maydonlar. Kategoriya lookup’i ham shu validatorda bajariladi.
- `products_view(request)` (`203–251`) GET’da seller bo‘yicha mahsulotlarni
  o‘qiydi; POST’da body parse, `_product_data`, DRAFT holati, slug yaratish va
  collision uchun suffix, `Product.save()` hamda 201 response’ni bajaradi.
- `product_detail_view(request, product_id)` (`256–309`) har bir method uchun
  sellerga tegishli mahsulotni `select_for_update()` bilan oladi. DELETE’da
  sotilgan mahsulotni o‘chirishni rad etadi; PATCH’da status o‘tishlarini
  cheklaydi, maydonlarni yozadi va JSON response qaytaradi. Funksiyaning
  yuqorisidagi `@transaction.atomic` GET va xato javoblarni ham tranzaksiya
  doirasiga kiritadi.
- `stats_view(request)` (`313–343`) mahsulot soni, `sales_count`, paid order
  summasi va mahsulot kesimidagi statistikani bir response modeliga yig‘adi.
- `categories_view(request)` (`347–355`) kategoriya query’sini olib, API
  formatiga serializatsiya qiladi.

### Aralashgan javobgarliklar

1. `products_view` HTTP method dispatch, input validation, slug policy,
   aggregate/business state (`DRAFT`) va persistence’ni bir joyda ushlab
   turibdi. View’ni test qilish uchun HTTP layer, ORM va slug collision birga
   ishga tushadi.
2. `_product_data` field schema bilan birga `Product._meta` va `Category`
   ORM’siga bog‘langan. Demak, input contract alohida application/domain
   qatlamida mustaqil tekshirilmaydi.
3. `product_detail_view` authorization scope, locking, o‘chirish/status
   qoidalari va response mapping’ni bitta transaction-dekoratsiyalangan view
   ichida aralashtiradi.
4. `api_token_required`, `_json_body` va `_err` transport, xavfsizlik,
   validation error mapping va response formatini bir vaqtda boshqaradi.

## 2. Xarid va to‘lov oqimi (`apps/orders/views.py`)

### Xarid yaratish

`checkout_view(request, product_id)` (`51–136`):

1. `login_required` va `require_POST` requestni cheklaydi; `get_object_or_404`
   active, o‘chirilmagan mahsulotni oladi.
2. Sotuvchining o‘z mahsulotini sotib olishi va avvalgi PAID order takroran
   xarid qilinishi bloklanadi (`56–67`).
3. `_simulation_requested` (`37–46`) demo rejimini va `archive_available`/
   `payments_configured()` shartlarini tekshiradi.
4. Birinchi `transaction.atomic` (`76–95`) order va PENDING
   `ClickTransaction`ni yaratadi; merchant transaction ID shu yerda beriladi.
5. Demo bo‘lsa ikkinchi atomic blok (`100–130`) Click transaction va orderni
   PAID qiladi, download token beradi, `sales_count` va seller/referral
   balanslarini yangilaydi.
6. Demo bo‘lmasa Click URL qurilib redirect qilinadi (`134–136`). Demak,
   response turi ham view ichida biznes holatiga qarab tanlanadi.

### Sotuvchi e’lon to‘lovi

`listing_pay_view` (`141–176`) seller scope, DRAFT status va payment
configurationni tekshiradi; PENDING listing transaction yaratadi. Demo oqimida
PAID qilib, mahsulotni PENDING moderatsiyaga o‘tkazadi; real oqimda Click’ka
redirect qiladi. Listing payment state transition’i va HTTP redirect bir
funksiyada.

### Buyurtma holati va yuklab olish

- `order_status_view` (`180–208`) ownership/staff authorizationni tekshiradi,
  pending order uchun PENDING Click transactionni GET request ichida lazy
  yaratadi, payment URL yasaydi va template render qiladi. O‘qish endpointida
  yozuv yaratish bor.
- `order_simulate_pay_view` (`213–263`) demo payment state transition, download
  token, sales counter, seller/referral credit, Telegram notification, flash
  message va redirectni birlashtiradi.
- `download_file_view` (`277–296`) token va PAID orderni, ownershipni va
  archive mavjudligini tekshiradi; storage’dan stream ochadi, download countni
  oshiradi va `FileResponse` qaytaradi. Authorization va storage policy bitta
  view’da.

### Click webhook oqimi

`click_prepare_webhook` (`410–448`) va `click_complete_webhook` (`452–572`)
ikkalasi ham quyidagi ketma-ketlikni takrorlaydi:

`POST` check → `extract_click_payload` → `check_click_auth` → merchant ID parse
→ transaction lookup → amount check → state/error response.

`click_complete_webhook` bundan keyin:

- PAID/FAILED/REFUNDED holatlari uchun idempotent yoki xato javob beradi
  (`478–502`);
- `transaction.atomic` ichida PENDING → PAID claim qiladi (`504–518`);
- purchase bo‘lsa orderni PAID qiladi, download token beradi, `sales_count`ni
  oshiradi, seller balansiga commission’dan keyingi summani yozadi va referral
  bonusni beradi (`520–553`);
- listing bo‘lsa mahsulotni DRAFT’dan PENDING’ga o‘tkazadi (`555–568`);
- Telegram xabarini `transaction.on_commit` orqali commit’dan keyin yuboradi,
  so‘ng Click formatidagi JSON response qaytaradi.

### Aralashgan javobgarliklar

1. `checkout_view` va `order_simulate_pay_view` order lifecycle, payment
   provider, ledger/balance, referral va user messagingni bir view’da bajaradi.
2. `click_complete_webhook` provider protocol parsing, authentication,
   idempotency, order/product state machine, moliyaviy yozuvlar va notification
   orchestrationni bir methodga jamlaydi. Bu eng katta application-service
   chegarasi.
3. `order_status_view` GET paytida `ClickTransaction` yaratgani sababli query
   va command semantikasi aralashgan; parallel refresh’lar uchun alohida
   uniqueness/idempotency policy service’da bo‘lishi kerak.
4. `seller_balance_view` (`358–404`) form validation, balansni atomik
   kamaytirish, Withdrawal yaratish, notification va UI message’ni bajaradi.
5. `seller_dashboard_view` (`331–354`) query/report calculation va template
   response’ni bir joyda ushlab turadi. `_simulation_requested` esa transport
   parametrini payment policy’ga bevosita bog‘laydi.

## 3. Refaktordan keyingi maqsadli shakl

View’lar faqat HTTP adapter bo‘lib qoladi: requestni oladi, schema/DTO orqali
inputni beradi, application service chaqiradi va service natijasini HTTP
status/redirect/template/JSON formatiga o‘giradi. View ichida balans, order
statusi, slug policy yoki Click protocol qarori qolmaydi.

Tavsiya etiladigan chegaralar:

- `core/api.py` uchun `ApiAuthService`, `ProductCommandService` va
  `ProductQueryService`: token auth, create/update/delete va read/statistics
  use-case’lari alohida bo‘ladi. `_json_body` transport parser, product input
  esa schema/validator bo‘ladi; kategoriya lookup’i command service yoki
  repository query’siga o‘tadi.
- `orders/services/checkout.py`: `create_checkout` active product, self-buy,
  existing paid order, archive/payment readiness va PENDING order/transaction
  invariantlarini boshqaradi.
- `orders/services/payment.py`: Click prepare/complete payloadini provider
  adapterdan oladi, signature/amount/prepare ID tekshiruvini bajaradi va
  `complete_purchase` yoki `complete_listing` use-case’ini chaqiradi.
- `orders/services/settlement.py`: bitta idempotent transaction ichida order
  va payment claim, download token, sales counter, seller credit va referral
  ledger o‘zgarishlarini bajaradi. Tranzaksiya chegarasi shu service’da aniq
  ko‘rinadi; view’da `F()` va balans matematikasi bo‘lmaydi.
- `orders/services/downloads.py`: paid ownership, archive policy, storage
  stream va download count invariantlarini boshqaradi.
- `orders/services/withdrawals.py`: formdan kelgan qiymatni command sifatida
  qabul qilib, balance reservation/refund state transitionni atomik bajaradi.
- `notifications/` yoki `core/integrations/telegram.py`: xabar payloadini
  service eventidan oladi; tashqi yuborish `transaction.on_commit`dan keyin
  ishlaydi.

Maqsadli oqim:

`HTTP view → request schema/auth adapter → application service → repository/
ORM query → domain result/event → response mapper`.

Har bir command service quyidagi invariantlarni test bilan mustahkamlaydi:

- seller scope URL yoki payloaddan emas, authenticated principal’dan olinadi;
- payment completion takror chaqirilsa moliyaviy credit bir marta beriladi;
- order/payment/product state transition ruxsat etilgan holatlar bilan
  cheklanadi;
- notification commit bo‘lmagan transactiondan tashqariga chiqmaydi;
- download faqat PAID va vakolatli xaridorga beriladi;
- failed transaction balansni o‘zgartirmaydi.

Refaktor bosqichma-bosqich qilinadi: avval hozirgi response kontraktlari va
regression testlar muzlatiladi, keyin `click_complete_webhook` settlement
service’ga, `checkout_view` checkout service’ga, so‘ng API product command’lari
ko‘chiriladi. Har bosqichdan keyin eski URL/status/JSON kontrakti, tranzaksiya
idempotency’si va production rollback yo‘li saqlanib tekshiriladi. Bu hujjat
joriy kodni o‘zgartirmaydi; keyingi implementation qarorlari uchun reading
baseline hisoblanadi.
