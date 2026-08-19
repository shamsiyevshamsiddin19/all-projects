# 🐍 Python Terminal va Muhit Buyruqlari (Linux)

> Unitib qo'yganingizda shu yerdan qarang. `Ctrl + F` bosib tezda qidiring.
> Barcha buyruqlar Ubuntu, Debian, Oracle Linux, CentOS, Fedora va Arch Linux muhitlari uchun to'liq moslashtirilgan.

---

## ✅ Python o'rnatilganini tekshirish

```bash
python3 --version                # Python 3 versiyasini ko'rish (masalan: Python 3.11.2)
python3 -V                       # Qisqartma (xuddi shu)
pip3 --version                   # pip paketlar menejeri versiyasi
which python3                    # Python qayerda joylashgan (masalan: /usr/bin/python3)
which pip3                       # pip qayerda joylashgan (masalan: /usr/bin/pip3)
```

> 💡 *Linux distributivlarida odatda `python` emas, `python3` buyrug'i ishlatiladi.*

---

## 📦 Virtual muhit (venv)

### Nima uchun kerak?
Har bir Python loyihasi uchun alohida, izolyatsiyalangan kutubxonalar to'plamini yaratish uchun. Natijada loyihalar kutubxona versiyalari bilan bir-biriga xalaqit bermaydi va tizim paketlariga zarar yetkazmaydi.

### 1. Linux'da venv modulini o'rnatish (agar o'rnatilmagan bo'lsa):
```bash
# Ubuntu / Debian da:
sudo apt update
sudo apt install python3-venv python3-pip

# Oracle Linux / RHEL / CentOS da:
sudo dnf install python3-pip
```

### 2. Virtual muhit yaratish:
```bash
python3 -m venv .venv            # ".venv" nomli yashirin virtual muhit yaratish (Tavsiya etiladi)
python3 -m venv venv             # "venv" nomli virtual muhit
python3 -m venv env              # "env" nomli
```

### 3. Faollashtirish (Activate):
```bash
source .venv/bin/activate        # .venv ni faollashtirish (Bash / Zsh da)
# yoki
source venv/bin/activate
```

Faollashganda terminal boshida `(.venv)` yozuvi paydo bo'ladi:
```bash
(.venv) opc@server:~/loyiha$
```

### 4. Chiqish (Deactivate):
```bash
deactivate                       # Virtual muhitdan chiqish
```

### 5. O'chirish (Delete):
```bash
rm -rf .venv                     # Virtual muhit papkasini to'liq o'chirish
```

---

## 📥 Kutubxona o'rnatish va boshqarish (pip)

### O'rnatish:
```bash
pip install requests             # Bitta kutubxona o'rnatish
pip install fastapi uvicorn      # Bir vaqtda bir nechta
pip install requests==2.31.0     # Muayyan aniq versiyani o'rnatish
pip install "requests>=2.28"     # Minimal versiya chegarasi bilan
pip install "requests>=2.28,<3"  # Versiya oralig'i bilan
pip install -U requests          # Kutubxonani eng so'nggi versiyaga yangilash
pip install -U pip               # pip ning o'zini yangilash
```

### O'chirish:
```bash
pip uninstall requests           # O'chirish (tasdiqlash so'raydi)
pip uninstall -y requests        # Savolsiz to'g'ridan-to'g'ri o'chirish
pip uninstall -y -r requirements.txt # Fayldagi barcha kutubxonalarni o'chirish
```

### Ro'yxat ko'rish va ma'lumot olish:
```bash
pip list                         # O'rnatilgan barcha kutubxonalar ro'yxati
pip list --outdated              # Yangilanishi mumkin bo'lgan eskirgan kutubxonalar
pip show requests                # Kutubxona haqida to'liq ma'lumot (versiya, litsenziya, muallif)
pip show -f requests             # Kutubxonaning barcha o'rnatilgan fayllari ro'yxati
pip check                        # Kutubxonalar o'rtasidagi ziddiyat va moslikni tekshirish
```

---

## 📋 requirements.txt bilan ishlash

### 1. Faylni yaratish (Eksport):
```bash
pip freeze > requirements.txt    # O'rnatilgan barcha kutubxonalarni faylga saqlash
```

`requirements.txt` namunasi:
```txt
fastapi==0.110.0
uvicorn==0.28.0
sqlalchemy==2.0.28
psycopg2-binary==2.9.9
pydantic==2.6.4
```

### 2. Fayldan o'rnatish (Import):
```bash
pip install -r requirements.txt  # Yangi server yoki muhitda barchasini 1 ta buyruq bilan o'rnatish
pip install -r requirements.txt --upgrade # Barchasini yangilab o'rnatish
```

---

## ▶️ Python faylni ishga tushirish (Linux)

```bash
python3 main.py                  # Python faylni ishga tushirish
python3 src/app.py               # Ichki papkadagi faylni ishga tushirish
python3 -m app.main              # Modul sifatida ishga tushirish (import xatolarini oldini oladi)

# Mini Web Server ishga tushirish (Test va fayl ulashish uchun):
python3 -m http.server 8000      # 8000 portda statik veb-server yoqish
python3 -m http.server 3000 --bind 127.0.0.1 # Faqat localhost uchun
```

