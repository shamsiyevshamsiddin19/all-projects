# -*- coding: utf-8 -*-
"""
Linux darsligi (7 ta bo'lim, 20 ta dars + mundarija) generatori.
"""
import os
import sys

BASE_DIR = os.getenv('LINUX_BASE_DIR', '/home/shamsiddin/Documents/shamsiyev/Dasturlash/Linux-Darslik')

CHAPTERS = [
    {
        "dir": "00-bob-kirish",
        "title": "00. Kirish va Linux Asoslari",
        "lessons": [
            {
                "fn": "0.1-linux-nima-tarixi-distributivlar.md",
                "name": "0.1. Linux nima, tarixi va distributivlar (Ubuntu, Debian, CentOS)",
                "content": """# 0.1. Linux nima, tarixi va distributivlar

## Bu darsda nimalarni o'rganasiz
- Linux operatsion tizimi nima va u qanday yaratilgan
- Linux yadrosi (Kernel) va OS farqi
- Mashhur Linux distributivlari (Ubuntu, Debian, CentOS, Rocky Linux, Arch)
- Nega dasturchilar va serverlar uchun Linux muhim

## 1. Nazariy qism
Linux — 1991-yilda Linus Torvalds tomonidan asos solingan erkin va ochiq kodli operatsion tizim yadrosi (kernel) hisoblanadi. Bugungi kunda dunyodagi deyarli barcha serverlar (96%+), bulutli platformalar (AWS, GCP, DigitalOcean), superkompyuterlar va Android qurilmalari aynan Linux asosida ishlaydi.

### Asosiy distributivlar (Distros):
1. **Debian oilasi:** Debian, Ubuntu, Linux Mint. Paket menejeri: `apt`. Eng ommabop va qulay tizim.
2. **Red Hat oilasi:** RHEL, CentOS, Rocky Linux, Fedora. Paket menejeri: `dnf` / `yum`. Korporativ serverlarda keng qo'llaniladi.
3. **Arch oilasi:** Arch Linux, Manjaro. Paket menejeri: `pacman`. Doimiy yangilanish (rolling release) rejimida ishlaydi.

## 2. Amaliy misol
Tizim haqidagi ma'lumotlarni ko'rish buyruqlari:

```bash
# Tizim yadrosi va arxitekturasi
uname -a

# O'rnatilgan distributiv ma'lumotlari
cat /etc/os-release

# Tizim nomi va arxitektura
hostnamectl
```

## 3. Keng tarqalgan xatolar
- ❌ **Xato:** Linux va Ubuntuni butunlay boshqa narsa deb o'ylash.
  - ✅ **Tushuntirish:** Linux bu yadro, Ubuntu esa uning asosiga qurilgan to'liq operatsion tizim (distributiv).

## 4. Mashq/Topshiriq
1. O'z kompyuteringiz yoki serveringizda `uname -r` buyrug'ini ishga tushiring va kernel versiyasini aniqlang.
2. `cat /etc/os-release` orqali OS nomi va versiyasini ko'ring.

## 5. Qisqacha xulosa
Linux serverlar va dasturlash dunyosining asosi hisoblanadi. Ubuntu kabi Debian asosidagi tizimlar yangi boshlovchilar va veb-ishlanmalar uchun eng qulay tanlovdir.
"""
            },
            {
                "fn": "0.2-terminal-va-shell-bash-zsh.md",
                "name": "0.2. Terminal va Shell tushunchasi (Bash, Zsh, buyruqlar tuzilishi)",
                "content": """# 0.2. Terminal va Shell tushunchasi

## Bu darsda nimalarni o'rganasiz
- Terminal, Konsol va Shell (Qobiq) o'rtasidagi farq
- Mashhur Shell turlari: Bash, Zsh, Sh
- Buyruqlar sintaksisi: Buyruq, Bayroqlar (Flags/Options) va Argumentlar
- Foydali tezkor tugmalar (Shortcuts)

## 1. Nazariy qism
- **Terminal Emulator:** Foydalanuvchi matn kiritadigan va natijani ko'radigan grafik oyna (masalan, GNOME Terminal, iTerm2, Alacritty).
- **Shell:** Kiritilgan buyruqlarni o'qib, operatsion tizim yadrosiga yetkazuvchi buyruqlar interpretatori (masalan, Bash, Zsh).

### Buyruq sintaksisi:
```bash
buyruq [bayroqlar] [argumentlar]
# Misol:
ls -la /var/log
```
- `ls` — buyruq
- `-l` va `-a` (`-la`) — bayroqlar (uzun ro'yxat va yashirin fayllar)
- `/var/log` — argument (yo'l)

## 2. Asosiy tezkor tugmalar (Hotkeys)
- `Ctrl + C` — Ishlayotgan buyruqni to'xtatish (Cancel/Kill)
- `Ctrl + L` — Ekranni tozalash (`clear` bilan bir xil)
- `Ctrl + R` — Tarixdan buyruqlarni qidirish (Reverse search)
- `Tab` — Buyruq yoki fayl nomini avtomatik to'ldirish (Auto-complete)
- `Ctrl + A` / `Ctrl + E` — Kursorni qator boshiga / oxiriga o'tkazish

## 3. Mashq/Topshiriq
1. Qaysi shell ishlatilayotganini aniqlang: `echo $SHELL`
2. `history` buyrug'i orqali oxirgi kiritilgan buyruqlarni ko'ring.

## 4. Qisqacha xulosa
Terminal bilan tez ishlash `Tab` va `Ctrl+R` kabi qisqa tugmalarni o'zlashtirishdan boshlanadi.
"""
            }
        ]
    },
    {
        "dir": "01-bob-fayl-tizimi",
        "title": "01. Fayl Tizimi va Asosiy Buyruqlar",
        "lessons": [
            {
                "fn": "1.1-fayl-daraxti-tuzilishi.md",
                "name": "1.1. Linux fayl daraxti tuzilishi (/root, /home, /etc, /var, /opt)",
                "content": """# 1.1. Linux fayl daraxti tuzilishi

## Bu darsda nimalarni o'rganasiz
- Linux fayl tizimi iyerarxiyasi (FHS — Filesystem Hierarchy Standard)
- Windows disklar (C:, D:) va Linux yagona ildiz (`/`) farqi
- Muhim tizim papkalarining vazifalari

## 1. Nazariy qism
Linuxda hamma narsa yagona ildiz papkasi — **`/`** (root) dan boshlanadi.

### Asosiy papkalar:
- **`/`** — Barcha papkalarning asosi (Ildiz).
- **`/home`** — Oddiy foydalanuvchilarning shaxsiy papkalari (`/home/shamsiddin`).
- **`/root`** — Superadmin (root) foydalanuvchisining shaxsiy uyi.
- **`/etc`** — Tizim va dasturlarning barcha konfiguratsiya fayllari (`nginx.conf`, `hosts`).
- **`/var`** — O'zgaruvchan ma'lumotlar: loglar (`/var/log`), veb-fayllar (`/var/www`).
- **`/opt`** — Qo'shimcha uchinchi tomon dasturlari va loyihalar.
- **`/tmp`** — Vaqtinchalik fayllar (qayta yuklanganda o'chadi).
- **`/bin` va `/usr/bin`** — Bajariluvchi dasturlar va buyruqlar.

## 2. Amaliy misol
```bash
# Ildizdagi papkalarni ko'rish
ls -l /

# Joriy foydalanuvchi uyiga o'tish
cd ~
pwd
```

## 3. Xulosa
Linuxda disk tushunchasi yo'q, barcha xotira qurilmalari va bo'limlar yagona daraxtga ulanadi (mount qilinadi).
"""
            },
            {
                "fn": "1.2-navigatsiya-va-fayllarni-korish.md",
                "name": "1.2. Navigatsiya va fayllarni ko'rish (pwd, ls, cd, cat, less, head, tail)",
                "content": """# 1.2. Navigatsiya va fayllarni ko'rish

## Bu darsda nimalarni o'rganasiz
- Papkalar bo'ylab harakatlanish (`pwd`, `cd`, `ls`)
- Matnli fayllarni o'qish (`cat`, `less`, `more`)
- Loglar va fayllarning boshi/oxirini ko'rish (`head`, `tail`, `tail -f`)

## 1. Asosiy Navigatsiya Buyruqlari
```bash
# Qayerda turganingizni ko'rsatadi (Print Working Directory)
pwd

# Fayl va papkalar ro'yxati (yashirin va o'lchamlari bilan)
ls -lah

# Papkaga kirish
cd /var/log

# Bir daraja yuqoriga chiqish
cd ..

# Uy papkaga qaytish
cd ~
```

## 2. Fayllarni Ko'rish
```bash
# Fayl tarkibini to'liq chiqarish
cat /etc/hostname

# Katta fayllarni sahifama-sahifa o'qish (Chiqish uchun 'q')
less /var/log/syslog

# Faylning birinchi 10 qatori
head -n 10 /etc/passwd

# Faylning oxirgi 20 qatori
tail -n 20 /var/log/nginx/error.log

# Loglarni jonli kuzatish (Real-time monitoring)
tail -f /var/log/nginx/access.log
```

## 3. Mashq/Topshiriq
1. `/etc/os-release` faylining faqat dastlabki 3 qatorini chiqaring.
2. `tail -f` orqali tizim loglarini jonli kuzatib ko'ring.
"""
            },
            {
                "fn": "1.3-fayl-va-papkalarni-boshqarish.md",
                "name": "1.3. Fayl va papkalarni boshqarish (mkdir, touch, cp, mv, rm)",
                "content": """# 1.3. Fayl va papkalarni boshqarish

## Bu darsda nimalarni o'rganasiz
- Papka va fayllar yaratish (`mkdir`, `touch`)
- Nusxalash va ko'chirish (`cp`, `mv`)
- Xavfsiz o'chirish (`rm`, `rmdir`)

## 1. Yaratish
```bash
# Bo'sh fayl yaratish
touch main.py

# Yangi papka yaratish
mkdir loyiha

# Ichma-ich papkalar yaratish (-p bayrog'i)
mkdir -p app/backend/api
```

## 2. Nusxalash va Ko'chirish
```bash
# Fayldan nusxa olish
cp config.env config.env.backup

# Butun papkani nusxalash (-r rekursiv)
cp -r app app_backup

# Fayl yoki papkani ko'chirish / nomini o'zgartirish
mv main.py app/main.py
mv eski_nom.txt yangi_nom.txt
```

## 3. O'chirish
```bash
# Bo'sh faylni o'chirish
rm test.txt

# Papkani barcha ichidagi fayllari bilan majburiy o'chirish (Ehtiyot bo'ling!)
rm -rf app_backup
```

> [!CAUTION]
> `rm -rf /` yoki `rm -rf *` kabi buyruqlarni hech qachon ehtiyotsizlik bilan ishlatmang, Linuxda o'chirilgan fayllar korzinkaga tushmaydi, darhol yo'qoladi!
"""
            },
            {
                "fn": "1.4-qidiruv-buyruqlari-find-grep.md",
                "name": "1.4. Qidiruv buyruqlari (find, grep, which, locate)",
                "content": """# 1.4. Qidiruv buyruqlari (find, grep, which)

## Bu darsda nimalarni o'rganasiz
- Fayllarni nomi, o'lchami va sanasi bo'yicha topish (`find`)
- Fayl ichidagi matnlarni qidirish (`grep`)
- Dastur qayerda joylashganini aniqlash (`which`, `whereis`)

## 1. Fayllarni qidirish (`find`)
```bash
# Joriy papkadan .py fayllarni qidirish
find . -name "*.py"

# /var papkasidan 50MB dan katta fayllarni topish
find /var -size +50M

# Oxirgi 24 soatda o'zgargan fayllarni topish
find /home -mtime -1
```

## 2. Matn ichidan qidirish (`grep`)
```bash
# Fayl ichidan qator qidirish (registrga qaramasdan -i)
grep -i "error" /var/log/nginx/error.log

# Butun papka ichidan rekursiv qidirish (-rn: qator raqamlari bilan)
grep -rn "DATABASE_URL" /opt/loyiha/

# Boshqa buyruq natijasidan qidirish (Pipe | bilan)
ps aux | grep python
```

## 3. Dastur joylashuvini topish
```bash
which python3
which nginx
```
"""
            }
        ]
    },
    {
        "dir": "02-bob-ruxsatlar",
        "title": "02. Foydalanuvchilar va Ruxsatlar (Permissions)",
        "lessons": [
            {
                "fn": "2.1-foydalanuvchilar-va-guruhlar.md",
                "name": "2.1. Foydalanuvchi va guruhlar boshqaruvi (useradd, usermod, sudo)",
                "content": """# 2.1. Foydalanuvchi va guruhlar boshqaruvi

## Bu darsda nimalarni o'rganasiz
- Linux ko'p foydalanuvchili tizimi
- Yangi foydalanuvchi qo'shish va parolini sozlash
- Superadmin (sudo) huquqini berish
- Guruhlar (groups) bilan ishlash

## 1. Foydalanuvchi yaratish
```bash
# Yangi foydalanuvchi yaratish (uy papkasi bilan)
sudo adduser devuser
# yoki: sudo useradd -m -s /bin/bash devuser

# Parol o'rnatish yoki o'zgartirish
sudo passwd devuser
```

## 2. Guruhlar va Sudo huquqi
```bash
# Foydalanuvchini sudo guruhiga qo'shish
sudo usermod -aG sudo devuser   # Ubuntu/Debian
sudo usermod -aG wheel devuser  # CentOS/RHEL

# Foydalanuvchining guruhlarini ko'rish
groups devuser

# Foydalanuvchini o'chirish (uy papkasi bilan birga)
sudo userdel -r devuser
```
"""
            },
            {
                "fn": "2.2-fayl-ruxsatlari-chmod-chown.md",
                "name": "2.2. Fayl ruxsatlari va egalik (chmod, chown, chgrp, 755, 644)",
                "content": """# 2.2. Fayl ruxsatlari va egalik (chmod, chown)

## Bu darsda nimalarni o'rganasiz
- Ruxsat turlari: Read (r=4), Write (w=2), Execute (x=1)
- Foydalanuvchi toifalari: Owner (u), Group (g), Others (o)
- `chmod` orqali ruxsatlarni raqamli va belgili o'zgartirish
- `chown` orqali fayl egasini o'zgartirish

## 1. Ruxsatlarni tushunish
`ls -l` buyrug'i natijasi:
`-rwxr-xr-- 1 shamsiddin developers 4096 script.sh`
- `-` — oddiy fayl (`d` bo'lsa papka)
- `rwx` (7) — Egasi (Owner): o'qish, yozish, ishga tushirish
- `r-x` (5) — Guruh (Group): o'qish, ishga tushirish
- `r--` (4) — Boshqalar (Others): faqat o'qish

## 2. `chmod` bilan ruxsat berish
```bash
# Skriptga ishga tushirish huquqini berish
chmod +x deploy.sh

# Standart fayl ruxsati (Egasi o'qiydi/yozadi, boshqalar faqat o'qiydi)
chmod 644 index.html

# Standart papka va skript ruxsati
chmod 755 /var/www/myweb
```

## 3. `chown` bilan egasini o'zgartirish
```bash
# Fayl egasini www-data ga o'zgartirish
sudo chown www-data /var/www/html/index.php

# Papka va ichidagi barcha fayllar egasi va guruhini o'zgartirish (-R)
sudo chown -R www-data:www-data /var/www/html/
```
"""
            }
        ]
    },
    {
        "dir": "03-bob-jarayonlar-monitoring",
        "title": "03. Jarayonlar va Monitoring",
        "lessons": [
            {
                "fn": "3.1-jarayonlarni-boshqarish-ps-top-kill.md",
                "name": "3.1. Jarayonlarni ko'rish va to'xtatish (ps, top, htop, kill, pkill)",
                "content": """# 3.1. Jarayonlarni ko'rish va boshqarish

## Bu darsda nimalarni o'rganasiz
- Process ID (PID) tushunchasi
- Ishlayotgan dasturlarni kuzatish (`ps`, `top`, `htop`)
- Jarayonlarni to'xtatish (`kill`, `pkill`, `killall`)

## 1. Jarayonlarni ko'rish
```bash
# Barcha faol jarayonlar to'liq ro'yxati
ps aux

# Muayyan dasturni topish
ps aux | grep gunicorn

# Interaktiv monitoring (Chiqish uchun 'q')
htop
# Agar o'rnatilmagan bo'lsa: sudo apt install htop
```

## 2. Jarayonni to'xtatish
```bash
# PID orqali xushmuomalalik bilan to'xtatish (SIGTERM)
kill 1234

# Majburiy o'ldirish (SIGKILL -9)
kill -9 1234

# Nomi bo'yicha barcha jarayonlarni to'xtatish
pkill -f gunicorn
killall nginx
```
"""
            },
            {
                "fn": "3.2-resurslar-monitoringi-df-du-free-uptime.md",
                "name": "3.2. Resurslar monitoringi (df, du, free, uptime)",
                "content": """# 3.2. Tizim resurslari va xotira monitoringi

## Bu darsda nimalarni o'rganasiz
- Tezkor xotira (RAM) holatini ko'rish (`free`)
- Qattiq disk to'lishini tekshirish (`df`, `du`)
- Tizim qancha vaqtdan beri ishlayotgani (`uptime`)

## 1. RAM va Disk
```bash
# Operativ xotirani megabayt/gigabaytlarda ko'rish (-m yoki -h)
free -h

# Disk bo'limlari to'lish foizini ko'rish (-h: human-readable)
df -h

# Joriy papka yoki fayllar hajmini aniqlash
du -sh *

# Eng ko'p joy olgan 5 ta papkani topish
du -sh /var/* | sort -hr | head -n 5
```

## 2. Server yuki
```bash
# Server ish vaqti va Load Average
uptime
```
"""
            }
        ]
    },
    {
        "dir": "04-bob-paketlar",
        "title": "04. Paketlar va Dasturlar Boshqaruvi",
        "lessons": [
            {
                "fn": "4.1-apt-va-paketlar-ornatish.md",
                "name": "4.1. APT va DPKG (Ubuntu/Debian) bilan paketlar o'rnatish",
                "content": """# 4.1. APT paket menejeri bilan ishlash

## Bu darsda nimalarni o'rganasiz
- Repozitoriyalar tushunchasi
- Paketlar ro'yxatini yangilash va dasturlarni yangilash
- Dasturlarni o'rnatish va to'liq tozalash

## 1. Asosiy APT Buyruqlari
```bash
# 1. Repozitoriya indekslarini yangilash (yangi versiyalar ro'yxati)
sudo apt update

# 2. O'rnatilgan barcha dasturlarni yangi versiyaga ko'tarish
sudo apt upgrade -y

# 3. Yangi dastur o'rnatish
sudo apt install nginx git curl ufw -y

# 4. Dasturni o'chirish
sudo apt remove nginx

# 5. Dastur va uning barcha konfiguratsiyalarini to'liq o'chirish
sudo apt purge nginx -y

# 6. Keraksiz qolgan qaramliklarni tozalash
sudo apt autoremove -y
```
"""
            },
            {
                "fn": "4.2-arxivlar-va-yuklab-olish-curl-wget-tar.md",
                "name": "4.2. Fayllarni yuklash va arxivlar (curl, wget, tar, zip)",
                "content": """# 4.2. Yuklab olish va arxivlar bilan ishlash

## Bu darsda nimalarni o'rganasiz
- Internetdan fayl yuklash (`curl`, `wget`)
- `.tar.gz`, `.zip` arxivlarini ochish va yaratish

## 1. Fayllarni yuklab olish
```bash
# Faylni to'g'ridan-to'g'ri yuklab olish
wget https://example.com/file.zip

# URL orqali faylni saqlash (-o yoki -O)
curl -O https://example.com/data.tar.gz

# API ga so'rov yuborish
curl -s https://api.ipify.org
```

## 2. Arxivlar bilan ishlash
```bash
# .tar.gz arxivini ochish (eXtract, Verbose, gZip, File)
tar -xzvf archive.tar.gz

# Yangi .tar.gz arxivi yaratish (Create)
tar -czvf loyiha_backup.tar.gz /opt/loyiha/

# .zip arxivini ochish
unzip archive.zip

# .zip arxiv yaratish
zip -r loyiha.zip app/
```
"""
            }
        ]
    },
    {
        "dir": "05-bob-systemd-cron",
        "title": "05. Xizmatlar (Systemd) va Avtomatlashtirish (Cron)",
        "lessons": [
            {
                "fn": "5.1-systemd-va-systemctl-servislar.md",
                "name": "5.1. Systemd va systemctl (Servislarni boshqarish va yaratish)",
                "content": """# 5.1. Systemd va systemctl boshqaruvi

## Bu darsda nimalarni o'rganasiz
- Systemd nima va servislar qanday ishlaydi
- `systemctl` orqali xizmatlarni boshqarish (start, stop, restart, status)
- Python / Django / Bot uchun o'z `.service` faylini yozish

## 1. Asosiy Servis Buyruqlari
```bash
# Servis holatini tekshirish
sudo systemctl status nginx

# Servisni ishga tushirish, to'xtatish va qayta yuklash
sudo systemctl start nginx
sudo systemctl stop nginx
sudo systemctl restart nginx

# Server yoqilganda avtomatik ishga tushishini yoqish (Autostart)
sudo systemctl enable nginx
sudo systemctl disable nginx
```

## 2. Shaxsiy `.service` fayl yaratish
Fayl: `/etc/systemd/system/mybot.service`
```ini
[Unit]
Description=Telegram Bot Service
After=network.target

[Service]
User=shamsiddin
WorkingDirectory=/opt/mybot
ExecStart=/opt/mybot/.venv/bin/python main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Faollashtirish:
```bash
sudo systemctl daemon-reload
sudo systemctl start mybot
sudo systemctl enable mybot
```
"""
            },
            {
                "fn": "5.2-journalctl-loglar-tahlili.md",
                "name": "5.2. Journalctl — tizim va servis loglarini tahlil qilish",
                "content": """# 5.2. Journalctl bilan loglarni o'qish

## Bu darsda nimalarni o'rganasiz
- `journalctl` orqali systemd servislarining loglarini ko'rish
- Xatoliklarni qidirish va real-vaqtda kuzatish

## 1. Asosiy buyruqlar
```bash
# Muayyan servisning loglarini jonli kuzatish (-u: unit, -f: follow)
sudo journalctl -u mybot.service -f

# Faqat oxirgi 50 ta qatorni ko'rish
sudo journalctl -u nginx -n 50

# Faqat bugungi loglarni ko'rish
sudo journalctl -u nginx --since today

# Xatolik darajasidagi (error/critical) loglar
sudo journalctl -u mybot -p err
```
"""
            },
            {
                "fn": "5.3-crontab-avtomatlashtirish.md",
                "name": "5.3. Crontab — Rejalashtirilgan vazifalar va avtomatlashtirish",
                "content": """# 5.3. Crontab bilan vazifalarni avtomatlashtirish

## Bu darsda nimalarni o'rganasiz
- Cron sintaksisi (5 ta yulduzcha: Daqiqa Soat Kun Oy Hafta_kuni)
- Zaxira nusxa olish yoki skriptlarni vaqt bo'yicha ishlatish

## 1. Cron sintaksisi
```
* * * * * /manzil/buyruq
│ │ │ │ │
│ │ │ │ └── Hafta kuni (0-7, 0 va 7 — Yakshanba)
│ │ │ └──── Oy (1-12)
│ │ └────── Oy kuni (1-31)
│ └──────── Soat (0-23)
└────────── Daqiqa (0-59)
```

## 2. Amaliy misollar
Crontabni tahrirlash:
```bash
crontab -e
```

Qo'shish:
```bash
# Har kuni tuni soat 03:00 da zaxira olish
0 3 * * * /home/shamsiddin/scripts/backup.sh >> /var/log/backup.log 2>&1

# Har 15 daqiqada bir marta ishga tushirish
*/15 * * * * /opt/app/.venv/bin/python /opt/app/cron_job.py

# Har dushanba ertalab soat 08:00 da
0 8 * * 1 /opt/report.sh
```

Ro'yxatni ko'rish: `crontab -l`
"""
            }
        ]
    },
    {
        "dir": "06-bob-tarmoq-ssh-xavfsizlik",
        "title": "06. Tarmoq (Networking), SSH va Xavfsizlik",
        "lessons": [
            {
                "fn": "6.1-tarmoq-buyruqlari-ping-netstat-ss.md",
                "name": "6.1. Tarmoq buyruqlari (ping, ss, ip, curl, dig)",
                "content": """# 6.1. Tarmoq diagnostikasi buyruqlari

## Bu darsda nimalarni o'rganasiz
- Server IP manzilini aniqlash (`ip a`)
- Bog'lanishni tekshirish (`ping`, `curl`)
- Ochiq portlar va tinglanayotgan servislarni ko'rish (`ss`, `netstat`)

## 1. Asosiy Tarmoq Buyruqlari
```bash
# Serverning barcha tarmoq interfeyslari va IP manzillari
ip a

# Sayt yoki server bilan aloqa bormi tekshirish
ping -c 4 google.com

# Ochiq tinglanayotgan (Listening) portlarni ko'rish (-t: tcp, -u: udp, -l: listen, -n: numeric, -p: process)
sudo ss -tulpn

# Domen DNS yozuvlarini tekshirish
dig google.com
nslookup google.com
```
"""
            },
            {
                "fn": "6.2-ssh-boshqaruvi-va-kalitlar.md",
                "name": "6.2. SSH server va kalitlar (ssh-keygen, ssh-copy-id, SCP)",
                "content": """# 6.2. SSH xavfsiz boshqaruvi

## Bu darsda nimalarni o'rganasiz
- SSH nima va u qanday ishlaydi (Port 22)
- Parolsiz SSH kalitlar yaratish (`ssh-keygen`, `ssh-copy-id`)
- Masofaviy server bilan fayl almashish (`scp`, `rsync`)

## 1. SSH kalit yaratish va yuklash
```bash
# Shaxsiy kompyuteringizda yangi Ed25519 kalit yaratish
ssh-keygen -t ed25519 -C "my-server-key"

# Ochiq kalitni (public key) serverga nusxalash
ssh-copy-id user@82.70.41.85

# Serverga ulanish
ssh user@82.70.41.85
```

## 2. SCP orqali fayl uzatish
```bash
# Lokal faylni serverga yuborish
scp my_file.txt user@server_ip:/opt/

# Serverdagi papkani lokal kompyuterga yuklab olish
scp -r user@server_ip:/var/log/nginx/ ./nginx_logs/
```
"""
            },
            {
                "fn": "6.3-xavfsizlik-va-ufw-firewall.md",
                "name": "6.3. Xavfsizlik va Firewall (UFW va eng yaxshi amaliyotlar)",
                "content": """# 6.3. Linux Server Xavfsizligi va UFW Firewall

## Bu darsda nimalarni o'rganasiz
- UFW (Uncomplicated Firewall) bilan portlarni boshqarish
- Faqat kerakli portlarni (SSH 22, HTTP 80, HTTPS 443) ochish
- Server xavfsizligining eng muhim qoidalari

## 1. UFW Firewall sozlash
```bash
# 1. Standart qoidalar: kiruvchilarni yopish, chiquvchilarga ruxsat
sudo ufw default deny incoming
sudo ufw default allow outgoing

# 2. MUHIM: Avval SSH portiga ruxsat bering (yo'qsa serverdan uzilib qolasiz!)
sudo ufw allow 22/tcp
# yoki: sudo ufw allow ssh

# 3. Veb-portlarni ochish
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 4. Firewallni yoqish va holatini ko'rish
sudo ufw enable
sudo ufw status verbose
```

## 2. Eng yaxshi xavfsizlik amaliyotlari
1. Root orqali to'g'ridan-to'g'ri SSH ga kirishni o'chiring (`PermitRootLogin no`).
2. Faqat SSH kalit bilan kirishga ruxsat bering (`PasswordAuthentication no`).
3. `fail2ban` o'rnatib, parolni ko'p xato tergan IP larni avtomatik bloklang.
4. Tizim xavfsizlik yangilanishlarini muntazam o'rnating (`sudo apt update && sudo apt upgrade`).
"""
            }
        ]
    }
]

