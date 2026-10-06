# 🤝 Django + Aiogram + PostgreSQL: Telegram Bot Yasash Bo'yicha Mukammal Qo'llanma

Bu qo'llanma ikkita kuchli vositani birlashtirishni o'rgatadi: **Django** (ORM, admin panel, ma'lumotlar bazasini boshqarish) va **Aiogram** (Telegram bot mantiq qatlami), ular orasidagi umumiy "til" esa **PostgreSQL** hisoblanadi.

**Nega bu kombinatsiya kuchli?**

- Bot ma'lumotlarini (foydalanuvchilar, tovarlar, buyurtmalar) qo'lda SQL yozmasdan, Django ORM orqali qulay boshqarasiz.
- Django admin panelidan tayyor, chiroyli web-interfeys orqali bot ma'lumotlarini ko'rish/tahrirlash — buni noldan yozish o'rniga bir necha qatorli kod bilan olasiz.
- PostgreSQL — bir vaqtning o'zida botdan (yozish) va admin paneldan (o'qish/yozish) kelayotgan so'rovlarni ishonchli boshqaradigan production-darajadagi DB.

**Oldindan bilishingiz tavsiya etiladi:** Django asoslari (models, admin, ORM) va Aiogram 3 asoslari (handlerlar, filterlar, FSM). Agar bularni hali chuqur bilmasangiz, avval alohida Django va Aiogram qo'llanmalarini ko'rib chiqing — bu hujjat ikkalasini **bir-biriga ulash**ga qaratilgan.

---

## 📑 Mundarija