---

## 🚀 Serverda Python xizmatlarini orqa fonda ishlatish

### 1. Nohup bilan (Oddiy orqa fon):
```bash
nohup python3 bot.py > bot.log 2>&1 & # Terminal yopilsa ham bot fonda ishlayveradi
ps aux | grep "bot.py"                # Ishlayotganini tekshirish
tail -f bot.log                       # Loglarni jonli kuzatish
```

### 2. Uvicorn va Gunicorn (Web API / FastAPI / Django):
```bash
# FastAPI ni Uvicorn bilan yoqish:
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Production rejimda Gunicorn + Uvicorn worker bilan:
gunicorn app.main:app -k uvicorn.workers.UvicornWorker --workers 2 --bind 127.0.0.1:8000
```

### 3. Systemd Service (Professional usul):
`/etc/systemd/system/mybot.service` fayli:
```ini
[Unit]
Description=My Telegram Bot
After=network.target

[Service]
User=opc
WorkingDirectory=/opt/mybot
ExecStart=/opt/mybot/.venv/bin/python main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload     # Yangi servisni tizimga tanitish
sudo systemctl start mybot       # Servisni yoqish
sudo systemctl enable mybot      # Server yonganda avtomatik yonishi uchun
sudo systemctl status mybot      # Holatini tekshirish
journalctl -u mybot -f           # Botning jonli loglarini ko'rish
```

---

## 💻 Python interaktiv rejim (REPL)

```bash
python3                          # Interaktiv rejimga kirish
>>> print("Salom Linux!")
>>> import sys; print(sys.platform) # 'linux'
>>> exit()                       # Chiqish
# yoki Ctrl + D                  # Chiqish (Linux klaviatura qisqartmasi)
```

### Bir qatorli tezkor buyruqlar (`-c`):
```bash
python3 -c "import os; print(os.uname())"
python3 -c "import torch; print('CUDA:', torch.cuda.is_available())" # GPU tekshirish
python3 -c "import secrets; print(secrets.token_hex(32))" # Xavfsiz Secret Key yaratish
```

---

## 📂 Linux'da yangi loyiha boshlash (Mukammal ketma-ketlik)

```bash
# 1. Loyiha papkasini yaratish va unga o'tish
mkdir -p ~/projects/my_project && cd ~/projects/my_project

# 2. Virtual muhit yaratish
python3 -m venv .venv

# 3. Virtual muhitni yoqish
source .venv/bin/activate

# 4. pip ni yangilash va kerakli kutubxonalarni o'rnatish
pip install -U pip setuptools wheel
pip install fastapi uvicorn python-dotenv

# 5. requirements.txt saqlash
pip freeze > requirements.txt

# 6. Boshlang'ich faylni yaratish
cat << 'EOF' > main.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "success", "msg": "Salom Dunyo!"}
EOF

# 7. Ishga tushirish
uvicorn main:app --reload
```

---

## 🛠️ Linux'da ko'p uchraydigan muammolar va yechimlar

### 1. `externally-managed-environment` xatosi (Ubuntu 23+, Debian 12+)
*Sabab:* Yangi Linux tizimlari global `pip install` ga ruxsat bermaydi.
*Yechim:* Har doim virtual muhit (`python3 -m venv .venv`) yarating va `source .venv/bin/activate` orqali o'rnating.

### 2. `python3-venv` topilmadi
```bash
sudo apt update && sudo apt install python3-venv python3-full
```

### 3. C-extensions / psycopg2 / pillow o'rnatishda `gcc` yoki `Python.h` xatosi
*Yechim:* Python dev headerlarini va kompilyatorni o'rnating:
```bash
# Ubuntu / Debian da:
sudo apt install build-essential python3-dev libpq-dev

# Oracle Linux / RHEL da:
sudo dnf groupinstall "Development Tools"
sudo dnf install python3-devel libpq-devel
```

### 4. Pip keshini tozalash:
```bash
pip cache purge
```

---

## 📝 TEZ JADVAL (Linux Python Cheat Sheet)

| Vazifa | Linux Terminal Buyrug'i |
|---|---|
| Python versiyasi | `python3 --version` |
| Python joyi | `which python3` |
| Virtual muhit yaratish | `python3 -m venv .venv` |
| Muhitni yoqish | `source .venv/bin/activate` |
| Muhitdan chiqish | `deactivate` |
| Muhitni o'chirish | `rm -rf .venv` |
| Paket o'rnatish | `pip install <paket>` |
| Paketni yangilash | `pip install -U <paket>` |
| Paketni o'chirish | `pip uninstall -y <paket>` |
| O'rnatilganlar ro'yxati | `pip list` |
| Paket haqida ma'lumot | `pip show <paket>` |
| requirements yaratish | `pip freeze > requirements.txt` |
| requirements o'rnatish | `pip install -r requirements.txt` |
| Skriptni ishga tushirish | `python3 app.py` |
| Orqa fonda ishlatish | `nohup python3 app.py > app.log 2>&1 &` |
| REPL interaktiv rejim | `python3` |
| REPL dan chiqish | `exit()` yoki `Ctrl + D` |

---

*🔍 Qidirish uchun: `Ctrl + F` bosib kerakli terminni yozing.*
