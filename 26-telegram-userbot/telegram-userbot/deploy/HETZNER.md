# Hetzner serverga o'rnatish (3 ta akkaunt)

Har bir akkaunt alohida jarayon bo'lib ishlaydi: `acc1`, `acc2`, `acc3`.
Barchasi bitta `systemd` shabloni (`userbot@.service`) orqali boshqariladi.

---

## 0. Server tayyorlash (Ubuntu 22.04/24.04)
Serverga SSH orqali `root` bilan kiring:

```bash
apt update && apt install -y python3 python3-venv python3-pip git
# Xavfsizlik uchun alohida foydalanuvchi
useradd -m -s /bin/bash userbot
```

## 1. Kodni serverga yuklash
Loyihani `/opt/telegram-userbot` ga qo'ying. Ikki yo'l:

**A) Git orqali (tavsiya):** avval GitHub'ga yuklang, keyin:
```bash
git clone <sizning-repo-url> /opt/telegram-userbot
```

**B) SCP orqali** (o'z kompyuteringizdan, `.env` va `sessions/` ni yubormang):
```bash
scp -r E:\telegram-userbot root@SERVER_IP:/opt/telegram-userbot
```

Egaligini o'zgartiring:
```bash
chown -R userbot:userbot /opt/telegram-userbot
```

## 2. Virtual muhit va kutubxonalar
```bash
cd /opt/telegram-userbot
sudo -u userbot python3 -m venv venv
sudo -u userbot venv/bin/pip install -r requirements.txt
```

## 3. .env faylini yaratish
```bash
sudo -u userbot cp .env.example .env
sudo -u userbot nano .env
```
Ichiga API_ID, API_HASH va GEMINI_API_KEY ni yozing.
> 3 ta akkaunt bitta `API_ID`/`API_HASH` bilan ishlashi mumkin. Xavfsizroq
> bo'lishi uchun har biriga alohida kalit ham berish mumkin (pastda "Alohida
> kalit" bo'limiga qarang).

## 4. Har bir akkauntga kirish (bir martalik)
Session fayli yaratish uchun har bir akkauntga bir marta login qilinadi.
Bu telefon raqami + Telegram kodi so'raydi:

```bash
sudo -u userbot venv/bin/python userbot.py acc1
# telefon + kod kiriting, "ishga tushdi" chiqqach Ctrl+C bosing
sudo -u userbot venv/bin/python userbot.py acc2
sudo -u userbot venv/bin/python userbot.py acc3
```
Har biri `sessions/acc1.session`, `sessions/acc2.session`, `sessions/acc3.session`
fayllarini yaratadi.

## 5. systemd xizmatlarini o'rnatish
```bash
cp /opt/telegram-userbot/deploy/userbot@.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now userbot@acc1 userbot@acc2 userbot@acc3
```

## 6. Boshqarish
```bash
systemctl status userbot@acc1          # holati
journalctl -u userbot@acc1 -f          # jonli log
systemctl restart userbot@acc2         # qayta ishga tushirish
systemctl stop userbot@acc3            # to'xtatish
```

Server qayta yuklansa ham 3 akkaunt avtomatik ishga tushadi (`enable` tufayli).

---

## Alohida API kalit (ixtiyoriy, xavfsizroq)
`.env` da akkaunt nomini katta harf bilan qo'shib yozing:
```
API_ID_ACC1=111
API_HASH_ACC1=aaa
API_ID_ACC2=222
API_HASH_ACC2=bbb
API_ID_ACC3=333
API_HASH_ACC3=ccc
```
Kod avtomatik shu akkauntga mos kalitni tanlaydi, topmasa umumiy `API_ID`/`API_HASH` ga qaytadi.

## Muhim eslatmalar
- `.env` va `sessions/` — **maxfiy**. Ularni GitHub'ga yuklamang (`.gitignore` da bor).
- Bir IP'da 3 akkaunt: Telegram odatda ruxsat beradi, lekin spam/flood qilmang —
  aks holda akkaunt bloklanishi mumkin.
- Login kodini SSH terminalда o'zingiz kiritasiz — buni avtomatlashtirib bo'lmaydi.