def main():
    os.makedirs(BASE_DIR, exist_ok=True)
    print(f"Linux darsligi fayllarini yaratish boshlandi ({BASE_DIR})...")

    mundarija_lines = [
        "# Linux darsligi — Barcha mavzular (to'liq, 7 bo'lim, 20 dars)",
        "",
        "_Ushbu darslik noldan boshlab serverlarni professional boshqarish, fayl tizimi, ruxsatlar, jarayonlar, tarmoq, systemd servislar va xavfsizlikkacha bo'lgan barcha bilimlarni qamrab oladi._",
        "",
        "---",
        ""
    ]

    total_lessons = 0
    for chap in CHAPTERS:
        chap_dir = os.path.join(BASE_DIR, chap["dir"])
        os.makedirs(chap_dir, exist_ok=True)

        mundarija_lines.append(f"## {chap['title']}")
        mundarija_lines.append("")
        mundarija_lines.append("| № | Mavzu | Fayl |")
        mundarija_lines.append("|---|---|---|")

        for lesson in chap["lessons"]:
            total_lessons += 1
            file_path = os.path.join(chap_dir, lesson["fn"])
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(lesson["content"].strip() + "\n")
            
            p_num = lesson["name"].split('.')[0] + '.' + lesson["name"].split('.')[1] if '.' in lesson["name"] else str(total_lessons)
            clean_title = lesson["name"].split('. ', 1)[-1] if '. ' in lesson["name"] else lesson["name"]
            mundarija_lines.append(f"| {p_num} | {clean_title} | {lesson['fn']} |")
            print(f"  ✅ Yaratildi: {chap['dir']}/{lesson['fn']}")

        mundarija_lines.append("")

    mundarija_path = os.path.join(BASE_DIR, "00-linux-darslik-mundarija.md")
    with open(mundarija_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(mundarija_lines))

    print(f"\n🎉 Muvaffaqiyatli yakunlandi! Jami {total_lessons} ta Linux darsi va mundarija fayli yaratildi.")

if __name__ == '__main__':
    main()
