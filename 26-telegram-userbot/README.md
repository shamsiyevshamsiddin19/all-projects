# 🤖 Telegram Userbot & Automation Suite

Telethon (Python) asosidagi ko'p akkauntli Telegram userbot hamda Instagram yordamchi boti to'plami. Oddiy botlardan farqli ravishda, bu skript bevosita shaxsiy foydalanuvchi akkauntlari nomidan intellektual tarzda ishlaydi.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![Telethon](https://img.shields.io/badge/Telethon-MTProto-2CA5E0?logo=telegram&logoColor=white)
![Gemini AI](https://img.shields.io/badge/Gemini_AI-Flash_Latest-8E75C2?logo=google&logoColor=white)
![aiohttp](https://img.shields.io/badge/aiohttp-Web_Panel-2C5BB4?logo=python&logoColor=white)
![systemd](https://img.shields.io/badge/systemd-Multi_Service-black?logo=linux&logoColor=white)

---

## 📂 Loyiha tuzilmasi

```text
26-telegram-userbot/
├── telegram-userbot/       # Telethon asosidagi asosiy Telegram userbot
│   ├── config.py           # Sozlamalar va muhit o'zgaruvchilari
│   ├── userbot.py          # Asosiy ishga tushirish skripti
│   ├── webpanel.py         # Minimalist aiohttp veb-boshqaruv paneli (port 8123)
│   ├── plugins/            # Modulli plaginlar to'plami
│   │   ├── autodraft.py    # Javob qoralamasini yozuvchi plagin (SaveDraftRequest)
│   │   ├── autoreply.py    # Gemini AI bilan intellektual avto-javob
│   │   ├── autoai.py       # Yarim-avtomatik tasdiqli AI javob rejimi
│   │   ├── ai.py           # Bevosita .ai buyrug'i
│   │   ├── autoread.py     # Kanallar/guruhlarni avtomatik o'qilgan qilish
│   │   ├── basic.py        # .ping, .alive, .id buyruqlari
│   │   ├── tools.py        # .del, .purge, .echo vositalari
│   │   ├── control.py      # Userbot holatini boshqarish
│   │   ├── statewatch.py   # Restartsiz sozlamalarni yangilovchi modul
│   │   └── _state.py       # State boshqaruvi
│   ├── deploy/             # Hetzner serveri uchun systemd va monitor skriptlari
│   └── persona.txt.example # AI javob uslubi va ko'rsatmalar
└── instagram-bot/          # Instagram va Gemini AI integratsiyasi
    ├── app.py              # Instagram webhook / bot ilovasi
    ├── gemini_client.py    # Gemini API mijozi
    └── instagram_client.py # Instagram Graph API mijozi
```

---

## ✨ Imkoniyatlar va Plaginlar

| Plagin | Vazifasi va Buyruqlari |
| :--- | :--- |
| **`autodraft`** | Javobni darhol yubormasdan, chatda **qoralama (draft)** sifatida tayyorlab qo'yadi. Foydalanuvchi ko'rib, tahrirlab o'zi yuboradi. |
| **`autoreply`** | Shaxsiy chatlar va guruhlarda mention/reply kelganda kontekst asosida tabiiy intellektual javob yozadi. |
| **`autoai`** | Yarim-avtomatik rejim: kelgan xabarga Gemini taklif tayyorlaydi, `Saved Messages`ga tashlaydi, `.ok` yoki `.no` orqali tasdiqlanadi. |
| **`autoread`** | Belgilangan kanallar, guruhlar yoki botlarni avtomatik o'qilgan qiladi (`.autoread on/off`, `.readall`). |
| **`basic`** | `.ping` (tezlikni o'lchash), `.alive` (holat tekshirish), `.id` (chat/user ID). |
| **`tools`** | `.del` (xabarni o'chirish), `.purge` (xabarlar tozalash), `.echo` (takrorlash). |
| **`statewatch`** | `data/state_<acc>.json` faylini har 5 soniyada kuzatadi — userbotni qayta ishga tushirmasdan sozlamalarni yangilaydi. |

---

## 👥 Ko'p akkauntli arxitektura (Multi-Account)

Loyiha bir vaqtning o'zida bir nechta akkauntlarda mustaqil sessiyalar bilan ishlashga mo'ljallangan:

| Slot | Akkaunt | Sessiya fayli | Systemd xizmati |
| :--- | :--- | :--- | :--- |
| **acc1** | `@Shamsiyevshamsiddin` | `sessions/acc1.session` | `userbot@acc1.service` |
| **acc2** | `@shamsiyev_shamsiddin` | `sessions/acc2.session` | `userbot@acc2.service` |
| **acc3** | `@scarpiont` | `sessions/acc3.session` | `userbot@acc3.service` |

---

## 🛡️ Ban va xavfsizlik choralari

- **Insondek yozish simulyatsiyasi:** Xabar yuborishdan oldin 2–5 soniyalik tabiiy "typing..." holati.
- **Cheklovlar:** Har bir chat va barcha chatlar bo'yicha global limitlar (`GLOBAL_MAX=15/60s`).
- **Ish vaqti:** `ACTIVE_HOURS=8-24`, `TZ_OFFSET=5` bo'yicha tungi vaqtda himoya.
- **Loop breaker:** Botlar o'rtasida cheksiz aylanib qolmaslik uchun xabarlar chegarasi (20 xabar / 10 daqiqa).

---

## 🖥️ Web boshqaruv paneli

- **Fayl:** `webpanel.py` (Aiohttp asosida, port `8123`)
- **Tizim xizmati:** `userbot-panel.service`
- Har bir akkaunt holatini ko'rish, plaginlarni yoqish/o'chirish va loglarni kuzatish imkoniyati.
- Chat ichidan `.bot` buyrug'i panelga havolani qaytaradi.

---

## 🚀 Ishga tushirish va boshqaruv

### Lokal muhitda:
```bash
cd telegram-userbot
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env     # API_ID va API_HASH ni kiriting
python3 userbot.py acc1  # acc1, acc2 yoki acc3
```

### Serverda boshqaruv (Hetzner CX23):
```bash
# Xizmat holatini tekshirish
systemctl status userbot@acc1

# Qayta ishga tushirish
systemctl restart userbot@acc1

# Jonli loglarni kuzatish
journalctl -u userbot@acc1 -f

# Web panel xizmati
systemctl restart userbot-panel
```

---

## 🔗 Aloqador manbalar

- Mustaqil repozitoriy: [github.com/shamsiyevshamsiddin19/userbot](https://github.com/shamsiyevshamsiddin19/userbot)
- Server joylashuvi: Hetzner CX23 `/opt/telegram-userbot`