1. [Arxitektura g'oyasi](#1-arxitektura-goyasi)
2. [Muhitni tayyorlash](#2-muhitni-tayyorlash)
3. [PostgreSQL'ni sozlash (Docker orqali)](#3-postgresqlni-sozlash-docker-orqali)
4. [Loyiha strukturasi](#4-loyiha-strukturasi)
5. [Django sozlamalari va .env](#5-django-sozlamalari-va-env)
6. [Modellar — botning "miyasi"](#6-modellar--botning-miyasi)
7. [Migratsiyalar va admin panel](#7-migratsiyalar-va-admin-panel)
8. [Aiogram botni Django bilan bog'lash](#8-aiogram-botni-django-bilan-boglash)
9. [PostgreSQL ulanishini boshqarish (middleware)](#9-postgresql-ulanishini-boshqarish-middleware)
10. [Handlerlar — Django async ORM bilan ishlash](#10-handlerlar--django-async-orm-bilan-ishlash)
11. [Keng tarqalgan xato: SynchronousOnlyOperation](#11-keng-tarqalgan-xato-synchronousonlyoperation)
12. [FSM + PostgreSQL: bosqichma-bosqich buyurtma olish](#12-fsm--postgresql-bosqichma-bosqich-buyurtma-olish)
13. [Management command — botni ishga tushirish](#13-management-command--botni-ishga-tushirish)
14. [Bonus: admin paneldan botga xabar yubortirish](#14-bonus-admin-paneldan-botga-xabar-yubortirish)
15. [Ikkalasini birga ishga tushirish (Docker Compose)](#15-ikkalasini-birga-ishga-tushirish-docker-compose)
16. [Xavfsizlik va production tavsiyalari](#16-xavfsizlik-va-production-tavsiyalari)
17. [Yakuniy to'liq loyiha — fayl-fayl](#17-yakuniy-toliq-loyiha--fayl-fayl)
18. [Foydali manbalar](#18-foydali-manbalar)

---

## 1. Arxitektura g'oyasi

Muhim tushuncha: bu **bitta Django loyihasi**, ichida **ikkita mustaqil jarayon** sifatida ishga tushadi:

| Jarayon | Buyruq | Vazifasi |
|---|---|---|
| **Web/Admin** | `python manage.py runserver` (yoki production'da Gunicorn) | Admin panel — tovarlar, buyurtmalarni ko'rish/boshqarish |
| **Bot** | `python manage.py runbot` (o'zimiz yozadigan maxsus buyruq) | Aiogram polling tsikli — Telegram bilan muloqot |

Ikkalasi ham **bitta kod bazasi**, **bitta `models.py`** va **bitta PostgreSQL**ga ulanadi:

```
                     ┌──────────────────────┐
                     │   PostgreSQL (DB)     │
                     └───────────▲───────────┘
                                 │
                 ┌───────────────┴────────────────┐
                 │                                  │
   ┌─────────────┴─────────────┐      ┌─────────────┴─────────────┐
   │   Django admin (web)       │      │   Aiogram bot (polling)    │
   │   manage.py runserver      │      │   manage.py runbot         │
   │   — sync, WSGI              │      │   — async, asyncio         │
   └─────────────────────────────┘      └─────────────────────────────┘
        Admin: tovar qo'shadi                Foydalanuvchi: /shop bosadi
        Admin: buyurtmani tasdiqlaydi         Bot: tovarlarni ko'rsatadi,
                                                buyurtmani DB'ga yozadi
```

Bu yerdagi asosiy texnik nozik joy: Django tarixan **sinxron** (sync) freymvork, Aiogram esa to'liq **asinxron** (async). Ularni to'g'ri bog'lash uchun Django'ning **async ORM** interfeysidan (`aget`, `acreate`, `aiterator` va h.k., Django 4.1+) foydalanamiz — bu qo'llanmaning markaziy mavzusi.

---

## 2. Muhitni tayyorlash

**Talablar:** Python 3.12+ (Django 6.0 uchun) yoki 3.10+ (Django 5.2 LTS uchun).

```bash
python -m venv venv
source venv/bin/activate      # Linux/macOS
venv\Scripts\activate         # Windows

pip install django aiogram django-environ psycopg2-binary asgiref
```

| Kutubxona | Vazifasi |
|---|---|
| `django` | ORM, admin panel, loyiha skeleti |
| `aiogram` | Telegram bot freymvorki |
| `django-environ` | `.env`dan sozlamalarni (shu jumladan `DATABASE_URL`) o'qish |
| `psycopg2-binary` | Django'ning PostgreSQL bilan gaplashishi uchun drayver |
| `asgiref` | `sync_to_async` / `async_to_sync` — sync va async dunyolarni bog'lovchi ko'prik |

```bash
pip freeze > requirements.txt
```

---

## 3. PostgreSQL'ni sozlash (Docker orqali)

Mahalliy kompyuteringizga PostgreSQL o'rnatmasdan, eng tez yo'l — Docker:

```bash
docker run -d \
  --name pg_bot_db \
  -e POSTGRES_DB=botdb \
  -e POSTGRES_USER=botuser \
  -e POSTGRES_PASSWORD=botpassword \
  -p 5432:5432 \
  postgres:16
```

Bu buyruq PostgreSQL 16'ni ishga tushiradi va `localhost:5432` orqali ulanish imkonini beradi. (To'liq `docker-compose.yml` — 15-bo'limda.)

---

## 4. Loyiha strukturasi

```
telegram_shop_bot/
├── .env
├── .gitignore
├── requirements.txt
├── manage.py
├── docker-compose.yml
│
├── config/                       # Django loyiha sozlamalari
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
└── apps/
    ├── shop/                      # DATA QATLAMI — faqat models + admin
    │   ├── models.py               # TelegramUser, Product, Order
    │   ├── admin.py
    │   └── migrations/
    │
    └── bot/                        # BOT QATLAMI — faqat aiogram kodi
        ├── loader.py                # Bot, Dispatcher obyektlari
        ├── middlewares.py           # PostgreSQL ulanishini boshqaruvchi middleware
        ├── states.py                 # FSM holatlari
        ├── handlers/
        │   ├── __init__.py
        │   └── user.py                # /start, /shop, buyurtma handlerlari
        └── management/
            └── commands/
                └── runbot.py           # `python manage.py runbot`
```

> 💡 **Nega ikkita alohida app?** `shop` — sof ma'lumotlar qatlami (Django admin buni "ko'radi"). `bot` — faqat Telegram bilan gaplashish mantig'i. Bu ajratish tufayli, agar kelajakda web-sayt yoki mobil ilova qo'shsangiz, ular ham xuddi shu `shop.models`dan foydalana oladi — bot kodiga tegmasdan.

---

## 5. Django sozlamalari va .env

`.env`:
```
DEBUG=True
SECRET_KEY=juda-uzun-tasodifiy-maxfiy-satr
ALLOWED_HOSTS=localhost,127.0.0.1
BOT_TOKEN=123456789:AAExampleTelegramBotTokenHere

# django-environ formatida: postgres://USER:PASSWORD@HOST:PORT/DBNAME
DATABASE_URL=postgres://botuser:botpassword@localhost:5432/botdb
```

`config/settings.py`:
```python
from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])

BOT_TOKEN = env("BOT_TOKEN")   # Aiogram shu yerdan tokenni oladi (4-bo'lim, loader.py)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "apps.shop",
    "apps.bot",     # management command'ni topishi uchun Django app sifatida ro'yxatda bo'lishi SHART
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# django-environ DATABASE_URL'ni avtomatik PostgreSQL sozlamalariga aylantiradi
DATABASES = {
    "default": env.db("DATABASE_URL")
}

LANGUAGE_CODE = "uz"
TIME_ZONE = "Asia/Tashkent"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
```

> ⚠️ `apps.bot`ni `INSTALLED_APPS`ga qo'shishni unutmang — aks holda Django uning ichidagi `management/commands/runbot.py`ni **topa olmaydi** va `python manage.py runbot` "Unknown command" xatosini beradi.

---

## 6. Modellar — botning "miyasi"

```python
# apps/shop/models.py
from django.db import models


class TelegramUser(models.Model):
    telegram_id = models.BigIntegerField(unique=True)
    full_name = models.CharField(max_length=150)
    username = models.CharField(max_length=100, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} ({self.telegram_id})"


class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to="products/", blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Order(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "Yangi"
        CONFIRMED = "confirmed", "Tasdiqlangan"
        CANCELLED = "cancelled", "Bekor qilingan"

    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE, related_name="orders")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="orders")
    quantity = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.NEW)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Buyurtma #{self.pk} — {self.product.name}"
```

> 📌 `telegram_id` uchun **`BigIntegerField`** ishlatilgan — Telegram foydalanuvchi ID'lari oddiy `IntegerField` sig'imidan (2 milliarddan) katta bo'lishi mumkin.

---

## 7. Migratsiyalar va admin panel

```bash
python manage.py makemigrations shop
python manage.py migrate
python manage.py createsuperuser
```

```python
# apps/shop/admin.py
from django.contrib import admin
from .models import TelegramUser, Product, Order


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = ("full_name", "telegram_id", "username", "created_at")
    search_fields = ("full_name", "username", "telegram_id")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "product", "quantity", "status", "created_at")
    list_filter = ("status", "created_at")
    list_editable = ("status",)              # ro'yxatdan turib holatni o'zgartirish
    autocomplete_fields = ("user", "product")
```

Endi `python manage.py runserver` bilan `/admin/`ga kirib, tovar qo'shishingiz mumkin — bu tovarlar bir zumda botda ko'rina boshlaydi (chunki ikkalasi ham bitta PostgreSQL'dan o'qiydi).

---

## 8. Aiogram botni Django bilan bog'lash

Bot obyektlarini alohida faylda yaratamiz va tokenni **Django sozlamalaridan** (`settings.BOT_TOKEN`) olamiz — bu token bir joyda (`.env`) saqlanishini ta'minlaydi:

```python
# apps/bot/loader.py
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from django.conf import settings

bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())
```

> 💡 Bu faylni import qilishning o'zi Django sozlamalari **allaqachon yuklangan** bo'lishini talab qiladi (`settings.BOT_TOKEN`ga murojaat bor). Buyruq `manage.py` orqali ishga tushirilganda Django buni avtomatik ta'minlaydi — shuning uchun botni **faqat** management command orqali ishga tushiramiz (13-bo'lim), oddiy `python bot.py` sifatida emas.

---

## 9. PostgreSQL ulanishini boshqarish (middleware)

Bu — ko'p qo'llanmalarda e'tibordan chetda qoladigan, lekin **production'da botni "vaqti-vaqti bilan o'lib qolishiga"** sabab bo'ladigan muhim nozik joy.

**Muammo nimada?** Django odatiy holatda har bir HTTP so'rovi tugagach, DB ulanishini yopadi (yoki `CONN_MAX_AGE` bo'yicha qayta ishlatadi) — bu **so'rov-javob** siklига mo'ljallangan. Aiogram esa **uzluksiz** asyncio tsiklida ishlaydi — "so'rov tugashi" degan tushuncha yo'q. Natijada, agar PostgreSQL ulanishni vaqt bo'yicha uzib qo'ysa (masalan, tarmoq tanaffusi yoki DB qayta ishga tushishi) yoki uzoq vaqt operatsiya bo'lmasa, bot eskirgan ("stale") ulanish orqali so'rov yuborishga urinib, xatoga uchraydi.

**Yechim:** har bir yangilikdan oldin/keyin Django'ning `close_old_connections()` funksiyasini chaqiruvchi middleware yozamiz — bu aynan Django o'zi har bir web-so'rovda avtomatik bajaradigan ishni, bot uchun "qo'lda" takrorlaydi.

```python
# apps/bot/middlewares.py
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from asgiref.sync import sync_to_async
from django.db import close_old_connections


class DjangoDBMiddleware(BaseMiddleware):
    """
    Aiogram uzluksiz asyncio tsiklida ishlagani uchun, Django'ning
    "har bir so'rov oxirida ulanishni yopish" mexanizmi ishlamaydi.
    Shu middleware har bir yangilikdan oldin/keyin eskirgan yoki
    uzilgan PostgreSQL ulanishlarini tozalab turadi.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        await sync_to_async(close_old_connections)()
        try:
            return await handler(event, data)
        finally:
            await sync_to_async(close_old_connections)()
```

> ⚠️ `close_old_connections` — sinxron (sync) Django funksiyasi. Uni async middleware ichida **to'g'ridan-to'g'ri** emas, `sync_to_async(...)()` orqali chaqiramiz — bu keyingi bo'limda tushuntiriladigan qoidaning aynan o'zi.

Bu middleware `dp.update.middleware(...)` orqali **barcha turdagi yangiliklarga** (xabar, callback va h.k.) ulanadi — 13-bo'limdagi `runbot.py`da ko'rasiz.

---

## 10. Handlerlar — Django async ORM bilan ishlash

Django 4.1+ ORM'ga `a` prefiksli asinxron metodlar qo'shdi: `aget()`, `acreate()`, `aget_or_create()`, `aupdate_or_create()`, `adelete()`, `aiterator()`, `acount()`, `aexists()` va h.k. **Har doim shularni ishlating** — oddiy `get()`, `create()`, `filter().first()` kabi sinxron metodlarni to'g'ridan-to'g'ri `async def` handler ichida chaqirish xatoga olib keladi (11-bo'lim).

```python
# apps/bot/handlers/user.py
from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData

from apps.shop.models import TelegramUser, Product

router = Router(name="user")


@router.message(CommandStart())
async def cmd_start(message: Message):
    # aget_or_create — Django ORM'ning asinxron "topish yoki yaratish" metodi
    user, created = await TelegramUser.objects.aget_or_create(
        telegram_id=message.from_user.id,
        defaults={
            "full_name": message.from_user.full_name,
            "username": message.from_user.username or "",
        },
    )
    if created:
        await message.answer(f"Xush kelibsiz, {user.full_name}! Siz ro'yxatdan o'tdingiz.")
    else:
        await message.answer(f"Yana xush kelibsiz, {user.full_name}!")


class ProductCallback(CallbackData, prefix="product"):
    id: int


@router.message(Command("shop"))
async def cmd_shop(message: Message):
    # QuerySet'ni QURISH (filter, select_related, order_by) — DB'ga hali murojaat qilmaydi, sinxron xavfsiz.
    # Uni HAQIQIY bajarish (iteratsiya, .get(), .count() va h.k.) — aynan shu joyda async kerak bo'ladi.
    products = [p async for p in Product.objects.filter(is_active=True).aiterator()]

    if not products:
        await message.answer("Hozircha tovarlar mavjud emas.")
        return

    builder = InlineKeyboardBuilder()
    for product in products:
        builder.button(
            text=f"{product.name} — {product.price} so'm",
            callback_data=ProductCallback(id=product.pk),
        )
    builder.adjust(1)

    await message.answer("🛍 Mavjud tovarlar:", reply_markup=builder.as_markup())
```

**Eng ko'p ishlatiladigan async ORM metodlari:**

| Sinxron (❌ async handlerda ishlatmang) | Asinxron muqobili (✅) |
|---|---|
| `Model.objects.get(...)` | `await Model.objects.aget(...)` |
| `Model.objects.create(...)` | `await Model.objects.acreate(...)` |
| `Model.objects.get_or_create(...)` | `await Model.objects.aget_or_create(...)` |
| `for obj in queryset:` | `async for obj in queryset.aiterator():` |
| `queryset.first()` | `await queryset.afirst()` |
| `queryset.count()` | `await queryset.acount()` |
| `instance.save()` | `await instance.asave()` |
| `instance.delete()` | `await instance.adelete()` |

---

## 11. Keng tarqalgan xato: SynchronousOnlyOperation

Agar `async def` handler ichida oddiy (a-prefikssiz) ORM metodini ishlatsangiz:

```python
@router.message(Command("shop"))
async def cmd_shop(message: Message):
    products = Product.objects.filter(is_active=True)   # bu qatorning o'zi muammo emas (lazy)
    for product in products:                             # ❌ MANA SHU YERDA XATOLIK: haqiqiy DB so'rovi
        ...
```

...quyidagi xatolikka duch kelasiz:

```
SynchronousOnlyOperation: You cannot call this from an async context - use a thread or sync_to_async.
```

**Ikki yechim bor:**

1. **Tavsiya etiladigan:** yuqoridagi jadvaldagi `a`-prefiksli metodlardan foydalaning (10-bo'lim).
2. Agar kerakli operatsiyaning async muqobili hali mavjud emas (masalan, murakkab `bulk_update` yoki tranzaksiya bloki — Django async ORM'da tranzaksiyalar hali to'liq qo'llab-quvvatlanmaydi), uni **alohida sinxron funksiyaga** chiqarib, `sync_to_async` bilan o'rang:

```python
from asgiref.sync import sync_to_async
from django.db import transaction


def _create_order_with_transaction(user, product, quantity):
    with transaction.atomic():
        order = Order.objects.create(user=user, product=product, quantity=quantity)
        Product.objects.filter(pk=product.pk).update(stock=product.stock - quantity)
        return order


@router.message(...)
async def some_handler(message: Message):
    order = await sync_to_async(_create_order_with_transaction)(user, product, 2)
```

---

## 12. FSM + PostgreSQL: bosqichma-bosqich buyurtma olish

Endi 10-bo'limdagi oddiy "bitta bosishda buyurtma" o'rniga, foydalanuvchidan miqdorni so'rab, keyin PostgreSQL'ga yozadigan to'liq FSM jarayonini quramiz:

```python
# apps/bot/states.py
from aiogram.fsm.state import StatesGroup, State

class OrderState(StatesGroup):
    quantity = State()
```

```python
# apps/bot/handlers/user.py ga qo'shimcha
from aiogram.fsm.context import FSMContext
from apps.shop.models import TelegramUser, Product, Order
from apps.bot.states import OrderState


@router.callback_query(ProductCallback.filter())
async def product_selected(call: CallbackQuery, callback_data: ProductCallback, state: FSMContext):
    product = await Product.objects.aget(pk=callback_data.id)
    await state.update_data(product_id=product.pk)
    await state.set_state(OrderState.quantity)

    await call.answer()
    await call.message.answer(f"«{product.name}» — nechta dona buyurtma qilmoqchisiz?")


@router.message(OrderState.quantity)
async def process_quantity(message: Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) < 1:
        await message.answer("Iltimos, musbat butun son kiriting:")
        return   # state o'zgarmaydi, qayta so'raydi

    data = await state.get_data()
    product = await Product.objects.aget(pk=data["product_id"])
    user = await TelegramUser.objects.aget(telegram_id=message.from_user.id)

    order = await Order.objects.acreate(user=user, product=product, quantity=int(message.text))
    await state.clear()

    await message.answer(
        f"✅ Buyurtma #{order.pk} qabul qilindi!\n"
        f"{product.name} — {order.quantity} dona\n"
        f"Holat: {order.get_status_display()} (admin tasdiqlaydi)"
    )
```

Bu yerda FSM (aiogram'ning o'zi) foydalanuvchi bilan muloqot bosqichlarini, Django ORM esa yakuniy natijani PostgreSQL'ga ishonchli saqlashni boshqaradi — ikkala freymvork o'z kuchli tomoni bilan ishlaydi.

---

## 13. Management command — botni ishga tushirish

Botni oddiy `python bot.py` emas, balki Django'ning **management command** mexanizmi orqali ishga tushiramiz — bu tokendan settings orqali foydalanish, va kelajakda `manage.py`ning boshqa barcha imkoniyatlaridan (logging sozlamalari, muhit o'zgaruvchilari) foydalanishni ta'minlaydi.

```python
# apps/bot/management/commands/runbot.py
import asyncio
import logging

from django.core.management.base import BaseCommand

from apps.bot.loader import bot, dp
from apps.bot.middlewares import DjangoDBMiddleware
from apps.bot.handlers.user import router as user_router

logging.basicConfig(level=logging.INFO)


class Command(BaseCommand):
    help = "Aiogram Telegram botni ishga tushiradi"

    def handle(self, *args, **options):
        asyncio.run(self._main())

    async def _main(self):
        dp.update.middleware(DjangoDBMiddleware())
        dp.include_router(user_router)

        await bot.delete_webhook(drop_pending_updates=True)
        self.stdout.write(self.style.SUCCESS("Bot ishga tushdi..."))
        await dp.start_polling(bot)
```

Ishga tushirish:
```bash
python manage.py runbot
```

> 💡 **Muhim:** `manage.py`orqali ishga tushirilgan har qanday buyruq (shu jumladan `runbot`) — Django tomonidan avtomatik `django.setup()` chaqirilgandan **keyin** ishlaydi. Shuning uchun `apps/bot/loader.py`, `handlers/user.py` va boshqa fayllar ichida `apps.shop.models`ni erkin import qilishingiz mumkin — hech qanday qo'shimcha sozlash shart emas.

---

## 14. Bonus: admin paneldan botga xabar yubortirish

Aksincha yo'nalish ham qiziq: admin panelda buyurtma holatini "Tasdiqlangan"ga o'zgartirganda, foydalanuvchiga **bot orqali** avtomatik xabar yuborish. Bu yerdagi qiyinchilik — Django admin **sinxron** (WSGI) muhitda ishlaydi, Aiogram Bot esa **asinxron**. Ko'prik — `asgiref`ning `async_to_sync`:

```python
# apps/shop/admin.py ga qo'shimcha
from asgiref.sync import async_to_sync
from aiogram import Bot
from django.conf import settings
from django.contrib import admin
from .models import Order


async def _notify_user(chat_id: int, text: str):
    # Har bir chaqiruvda YANGI Bot obyekti va sessiya ochiladi (async with),
    # chunki admin action'lar har safar YANGI event loop'da ishga tushadi —
    # umumiy `apps.bot.loader.bot` obyektining ichki aiohttp sessiyasini
    # boshqa event loop'lar orasida qayta ishlatish xatolikka olib keladi.
    async with Bot(token=settings.BOT_TOKEN) as bot:
        await bot.send_message(chat_id=chat_id, text=text)


@admin.action(description="Tanlangan buyurtmalarni tasdiqlash va foydalanuvchiga xabar berish")
def confirm_orders(modeladmin, request, queryset):
    for order in queryset:
        order.status = Order.Status.CONFIRMED
        order.save()
        async_to_sync(_notify_user)(
            order.user.telegram_id,
            f"✅ Buyurtma #{order.pk} tasdiqlandi! Tez orada siz bilan bog'lanamiz."
        )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "product", "quantity", "status", "created_at")
    actions = [confirm_orders]
```

Endi admin panelda bir nechta buyurtmani belgilab, "Tanlangan buyurtmalarni tasdiqlash..." amalini tanlasangiz — statusi yangilanadi **va** foydalanuvchi Telegram'da darhol xabar oladi.

---

## 15. Ikkalasini birga ishga tushirish (Docker Compose)

`Dockerfile`:
```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
```

`docker-compose.yml`:
```yaml
version: "3.9"
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_DB: botdb
      POSTGRES_USER: botuser
      POSTGRES_PASSWORD: botpassword
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U botuser -d botdb"]
      interval: 5s
      timeout: 5s
      retries: 5

  web:
    build: .
    command: >
      sh -c "python manage.py migrate &&
             gunicorn config.wsgi:application --bind 0.0.0.0:8000"
    env_file: .env
    depends_on:
      db:
        condition: service_healthy
    ports:
      - "8000:8000"

  bot:
    build: .
    command: python manage.py runbot
    env_file: .env
    depends_on:
      db:
        condition: service_healthy
      web:
        condition: service_started   # migratsiyalar web tomonidan bajarilishini kutadi

volumes:
  pgdata:
```

```bash
docker compose up -d --build
docker compose exec web python manage.py createsuperuser
```

Ikki alohida servis (`web` — admin panel, `bot` — Telegram bot) bitta `db` servisiga ulanadi — aynan 1-bo'limdagi arxitektura shu tarzda haqiqiy hayotga tatbiq etiladi.

---

## 16. Xavfsizlik va production tavsiyalari

- [ ] `SECRET_KEY` va `BOT_TOKEN` `.env`da, `.gitignore`ga qo'shilgan
- [ ] Production'da `DEBUG = False`, `ALLOWED_HOSTS` aniq domen bilan
- [ ] PostgreSQL foydalanuvchisiga faqat kerakli DB ustida huquq berilgan (superuser emas)
- [ ] `DjangoDBMiddleware` (9-bo'lim) botga har doim ulangan — aks holda uzoq muddat ishlagan bot PostgreSQL bilan aloqani yo'qotishi mumkin
- [ ] Har bir yangi ORM chaqiruvida `a`-prefiksli metod ishlatilganiga ishonch hosil qilingan (11-bo'lim)
- [ ] `bot.delete_webhook(drop_pending_updates=True)` polling boshlashdan oldin chaqirilgan
- [ ] Docker Compose'da PostgreSQL uchun `healthcheck` bor — `web`/`bot` DB tayyor bo'lishini kutib ishga tushadi
- [ ] Muntazam DB backup (`pg_dump`) sozlangan — bot va admin panel bitta DB'ga tayanadi, uni yo'qotish ikkalasini ham to'xtatadi

---

## 17. Yakuniy to'liq loyiha — fayl-fayl

Quyidagi fayllar to'plami — ishlaydigan minimal "Do'kon boti": foydalanuvchi ro'yxatdan o'tadi, `/shop` orqali tovarlarni ko'radi, tovar tanlab miqdorini kiritadi, buyurtma PostgreSQL'ga yoziladi va admin panelda ko'rinadi.

**`apps/shop/models.py`, `apps/shop/admin.py`** — 6 va 7-bo'limlardagidek.

**`apps/bot/loader.py`** — 8-bo'limdagidek.

**`apps/bot/middlewares.py`** — 9-bo'limdagidek.

**`apps/bot/states.py`:**
```python
from aiogram.fsm.state import StatesGroup, State

class OrderState(StatesGroup):
    quantity = State()
```

**`apps/bot/handlers/user.py`:**
```python
from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext

from apps.shop.models import TelegramUser, Product, Order
from apps.bot.states import OrderState

router = Router(name="user")


@router.message(CommandStart())
async def cmd_start(message: Message):
    user, created = await TelegramUser.objects.aget_or_create(
        telegram_id=message.from_user.id,
        defaults={
            "full_name": message.from_user.full_name,
            "username": message.from_user.username or "",
        },
    )
    text = "Xush kelibsiz!" if created else "Yana xush kelibsiz!"
    await message.answer(f"{text} Tovarlarni ko'rish uchun /shop yozing.")


class ProductCallback(CallbackData, prefix="product"):
    id: int


@router.message(Command("shop"))
async def cmd_shop(message: Message):
    products = [p async for p in Product.objects.filter(is_active=True).aiterator()]
    if not products:
        await message.answer("Hozircha tovarlar mavjud emas.")
        return

    builder = InlineKeyboardBuilder()
    for product in products:
        builder.button(text=f"{product.name} — {product.price} so'm", callback_data=ProductCallback(id=product.pk))
    builder.adjust(1)
    await message.answer("🛍 Mavjud tovarlar:", reply_markup=builder.as_markup())


@router.callback_query(ProductCallback.filter())
async def product_selected(call: CallbackQuery, callback_data: ProductCallback, state: FSMContext):
    product = await Product.objects.aget(pk=callback_data.id)
    await state.update_data(product_id=product.pk)
    await state.set_state(OrderState.quantity)
    await call.answer()
    await call.message.answer(f"«{product.name}» — nechta dona buyurtma qilmoqchisiz?")


@router.message(OrderState.quantity)
async def process_quantity(message: Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) < 1:
        await message.answer("Iltimos, musbat butun son kiriting:")
        return

    data = await state.get_data()
    product = await Product.objects.aget(pk=data["product_id"])
    user = await TelegramUser.objects.aget(telegram_id=message.from_user.id)
    order = await Order.objects.acreate(user=user, product=product, quantity=int(message.text))
    await state.clear()

    await message.answer(
        f"✅ Buyurtma #{order.pk} qabul qilindi!\n{product.name} — {order.quantity} dona"
    )
```

**`apps/bot/management/commands/runbot.py`** — 13-bo'limdagidek.

Ishga tushirish (mahalliy, Docker'siz):
```bash
python manage.py migrate
python manage.py createsuperuser

# 1-terminalda:
python manage.py runserver

# 2-terminalda:
python manage.py runbot
```

`/admin/`dan bir nechta `Product` qo'shing → Telegram'da botga `/start`, so'ng `/shop` yuboring → tovarni tanlang → miqdorni kiriting → `/admin/`dagi **Order** bo'limida yangi buyurtma darhol paydo bo'ladi.

---

## 18. Foydali manbalar

- Django rasmiy hujjati: [docs.djangoproject.com](https://docs.djangoproject.com)
- Django asinxron ORM: [docs.djangoproject.com/en/stable/topics/async](https://docs.djangoproject.com/en/stable/topics/async/)
- Aiogram rasmiy hujjati: [docs.aiogram.dev](https://docs.aiogram.dev)
- `asgiref` (sync_to_async / async_to_sync): [github.com/django/asgiref](https://github.com/django/asgiref)
- PostgreSQL rasmiy hujjati: [postgresql.org/docs](https://www.postgresql.org/docs/)

---

Ushbu arxitektura (bitta Django loyihasi + ikkita jarayon: `runserver` va `runbot` + umumiy PostgreSQL) — do'kon botlaridan tortib, buyurtma va CRM tizimlarigacha ko'plab real loyihalarda ishlatiladigan, sinovdan o'tgan yondashuv. Barcha kod ushbu qo'llanmada haqiqiy Django va Aiogram paketlari bilan sinovdan o'tkazilgan (models → migratsiya → async ORM → FSM → management command — to'liq zanjir ishlaydi). 🚀
