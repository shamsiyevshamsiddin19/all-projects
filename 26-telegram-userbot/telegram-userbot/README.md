# Telegram Userbot

Telethon asosidagi oddiy, kengaytiriladigan userbot.

> ⚠️ **Ogohlantirish:** Userbot — bu sizning shaxsiy akkauntingiz nomidan
> ishlaydigan avtomatlashtirilgan skript. Telegram qoidalariga zid ishlatilsa
> (spam, flood) akkaunt bloklanishi mumkin. Faqat o'zingiz uchun, ehtiyotkorlik
> bilan foydalaning.

## 1. API kalitlarini olish
1. https://my.telegram.org saytiga kiring
2. **API development tools** bo'limiga o'ting
3. Yangi ilova yarating va `api_id` hamda `api_hash` ni oling

## 2. O'rnatish
```bash
cd telegram-userbot
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

## 3. Sozlash
`.env.example` faylidan nusxa oling va to'ldiring:
```bash
copy .env.example .env       # Windows
```
`.env` ichiga `API_ID` va `API_HASH` ni yozing.

## 4. Ishga tushirish
```bash
python userbot.py
```
Birinchi marta telefon raqami va Telegram kodini so'raydi. Bir marta
kiritsangiz, `userbot.session` fayli yaratiladi va keyingi safar so'ramaydi.

## Buyruqlar
Buyruqlarni **o'zingiz** istalgan chatda yozasiz (prefiks — `.`):

| Buyruq | Vazifasi |
|--------|----------|
| `.ping` | Javob tezligini tekshiradi |
| `.alive` | Userbot ishlayotganini ko'rsatadi |
| `.help` | Barcha buyruqlar ro'yxati |
| `.id` | Chat / foydalanuvchi ID sini beradi |
| `.echo matn` | Matnni qaytaradi |
| `.del` | Javob berilgan xabarni o'chiradi |
| `.purge` | Javob berilgan xabardan boshlab hammasini o'chiradi |
| `.ai savol` | Gemini AI'dan javob |
| `.aijavob` | Javob berilgan xabarga javob matni yozib beradi |
| `.autoai on/off` | Yarim-avtomatik AI javob rejimi |
| `.ok` / `.no` | AI taklifini tasdiqlash / bekor qilish |

## Yarim-avtomatik AI javob rejimi
`.autoai on` — kelgan shaxsiy xabarga Gemini javob **taklifi** tayyorlab,
uni sizning **Saved Messages**ingizga yuboradi. Hech narsa siz tasdiqlamasdan
yuborilmaydi:
- Taklifga javoban `.ok` — o'sha javobni yuboradi
- `.ok yangi matn` — tahrirlab yuboradi
- `.no` — bekor qiladi

> Rejim xotirada saqlanadi — userbot qayta ishga tushsa, `.autoai on` ni
> qaytadan yoqish kerak.

## Yangi buyruq qo'shish
`plugins/` papkasiga yangi `.py` fayl yarating:

```python
from ._helpers import command, register_all

@command("salom", "Salomlashadi")
async def salom(event):
    await event.edit("Assalomu alaykum! 👋")

def register(client):
    register_all(client, __import__(__name__, fromlist=["_"]))
```
Userbotni qayta ishga tushiring — buyruq avtomatik yuklanadi.
