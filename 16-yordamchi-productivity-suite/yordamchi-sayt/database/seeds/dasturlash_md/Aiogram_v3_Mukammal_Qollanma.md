# 🤖 Aiogram 3 — Noldan Production'gacha Mukammal Qo'llanma

**Aiogram** — Python uchun eng tez, to'liq asinxron (`async/await`) va eng ko'p yuklab olinadigan Telegram Bot freymvorki. 2026-yil holatiga ko'ra so'nggi barqaror versiya **3.30.x** hisoblanadi (aiogram muntazam yangilanib turadi, shuning uchun `pip install -U aiogram` bilan doim yangilab turing).

Bu qo'llanma sizni ikki narsaga tayyorlaydi: **(1)** Aiogram 3 ning barcha asosiy va ilg'or imkoniyatlarini chuqur tushunish, **(2)** oddiy "bitta faylga yozilgan bot"dan haqiqiy, katta va production'ga tayyor loyiha strukturasiga o'tish.

**Manba:** rasmiy hujjatlar — [docs.aiogram.dev](https://docs.aiogram.dev)

---

## 📑 Mundarija

1. [Muhitni tayyorlash](#1-muhitni-tayyorlash)
2. [Professional loyiha strukturasi](#2-professional-loyiha-strukturasi)
3. [Asosiy arxitektura: Bot, Dispatcher, Router](#3-asosiy-arxitektura-bot-dispatcher-router)
4. [Konfiguratsiya — tokenni xavfsiz saqlash](#4-konfiguratsiya--tokenni-xavfsiz-saqlash)
5. [Handlerlar va filterlar chuqur tahlili](#5-handlerlar-va-filterlar-chuqur-tahlili)
6. [Klaviaturalar — to'liq qo'llanma](#6-klaviaturalar--toliq-qollanma)
7. [CallbackData factory va pagination](#7-callbackdata-factory-va-pagination)
8. [FSM — Holatlar mashinasi chuqur](#8-fsm--holatlar-mashinasi-chuqur)
9. [Media fayllar bilan ishlash](#9-media-fayllar-bilan-ishlash)
10. [Ommaviy xabar yuborish (broadcast)](#10-ommaviy-xabar-yuborish-broadcast)
11. [Middleware — chuqur va amaliy](#11-middleware--chuqur-va-amaliy)
12. [Custom filterlar yaratish](#12-custom-filterlar-yaratish)
13. [Routerlar bilan modulli arxitektura (to'liq loyiha)](#13-routerlar-bilan-modulli-arxitektura-toliq-loyiha)
14. [Xatoliklarni global ushlash](#14-xatoliklarni-global-ushlash)
15. [Ma'lumotlar bazasi bilan ishlash](#15-malumotlar-bazasi-bilan-ishlash)
16. [Ko'p tillilik (i18n)](#16-kop-tillilik-i18n)
17. [Production: Webhook, Docker, deploy](#17-production-webhook-docker-deploy)
18. [Xavfsizlik va Best Practice cheklist](#18-xavfsizlik-va-best-practice-cheklist)
19. [Yakuniy to'liq ishchi misol](#19-yakuniy-toliq-ishchi-misol)
20. [Foydali manbalar](#20-foydali-manbalar)

---

## 1. Muhitni tayyorlash

**Talablar:** Python 3.9+ (tavsiya: 3.11 yoki 3.12).

```bash
# 1. Virtual muhit yaratish (loyihalarni bir-biridan izolyatsiya qilish uchun MAJBURIY odat)
python -m venv venv

# 2. Faollashtirish
source venv/bin/activate      # Linux / macOS
venv\Scripts\activate         # Windows

# 3. Kerakli kutubxonalarni o'rnatish
pip install aiogram python-dotenv
```

`requirements.txt` yarating — bu loyihani boshqa kompyuterda yoki serverda bir zumda tiklash imkonini beradi:

```bash
pip freeze > requirements.txt
```

> 💡 **Nega venv kerak?** Har bir loyihaning o'z kutubxona versiyalari bo'ladi. Venv'siz ishlasangiz, bitta loyihada kutubxonani yangilash boshqa loyihani buzib qo'yishi mumkin.

---

## 2. Professional loyiha strukturasi

Bitta faylga (`main.py`) 500-1000 qatorlik kod yozish kichik test uchun yaroqli, lekin real loyihada **modullarga ajratish shart**. Aiogram jamoasi tavsiya qiladigan tuzilma:

```
mybot/
├── .env                     # Maxfiy ma'lumotlar (token, DB parol) — Git'ga qo'shilmaydi
├── .gitignore
├── requirements.txt
├── main.py                  # Kirish nuqtasi — botni ishga tushiradi
├── config.py                # .env'ni o'qib, sozlamalarni beradi
│
├── handlers/                # Foydalanuvchi xabarlariga javob beruvchi funksiyalar
│   ├── __init__.py
│   ├── user.py               # Oddiy foydalanuvchi komandalari
│   ├── admin.py               # Faqat admin uchun komandalar
│   └── errors.py              # Xatoliklarni ushlash
│
├── keyboards/                # Klaviaturalar shu yerda generatsiya qilinadi
│   ├── __init__.py
│   ├── reply.py
│   └── inline.py
│
├── middlewares/               # Har bir xabardan oldin ishlaydigan qatlamlar
│   ├── __init__.py
│   ├── throttling.py
│   └── db.py
│
├── filters/                   # Maxsus (custom) filterlar
│   ├── __init__.py
│   └── admin.py
│
├── states/                    # FSM holatlari
│   ├── __init__.py
│   └── registration.py
│
├── database/                  # Ma'lumotlar bazasi qatlami
│   ├── __init__.py
│   ├── models.py
│   └── requests.py
│
└── downloads/                  # Yuklab olingan fayllar (bo'sh papka, .gitkeep bilan)
```

`.gitignore` (token va vaqtinchalik fayllarni GitHub'ga chiqarib yubormaslik uchun **juda muhim**):

```
venv/
.env
__pycache__/
*.pyc
db.sqlite3
downloads/*
!downloads/.gitkeep
```

---

## 3. Asosiy arxitektura: Bot, Dispatcher, Router

Aiogram 3 uchta asosiy obyektga tayanadi:

| Obyekt | Vazifasi |
|---|---|
| **Bot** | Telegram API bilan bevosita muloqot qiladi (xabar yuborish, fayl yuklash va h.k.) |
| **Dispatcher** | Kelgan yangiliklarni (update) qabul qiladi va mos handlerga yo'naltiradi. Ildiz (root) Router hisoblanadi |
| **Router** | Handlerlar guruhi. Katta loyihada har bir modul (`user.py`, `admin.py`) o'z Router'iga ega bo'ladi, so'ng ular Dispatcher'ga ulanadi |

```python
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

# ⚠️ aiogram 3.7+ da parse_mode endi to'g'ridan-to'g'ri Bot(parse_mode=...) orqali emas,
# DefaultBotProperties orqali beriladi — bu eski qo'llanmalarda ko'p uchraydigan xato joy.
bot = Bot(
    token="TOKEN",
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()
```

**Polling vs Webhook:**

| | Polling | Webhook |
|---|---|---|
| Ishlash prinsipi | Bot Telegram serveriga o'zi doimiy so'rov yuboradi ("yangilik bormi?") | Telegram bot serveringizga o'zi xabar yuboradi |
| Sozlash qulayligi | Juda oson, domen/SSL kerak emas | Domen + SSL sertifikat kerak |
| Qachon ishlatiladi | Rivojlantirish (development), kichik-o'rta botlar | Yuqori yuklamali production botlar |

```python
import asyncio

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
```

Webhook sozlash — 17-bo'limda batafsil.

---

## 4. Konfiguratsiya — tokenni xavfsiz saqlash

❌ **Hech qachon** tokenni kodga to'g'ridan-to'g'ri yozmang (GitHub'ga tasodifan tushib ketsa, botingiz o'g'irlanadi). ✅ `.env` faylida saqlang.

`.env`:
```
BOT_TOKEN=123456789:AAExampleTokenHereDoNotShareItWithAnyone
ADMIN_IDS=123456789,987654321
```

`config.py`:
```python
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()  # .env faylini o'qib, muhit o'zgaruvchilariga yuklaydi


@dataclass
class Config:
    bot_token: str
    admin_ids: list[int]


def load_config() -> Config:
    return Config(
        bot_token=os.getenv("BOT_TOKEN"),
        admin_ids=[int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x],
    )
```

`main.py` ichida ishlatish:
```python
from config import load_config

config = load_config()
bot = Bot(token=config.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
```

---

## 5. Handlerlar va filterlar chuqur tahlili

Handler — bu ma'lum bir hodisaga (xabar, callback, yangi a'zo va h.k.) javob beruvchi `async` funksiya. Aiogram handlerlarni **yozilish tartibida** tekshiradi va **birinchi mos kelgan** filterni ishlatadi — shuning uchun tor (aniq) filterlarni yuqoriga, keng filterlarni pastga yozish kerak.

### Komandalar

```python
from aiogram.filters import CommandStart, Command, CommandObject

@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("Salom!")

# Bir nechta komandani bitta funksiyaga ulash
@router.message(Command("help", "info"))
async def cmd_help(message: Message):
    await message.answer("Yordam matni...")

# Komandadan keyingi argumentni olish: /start ref_12345
@router.message(CommandStart(deep_link=True))
async def cmd_start_with_arg(message: Message, command: CommandObject):
    referral_code = command.args
    await message.answer(f"Referal kod: {referral_code}")
```

### `F` — magic filter

`F` orqali istalgan obyekt maydonini (text, chat, from_user va h.k.) tekshirish mumkin:

```python
from aiogram import F

# Aniq mos kelish (katta-kichik harf muhim)
@router.message(F.text == "Salom")
async def salom(message: Message): ...

# Katta-kichik harfga e'tibor bermasdan, ichida bor-yo'qligini tekshirish
@router.message(F.text.lower().contains("rahmat"))
async def rahmat(message: Message): ...

# Regex orqali
@router.message(F.text.regexp(r"^\d+$"))
async def faqat_raqam(message: Message): ...

# Bir nechta variantdan birortasi
@router.message(F.text.in_(["Ha", "Yo'q", "Bilmadim"]))
async def variant(message: Message): ...

# Faqat guruh/superguruh xabarlarini ushlash
@router.message(F.chat.type.in_({"group", "supergroup"}))
async def guruh_xabari(message: Message): ...

# Faqat shaxsiy chat
@router.message(F.chat.type == "private")
async def shaxsiy_xabar(message: Message): ...
```

### StateFilter

```python
from aiogram.filters import StateFilter

# Ikkalasi ham bir xil ishlaydi:
@router.message(RegState.ism)
@router.message(StateFilter(RegState.ism))
async def get_ism(message: Message, state: FSMContext): ...

# Faqat hech qanday state bo'lmaganda ishlaydi
@router.message(StateFilter(None))
async def erkin_holat(message: Message): ...
```

### Filterlarni birlashtirish

Bir handlerda vergul bilan yozilgan filterlarning **barchasi** rost bo'lishi kerak (AND mantiqi):

```python
@router.message(Command("admin"), F.chat.type == "private")
async def admin_panel(message: Message): ...
```

---

## 6. Klaviaturalar — to'liq qo'llanma

### 6.1 ReplyKeyboard (klaviatura o'rniga chiqadigan tugmalar)

```python
from aiogram.utils.keyboard import ReplyKeyboardBuilder

@router.message(Command("menu"))
async def show_menu(message: Message):
    builder = ReplyKeyboardBuilder()
    builder.button(text="🛍 Mahsulotlar")
    builder.button(text="📞 Aloqa")

    # Telefon raqamini so'rash (Telegram avtomatik so'raydi, foydalanuvchi faqat tasdiqlaydi)
    builder.button(text="📱 Raqamni yuborish", request_contact=True)

    # Lokatsiyani so'rash
    builder.button(text="📍 Manzilni yuborish", request_location=True)

    builder.adjust(2, 1, 1)  # qatorlarga nechtadan joylashishini belgilaydi

    await message.answer(
        "Menyu:",
        reply_markup=builder.as_markup(
            resize_keyboard=True,      # tugmalarni ixcham qiladi
            one_time_keyboard=False,   # True bo'lsa, bosilgach klaviatura yopiladi
            input_field_placeholder="Tanlang..."
        )
    )
```

Klaviaturani olib tashlash:
```python
from aiogram.types import ReplyKeyboardRemove

@router.message(Command("hide"))
async def hide_menu(message: Message):
    await message.answer("Klaviatura olib tashlandi.", reply_markup=ReplyKeyboardRemove())
```

### 6.2 InlineKeyboard (xabar tanasiga yopishgan tugmalar)

```python
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import WebAppInfo

@router.message(Command("links"))
async def show_links(message: Message):
    builder = InlineKeyboardBuilder()

    # Oddiy callback tugma
    builder.button(text="👍 Yoqdi", callback_data="like")

    # Tashqi havolaga o'tuvchi tugma (callback yubormaydi, brauzer/kanalni ochadi)
    builder.button(text="🔗 Kanalimiz", url="https://t.me/example_channel")

    # Telegram Mini App (Web App) ochuvchi tugma
    builder.button(text="🌐 Web ilova", web_app=WebAppInfo(url="https://example.com/app"))

    # Boshqa chatga shu botni inline rejimda ulash uchun tugma
    builder.button(text="🔍 Do'stga ulashish", switch_inline_query="tavsiya")

    builder.adjust(1)
    await message.answer("Tanlang:", reply_markup=builder.as_markup())
```

### 6.3 Ro'yxatdan dinamik klaviatura yasash

```python
@router.message(Command("fruits"))
async def fruits_handler(message: Message):
    fruits = ["🍎 Olma", "🍌 Banan", "🍇 Uzum", "🍊 Apelsin"]
    builder = InlineKeyboardBuilder()
    for fruit in fruits:
        builder.button(text=fruit, callback_data=f"fruit_{fruit}")
    builder.adjust(2)
    await message.answer("Meva tanlang:", reply_markup=builder.as_markup())
```

---

## 7. CallbackData factory va pagination

Oddiy `callback_data="matn"` faqat oddiy holatlar uchun yetarli. Bir nechta ma'lumotni (kategoriya, ID, sahifa raqami) bitta tugmaga yopishtirish uchun `CallbackData` klassi ishlatiladi — u avtomatik ravishda `"prod:laptop:5"` kabi satrga serialize qiladi va qayta o'qishda tiplarni (int, str) to'g'ri tiklaydi.

```python
from aiogram.filters.callback_data import CallbackData

class ProductCallback(CallbackData, prefix="prod"):
    category: str
    item_id: int

@router.message(Command("shop"))
async def shop_handler(message: Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="📱 Telefon #1", callback_data=ProductCallback(category="phone", item_id=1))
    builder.button(text="💻 Noutbuk #5", callback_data=ProductCallback(category="laptop", item_id=5))
    await message.answer("Tovar tanlang:", reply_markup=builder.as_markup())

# Faqat kategoriyasi "laptop" bo'lganlarni ushlash
@router.callback_query(ProductCallback.filter(F.category == "laptop"))
async def laptop_clicked(call: CallbackQuery, callback_data: ProductCallback):
    await call.answer()
    await call.message.answer(f"Noutbuk #{callback_data.item_id} tanlandi!")
```

### Amaliy misol: sahifalash (pagination)

```python
class PageCallback(CallbackData, prefix="page"):
    action: str   # "prev" yoki "next"
    page: int

def build_pagination_kb(page: int, total_pages: int):
    builder = InlineKeyboardBuilder()
    if page > 1:
        builder.button(text="⬅️", callback_data=PageCallback(action="prev", page=page - 1))
    builder.button(text=f"{page}/{total_pages}", callback_data="ignore")
    if page < total_pages:
        builder.button(text="➡️", callback_data=PageCallback(action="next", page=page + 1))
    builder.adjust(3)
    return builder.as_markup()

@router.message(Command("catalog"))
async def open_catalog(message: Message):
    await message.answer("1-sahifa", reply_markup=build_pagination_kb(page=1, total_pages=5))

@router.callback_query(PageCallback.filter())
async def change_page(call: CallbackQuery, callback_data: PageCallback):
    await call.message.edit_text(
        f"{callback_data.page}-sahifa",
        reply_markup=build_pagination_kb(page=callback_data.page, total_pages=5)
    )
    await call.answer()
```

> ⚠️ Har bir `callback_query` handlerida **albatta** `await call.answer()` chaqiring — aks holda foydalanuvchi tugmasi ustida "soat" belgisi aylanaverib, keyin "vaqt tugadi" degan xatolik chiqadi.

---

## 8. FSM — Holatlar mashinasi chuqur

FSM (Finite State Machine) — foydalanuvchidan bosqichma-bosqich ma'lumot yig'ish uchun (masalan, ro'yxatdan o'tish: Ism → Yosh → Telefon).

### 8.1 Storage tanlash

```python
from aiogram.fsm.storage.memory import MemoryStorage
dp = Dispatcher(storage=MemoryStorage())
```

`MemoryStorage` — barcha holatlarni **RAM'da** saqlaydi. Bot qayta ishga tushsa (deploy, xato, restart), foydalanuvchilarning barcha holatlari o'chib ketadi. Kichik loyihalar va rivojlantirish uchun yetarli.

Production'da esa **RedisStorage** tavsiya etiladi — bot qayta ishga tushsa ham foydalanuvchi holati saqlanib qoladi:

```python
from aiogram.fsm.storage.redis import RedisStorage

storage = RedisStorage.from_url("redis://localhost:6379/0")
dp = Dispatcher(storage=storage)
```

### 8.2 To'liq FSM misoli (validatsiya bilan)

```python
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

class RegState(StatesGroup):
    ism = State()
    yosh = State()
    telefon = State()

@router.message(Command("reg"))
async def start_reg(message: Message, state: FSMContext):
    await message.answer("To'liq ismingizni kiriting:")
    await state.set_state(RegState.ism)

@router.message(RegState.ism)
async def get_ism(message: Message, state: FSMContext):
    if len(message.text) < 2:
        await message.answer("Ism juda qisqa, qayta kiriting:")
        return  # state o'zgarmaydi — qayta shu bosqichda so'raydi
    await state.update_data(ism=message.text)
    await message.answer("Yoshingiz nechada?")
    await state.set_state(RegState.yosh)

@router.message(RegState.yosh)
async def get_yosh(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Faqat raqam kiriting:")
        return
    await state.update_data(yosh=int(message.text))
    await message.answer("Telefon raqamingiz (+998...):")
    await state.set_state(RegState.telefon)

@router.message(RegState.telefon)
async def get_telefon(message: Message, state: FSMContext):
    data = await state.get_data()  # avval saqlangan barcha ma'lumotlar
    await message.answer(
        f"✅ Ro'yxatdan o'tdingiz!\nIsm: {data['ism']}\nYosh: {data['yosh']}\nTel: {message.text}"
    )
    await state.clear()  # holatni va yig'ilgan ma'lumotni tozalash

# Jarayonning istalgan bosqichida bekor qilish imkoniyati
@router.message(Command("cancel"))
async def cancel_handler(message: Message, state: FSMContext):
    if await state.get_state() is None:
        return
    await state.clear()
    await message.answer("❌ Jarayon bekor qilindi.")
```

> 💡 **Muhim odat:** har bir FSM jarayoniga `/cancel` kabi chiqish yo'lini qo'shing — aks holda foydalanuvchi bosqichda "qotib qolsa", botning boshqa hech bir buyrug'iga javob ololmay qoladi (chunki matn handlerlari state filter bilan bog'langan).

---

## 9. Media fayllar bilan ishlash

### 9.1 Qabul qilish

```python
@router.message(F.photo)
async def handle_photo(message: Message):
    # message.photo — turli o'lchamdagi versiyalar ro'yxati, [-1] eng sifatlisi
    photo_id = message.photo[-1].file_id
    await message.reply_photo(photo=photo_id, caption="📸 Rasm qabul qilindi!")

@router.message(F.video)
async def handle_video(message: Message):
    await message.answer(f"🎬 Video hajmi: {message.video.file_size // 1024} KB")

@router.message(F.voice)
async def handle_voice(message: Message):
    await message.answer(f"🎤 Ovozli xabar: {message.voice.duration} soniya")

@router.message(F.document)
async def handle_doc(message: Message):
    doc = message.document
    await message.answer(f"📁 {doc.file_name} ({doc.file_size // 1024} KB, {doc.mime_type})")

# Bir nechta turdagi kontentni bitta handlerda ushlash
@router.message(F.content_type.in_({"photo", "video", "document"}))
async def any_media(message: Message):
    await message.answer("Media qabul qilindi ✅")
```

### 9.2 Faylni diskka yuklab olish

```python
@router.message(F.document)
async def save_document(message: Message, bot: Bot):
    destination = f"downloads/{message.document.file_name}"
    await bot.download(message.document, destination=destination)
    await message.answer("Fayl serverga saqlandi ✅")
```

### 9.3 Albom (media group) yuborish

```python
from aiogram.utils.media_group import MediaGroupBuilder

@router.message(Command("album"))
async def send_album(message: Message):
    album = MediaGroupBuilder(caption="Umumiy tavsif barcha rasmlar ostida")
    album.add_photo(photo="AgACAgI...")   # file_id yoki URL
    album.add_photo(photo="AgACAgI...")
    album.add_video(video="BAACAgI...")
    await message.answer_media_group(media=album.build())
```

### 9.4 Faylni boshqa foydalanuvchiga uzatish

`file_id` orqali faylni qayta yuklamasdan, bir zumda boshqa chatga jo'natish mumkin:

```python
@router.message(F.document)
async def forward_to_admin(message: Message, bot: Bot, config):
    for admin_id in config.admin_ids:
        await bot.send_document(
            chat_id=admin_id,
            document=message.document.file_id,
            caption=f"{message.from_user.full_name} dan fayl"
        )
```

---

## 10. Ommaviy xabar yuborish (broadcast)

Barcha foydalanuvchilarga xabar yuborishda ikkita narsani hisobga olish shart: **(1)** foydalanuvchi botni bloklagan bo'lishi mumkin, **(2)** Telegram sekundiga taxminan 30 ta xabar limitini qo'yadi.

```python
import asyncio
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter

async def broadcast(bot: Bot, user_ids: list[int], text: str) -> tuple[int, int]:
    success, blocked = 0, 0
    for user_id in user_ids:
        try:
            await bot.send_message(user_id, text)
            success += 1
        except TelegramForbiddenError:
            blocked += 1  # foydalanuvchi botni bloklagan
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after)  # Telegram qancha kutish kerakligini aytadi
            await bot.send_message(user_id, text)
            success += 1
        await asyncio.sleep(0.05)  # ~20 xabar/soniya — limitdan xavfsiz chegara
    return success, blocked
```

---

## 11. Middleware — chuqur va amaliy

Middleware — handlerga yetib borishdan **oldin** (yoki keyin) ishga tushadigan qatlam. Ikki turi bor:

- **Outer middleware** — filterlardan **oldin** ishlaydi, har doim chaqiriladi (filtrga mos kelmasa ham).
- **Inner middleware** (odatiy) — filterlar mos kelgandan **keyin**, handlerdan oldin ishlaydi.

### 11.1 Anti-flood (throttling) middleware

Foydalanuvchi bir necha soniyada o'nlab xabar yuborib botni "buzishi"ning oldini olish:

```python
from cachetools import TTLCache
from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Dict, Any, Awaitable

class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, rate_limit: float = 0.7):
        self.cache = TTLCache(maxsize=10_000, ttl=rate_limit)

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        if event.chat.id in self.cache:
            return  # tezkor takroriy xabarni jimgina e'tiborsiz qoldiramiz
        self.cache[event.chat.id] = True
        return await handler(event, data)

dp.message.middleware(ThrottlingMiddleware(rate_limit=0.7))
```

### 11.2 Dependency Injection — DB session'ni handlerga uzatish

Middleware orqali handlerga tayyor obyekt (masalan, DB session) "in'yeksiya" qilish mumkin — bu Aiogram 3 ning eng qulay imkoniyatlaridan biri:

```python
class DbSessionMiddleware(BaseMiddleware):
    def __init__(self, session_pool):
        self.session_pool = session_pool

    async def __call__(self, handler, event, data: Dict[str, Any]):
        async with self.session_pool() as session:
            data["session"] = session  # endi har bir handler shu argumentni oladi
            return await handler(event, data)

dp.update.middleware(DbSessionMiddleware(session_pool=async_session))
```

Handlerda ishlatish:
```python
@router.message(Command("me"))
async def cmd_me(message: Message, session):  # 'session' avtomatik keladi!
    user = await session.get(User, message.from_user.id)
    await message.answer(f"Siz: {user.full_name}")
```

### 11.3 Logging middleware

```python
import logging

class LoggingMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Message, data):
        logging.info(f"{event.from_user.id}: {event.text}")
        return await handler(event, data)
```

---

## 12. Custom filterlar yaratish

Tayyor filterlar yetmasa, o'z filteringizni yozishingiz mumkin — bu shunchaki `BaseFilter`dan meros oluvchi klass:

```python
from aiogram.filters import BaseFilter
from aiogram.types import Message

class IsAdmin(BaseFilter):
    def __init__(self, admin_ids: list[int]):
        self.admin_ids = admin_ids

    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in self.admin_ids


@router.message(Command("admin"), IsAdmin(admin_ids=[123456789]))
async def admin_panel(message: Message):
    await message.answer("🔑 Admin panelga xush kelibsiz!")
```

---

## 13. Routerlar bilan modulli arxitektura (to'liq loyiha)

Endi 2-bo'limdagi strukturani to'liq kod bilan ko'raylik.

**`keyboards/reply.py`:**
```python
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.types import ReplyKeyboardMarkup

def main_menu() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="🛍 Mahsulotlar")
    builder.button(text="📞 Aloqa")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)
```

**`handlers/user.py`:**
```python
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message

from keyboards.reply import main_menu

router = Router(name="user")

@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(f"Salom, {message.from_user.first_name}!", reply_markup=main_menu())

@router.message(F.text == "📞 Aloqa")
async def contact(message: Message):
    await message.answer("+998 90 123 45 67")
```

**`handlers/admin.py`:**
```python
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from filters.admin import IsAdmin

router = Router(name="admin")
router.message.filter(IsAdmin(admin_ids=[123456789]))  # ushbu routerdagi BARCHA handlerlarga qo'llanadi

@router.message(Command("stats"))
async def stats(message: Message):
    await message.answer("📊 Statistika: 1234 ta foydalanuvchi")
```

**`main.py`:**
```python
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import load_config
from handlers import user, admin, errors
from middlewares.throttling import ThrottlingMiddleware

logging.basicConfig(level=logging.INFO)


async def main():
    config = load_config()

    bot = Bot(token=config.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    dp.message.middleware(ThrottlingMiddleware())

    dp.include_router(user.router)
    dp.include_router(admin.router)
    dp.include_router(errors.router)

    await bot.delete_webhook(drop_pending_updates=True)  # eski so'rovlarni tozalash
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot to'xtatildi")
```

> 📌 `dp.include_router()` tartibi muhim — Dispatcher ham Router bo'lgani uchun, xabar yuqoridan pastga qarab routerlar orasida qidiriladi. Tor/maxsus routerlarni (masalan, `admin`) tepaga, umumiy routerni pastga qo'ying.

---

## 14. Xatoliklarni global ushlash

Har bir handlerni alohida `try/except` bilan o'rashning o'rniga, butun bot uchun **yagona** xato ushlagich yozish mumkin:

```python
from aiogram import Router
from aiogram.types import ErrorEvent
import logging

router = Router(name="errors")

@router.errors()
async def global_error_handler(event: ErrorEvent):
    logging.exception(f"Xatolik: {event.exception}\nUpdate: {event.update}")
    if event.update.message:
        await event.update.message.answer("⚠️ Kutilmagan xatolik yuz berdi. Keyinroq urinib ko'ring.")
```

Bu handler `main.py`da boshqa routerlar bilan birga `dp.include_router(errors.router)` orqali ulanadi (13-bo'limga qarang).

---

## 15. Ma'lumotlar bazasi bilan ishlash

Kichik-o'rta botlar uchun **SQLite + SQLAlchemy (async)** — eng oson va ishonchli kombinatsiya.

```bash
pip install sqlalchemy aiosqlite
```

**`database/models.py`:**
```python
from sqlalchemy import BigInteger
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

engine = create_async_engine("sqlite+aiosqlite:///db.sqlite3")
async_session = async_sessionmaker(engine, expire_on_commit=False)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    full_name: Mapped[str]


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

**`database/requests.py`:**
```python
from sqlalchemy import select
from database.models import async_session, User


async def add_user(tg_id: int, full_name: str) -> None:
    async with async_session() as session:
        exists = await session.scalar(select(User).where(User.tg_id == tg_id))
        if not exists:
            session.add(User(tg_id=tg_id, full_name=full_name))
            await session.commit()


async def get_all_user_ids() -> list[int]:
    async with async_session() as session:
        result = await session.scalars(select(User.tg_id))
        return list(result)
```

`main.py`da ishga tushirishda chaqiriladi:
```python
from database.models import init_db

async def main():
    await init_db()
    ...
```

Handlerda foydalanish:
```python
from database.requests import add_user

@router.message(CommandStart())
async def cmd_start(message: Message):
    await add_user(message.from_user.id, message.from_user.full_name)
    await message.answer("Ro'yxatdan o'tdingiz!")
```

---

## 16. Ko'p tillilik (i18n)

Aiogram 3 tayyor i18n vositasini majburlamaydi, shuning uchun eng sodda va tez usul — lug'at (dictionary) asosida:

```python
LEXICON = {
    "uz": {"start": "Xush kelibsiz!", "help": "Yordam matni"},
    "ru": {"start": "Добро пожаловать!", "help": "Текст помощи"},
    "en": {"start": "Welcome!", "help": "Help text"},
}

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    await message.answer(LEXICON[lang]["start"])
```

Katta loyihalarda `fluent.runtime` (Mozilla Fluent formati) kutubxonasi orqali `.ftl` fayllarga matnlarni chiqarib qo'yish tavsiya etiladi — bu tarjimonlarga kod bilan ishlamasdan tarjima qilish imkonini beradi.

---

## 17. Production: Webhook, Docker, deploy

### 17.1 Webhook (aiohttp orqali)

```python
from aiohttp import web
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = "https://sizning-domeningiz.uz" + WEBHOOK_PATH


async def on_startup(bot: Bot):
    await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)


def main():
    dp.startup.register(on_startup)

    app = web.Application()
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    web.run_app(app, host="0.0.0.0", port=8080)


if __name__ == "__main__":
    main()
```

Bunda `nginx` orqali `https://domain.uz/webhook` manzili serverdagi `8080` portga proksi qilinadi (SSL sertifikat — masalan, Let's Encrypt orqali).

### 17.2 Docker

`Dockerfile`:
```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

`docker-compose.yml`:
```yaml
version: "3.9"
services:
  bot:
    build: .
    restart: always
    env_file: .env
    volumes:
      - ./downloads:/app/downloads
      - ./db.sqlite3:/app/db.sqlite3
```

Ishga tushirish:
```bash
docker compose up -d --build
```

### 17.3 Serverda doimiy ishlash (systemd)

`/etc/systemd/system/mybot.service`:
```ini
[Unit]
Description=Telegram Bot
After=network.target

[Service]
WorkingDirectory=/home/user/mybot
ExecStart=/home/user/mybot/venv/bin/python main.py
Restart=always
User=user

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable mybot
sudo systemctl start mybot
```

---

## 18. Xavfsizlik va Best Practice cheklist

- [ ] Token `.env` faylida, `.gitignore`ga qo'shilgan
- [ ] `bot.delete_webhook(drop_pending_updates=True)` polling boshlashdan oldin chaqirilgan (eski so'rovlar to'planib qolmasligi uchun)
- [ ] Har bir uzun jarayon (FSM)da `/cancel` chiqish yo'li bor
- [ ] `callback_query` handlerlarida har doim `call.answer()` chaqiriladi
- [ ] Tashqi API/DB chaqiruvlar `try/except` bilan himoyalangan, global error handler mavjud
- [ ] Broadcast'da `TelegramForbiddenError` va flood-limit hisobga olingan
- [ ] Production'da `MemoryStorage` emas, `RedisStorage` ishlatiladi
- [ ] Loyiha routerlarga bo'lingan, bitta 1000+ qatorlik faylda emas
- [ ] Loglar (`logging`) yoqilgan — xatoni consolega emas, faylga yoki monitoring tizimiga yozish tavsiya etiladi
- [ ] `requirements.txt` versiyalari qattiq belgilangan (`aiogram==3.30.0`) — kutilmagan breaking change'lardan himoya

---

## 19. Yakuniy to'liq ishchi misol

Quyidagi kodni nusxa olib, `TOKEN`ni almashtirsangiz, bitta faylda barcha asosiy imkoniyatlar bilan ishlaydigan bot olasiz (o'rganish/test uchun; real loyihada 13-bo'limdagi strukturani ishlating):

```python
import asyncio
import logging
from typing import Callable, Dict, Any, Awaitable

from aiogram import Bot, Dispatcher, F, Router, BaseMiddleware
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Message, CallbackQuery, ErrorEvent
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData

logging.basicConfig(level=logging.INFO)

TOKEN = "123456789:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())
router = Router()


# === FSM ===
class RegState(StatesGroup):
    ism = State()
    yosh = State()


# === CallbackData ===
class ProductCB(CallbackData, prefix="prod"):
    cat: str
    id: int


# === Middleware: oddiy anti-flood ===
class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self):
        self.last_seen: Dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        import time
        now = time.monotonic()
        chat_id = event.chat.id
        if chat_id in self.last_seen and now - self.last_seen[chat_id] < 0.5:
            return
        self.last_seen[chat_id] = now
        return await handler(event, data)


dp.message.middleware(ThrottlingMiddleware())


# === Handlerlar ===
@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(f"Salom, <b>{message.from_user.first_name}</b>! /help — yordam.")


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer("/start /menu /inline /shop /reg /photo")


@router.message(Command("menu"))
async def cmd_menu(message: Message):
    kb = ReplyKeyboardBuilder()
    kb.button(text="🛍 Mahsulotlar")
    kb.button(text="📞 Aloqa")
    kb.adjust(2)
    await message.answer("Tanlang:", reply_markup=kb.as_markup(resize_keyboard=True))


@router.message(F.text == "📞 Aloqa")
async def reply_contact(message: Message):
    await message.answer("+998 90 123 45 67")


@router.message(Command("inline"))
async def cmd_inline(message: Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="👍", callback_data="like")
    kb.button(text="👎", callback_data="dislike")
    await message.answer("Baholang:", reply_markup=kb.as_markup())


@router.callback_query(F.data == "like")
async def cb_like(call: CallbackQuery):
    await call.answer("Rahmat!")
    await call.message.edit_text("👍 qabul qilindi.")


@router.callback_query(F.data == "dislike")
async def cb_dislike(call: CallbackQuery):
    await call.answer("Tushundik.")
    await call.message.edit_text("👎 qabul qilindi.")


@router.message(Command("shop"))
async def cmd_shop(message: Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="📱 Telefon", callback_data=ProductCB(cat="phone", id=1))
    kb.button(text="💻 Noutbuk", callback_data=ProductCB(cat="laptop", id=5))
    kb.adjust(1)
    await message.answer("Tanlang:", reply_markup=kb.as_markup())


@router.callback_query(ProductCB.filter())
async def cb_product(call: CallbackQuery, callback_data: ProductCB):
    await call.answer()
    await call.message.answer(f"{callback_data.cat} #{callback_data.id} tanlandi")


@router.message(Command("reg"))
async def cmd_reg(message: Message, state: FSMContext):
    await message.answer("Ismingiz:")
    await state.set_state(RegState.ism)


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    if await state.get_state() is None:
        return
    await state.clear()
    await message.answer("❌ Bekor qilindi.")


@router.message(RegState.ism)
async def fsm_ism(message: Message, state: FSMContext):
    await state.update_data(ism=message.text)
    await message.answer("Yoshingiz:")
    await state.set_state(RegState.yosh)


@router.message(RegState.yosh)
async def fsm_yosh(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Faqat raqam kiriting:")
        return
    data = await state.get_data()
    await message.answer(f"✅ {data['ism']}, {message.text} yosh")
    await state.clear()


@router.message(F.photo)
async def on_photo(message: Message):
    await message.reply_photo(photo=message.photo[-1].file_id, caption="📸 Rasm qabul qilindi!")


@router.message(F.document)
async def on_doc(message: Message):
    await message.answer(f"📁 Fayl: {message.document.file_name}")


# === Global xato ushlagich ===
@router.errors()
async def error_handler(event: ErrorEvent):
    logging.exception(f"Xatolik: {event.exception}")


dp.include_router(router)


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("Bot ishga tushdi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot to'xtatildi")
```

---

## 20. Foydali manbalar

- Rasmiy hujjat: [docs.aiogram.dev](https://docs.aiogram.dev)
- GitHub: [github.com/aiogram/aiogram](https://github.com/aiogram/aiogram)
- Rasmiy Telegram community: `@aiogram_live` (rasmiy chat guruhi)
- Telegram Bot API rasmiy hujjati: [core.telegram.org/bots/api](https://core.telegram.org/bots/api)

---

Shu qo'llanmani asos qilib, kichik botdan boshlab, uni bosqichma-bosqich (FSM → klaviaturalar → DB → middleware → routerlar → Docker/webhook) kengaytirib borsangiz, real production darajasidagi Telegram botini yarata olasiz. 🚀
