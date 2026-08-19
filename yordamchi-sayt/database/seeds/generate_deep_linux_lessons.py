# -*- coding: utf-8 -*-
"""
Ubuntu 24.04 LTS uchun to'liq mukammal Linux darsligi generatori (7 ta bob, 17 ta dars + mundarija).
Obsidian Vault va Darslik yaratish prompti standartlari asosida.
"""
import os
import sys

BASE_DIR = os.getenv('LINUX_BASE_DIR', '/home/shamsiddin/Documents/shamsiyev/Dasturlash/Linux-Darslik')

CHAPTERS = [
    {
        "dir": "00-bob-kirish",
        "title": "00. Kirish va Ubuntu 24.04 Asoslari",
        "lessons": [
            {
                "fn": "0.1-linux-nima-tarixi-arxitekturasi.md",
                "name": "0.1. Linux nima, tarixi va tizim arxitekturasi",
                "content": """# Linux nima, uning tarixi va tizim arxitekturasi

## Bu darsda nimalarni o'rganasiz

- Linux operatsion tizimining tarixi va Linus Torvalds hissasi
- Linux yadrosi (Kernel), Shell va Userspace (Foydalanuvchi qatlami) o'rtasidagi farq
- Linux nima sababdan serverlar, bulutli infratuzilmalar (Cloud) va superkompyuterlar standarti ekanligi
- Linux distributivlari oilalari (Debian/Ubuntu, RedHat/Rocky, Arch) va ularning vazifalari

## Nazariy qism

### 1. Muammo va Tarix — Linux qanday paydo bo'ldi?

1980-yillarda Unix operatsion tizimi mavjud edi, biroq u yopiq, qimmat va faqat yirik korporatsiyalar uchun mo'ljallangan edi. Richard Stallman 1983-yilda erkin dasturiy ta'minot harakati (GNU Project)ni boshladi, lekin tizimning eng muhim qismi — **yadro (kernel)** yetishmas edi.

1991-yilda Finlandiyalik 21 yoshli talaba **Linus Torvalds** o'zining shaxsiy kompyuteri uchun Unix-ga o'xshash erkin yadro yozdi va uni internetga ochiq e'lon qildi. Shu tariqa **GNU vositalari + Linux yadrosi = GNU/Linux** operatsion tizimi dunyoga keldi.

Bugungi kunda:
- Dunyodagi TOP-500 superkompyuterlarning **100%**i Linuxda ishlaydi.
- Internetdagi barcha veb-serverlar va ma'lumotlar bazalarining **96%+**i Linuxda ishlaydi.
- Android, Docker konteynerlari va sun'iy intellekt klasterlari Linux asosida qurilgan.

### 2. Linux Tizim Arxitekturasi

Linux qatlamli tuzilishga ega:

```
┌─────────────────────────────────────────────────────────┐
│ Foydalanuvchi Dasturlari (Browser, Python, Nginx, Bash) │ ◄── Userspace
├─────────────────────────────────────────────────────────┤
│ Tizim Kutubxonalari (glibc, POSIX API, System Calls)    │
├─────────────────────────────────────────────────────────┤
│ LINUX YADROSI (Kernel)                                   │
│  - Jarayonlar boshqaruvi (Process Scheduler)            │ ◄── Kernel Space
│  - Xotira boshqaruvi (Memory Management - RAM)          │
│  - Fayl tizimlari (ext4, btrfs, VFS)                    │
│  - Qurilmalar drayverlari (Device Drivers)              │
│  - Tarmoq steki (TCP/IP, Netfilter/Firewall)            │
├─────────────────────────────────────────────────────────┤
│ APPARATURA (CPU, RAM, SSD/HDD, Tarmoq kartasi)           │ ◄── Hardware
└─────────────────────────────────────────────────────────┘
```

- **Kernel (Yadro):** Dasturlar va apparat (Hardware) o'rtasidagi yagona ko'prik. U xotirani taqsimlaydi, CPU vaqtini boshqaradi va qurilmalar bilan xavfsiz aloqani ta'minlaydi.
- **System Calls (Tizim chaqiruvlari):** Dasturlarning yadro bilan muloqot qilish interfeysi (masalan, fayl ochish `open()`, xotira so'rash `malloc()`).
- **Userspace:** Biz ishlatadigan barcha utilitalar (`ls`, `grep`), matn muharrirlari va server dasturlari.

### 3. Asosiy Distributivlar Oilasi

| Oila | Asosiy vakillari | Paket menejeri | Ishlatilish sohasi |
|---|---|---|---|
| **Debian oilasi** | **Ubuntu (24.04 LTS)**, Debian, Linux Mint | `apt`, `dpkg` | Veb-serverlar, shaxsiy kompyuterlar, Cloud |
| **Red Hat oilasi** | RHEL, Rocky Linux, AlmaLinux, Fedora | `dnf`, `rpm` | Korporativ banklar, yirik korxonalar |
| **Arch oilasi** | Arch Linux, Manjaro | `pacman` | Doimiy yangilanish (Rolling release), ixlosmandlar |
| **SUSE oilasi** | openSUSE, SLES | `zypper`, `rpm` | Yevropa korporativ sektori |

## Amaliy misol

Ubuntu 24.04 LTS tizimingizda yadro va distributiv ma'lumotlarini tekshirish:

```bash
# 1. Yadro (Kernel) versiyasi va arxitekturani ko'rish
uname -a
# Chiqish misoli: Linux shamsiyev 6.8.0-40-generic x86_64 GNU/Linux

# 2. Ubuntu versiyasi tafsilotlarini o'qish
cat /etc/os-release

# 3. Tizimning umumiy xulosasi (hostname, kernel, arxitektura)
hostnamectl
```

## Keng tarqalgan xatolar

**Xato 1:** Linux va Ubuntuni alohida, mustaqil tizimlar deb o'ylash.
- ❌ "Men serverimga Linux emas, Ubuntu o'rnatdim".
- ✅ **Sabab:** Linux — bu yadro (dvigatel), Ubuntu esa Canonical kompaniyasi tomonidan shu yadro atrofida yig'ilgan to'liq operatsion tizimdir (avtomobil).

**Xato 2:** Dasturlarni to'g'ridan-to'g'ri apparatura bilan ishlaydi deb hisoblash.
- ❌ Dastur to'g'ridan-to'g'ri diskka yoki xotiraga yozadi deb o'ylash.
- ✅ **Sabab:** Xavfsizlik sababli barcha amallar Linux yadrosi (Kernel) ruxsati va nazorati ostida amalga oshiriladi.

## Mashq/topshiriq

1. **(Oson)** Terminalda `uname -r` buyrug'ini ishga tushiring va Ubuntu 24.04 kompyuteringiz qaysi Linux yadro versiyasida ishlayotganini aniqlang.
2. **(O'rtacha)** `cat /etc/os-release` faylini ochib, undagi `VERSION_ID` va `VERSION_CODENAME` qiymatlarini toping (Ubuntu 24.04 uchun `noble`).
3. **(Qiyin)** Linux arxitekturasi qatlamlarini (Userspace, System Calls, Kernel, Hardware) o'z so'zlaringiz bilan chizib, tushuntirib bering.

## Qisqacha xulosa

Linux — xavfsiz, ochiq kodli va barqaror operatsion tizim yadrosi bo'lib, zamonaviy axborot texnologiyalari infratuzilmasining tamal toshidir. Ubuntu 24.04 LTS esa ushbu yadroning eng so'nggi uzoq muddatli qo'llab-quvvatlanuvchi (Long Term Support) zamonaviy distributividir.

## Bog'liq

- Keyingi dars: [0.2. Ubuntu 24.04 LTS tizimi, Terminal va Shell asoslari](0.2-ubuntu-24-04-terminal-shell-asoslari.md)
"""
            },
            {
                "fn": "0.2-ubuntu-24-04-terminal-shell-asoslari.md",
                "name": "0.2. Ubuntu 24.04 LTS tizimi, Terminal va Shell (Bash/Zsh) asoslari",
                "content": """# Ubuntu 24.04 LTS tizimi, Terminal va Shell asoslari

## Bu darsda nimalarni o'rganasiz

- Terminal, Emulyator va Shell (Qobiq) o'rtasidagi farqni aniq bilib olasiz
- Bash va Zsh qobiqlarining imkoniyatlari hamda muhit o'zgaruvchilari (`$PATH`, `$HOME`, `$SHELL`)
- Buyruqlar sintaksisi: Buyruq (Command), Bayroqlar (Options/Flags) va Argumentlar
- Terminalda ishlashni 10 barobar tezlashtiruvchi tezkor klaviatura kombinatsiyalari (Hotkeys)

## Nazariy qism

### 1. Terminal vs Shell — Farqi nimada?

Boshlovchilar ko'pincha "qora ekran"ni bitta narsa deb atashadi, ammo u ikki qismdan iborat:

```
┌────────────────────────────────────────────────────────┐
│ TERMINAL EMULYATORI (GNOME Terminal, Alacritty, iTerm)  │
│  - Matnni ekranga chizadi, shrift va ranglarni ko'rsatadi│
│  - Klaviatura bosilishini qabul qiladi                 │
├────────────────────────────────────────────────────────┤
│ SHELL (QOBIQ - Bash, Zsh, Fish)                        │
│  - Kiritilgan matnni tahlil qiladi (parsing)           │
│  - Buyruqni topadi va yadroga bajarish uchun beradi    │
│  - Natijani terminalga qaytaradi                       │
└────────────────────────────────────────────────────────┘
```

1. **Terminal:** Foydalanuvchi oynasi (Grafik dastur).
2. **Shell:** Buyruqlarni talqin qiluvchi (interpretatsiya) dastur. Ubuntu 24.04 da standart shell — **Bash** (Bourne Again Shell). Dasturchilar orasida esa plaginlarga boy **Zsh** (Oh My Zsh bilan) juda mashhur.

### 2. Buyruqlar Anatomiyasi

Linuxda har qanday buyruq quyidagi qoliplardan biriga tushadi:

```bash
buyruq [bayroqlar] [argumentlar]
```

- **Buyruq (Command):** Bajarilishi kerak bo'lgan dastur nomi (`ls`, `mkdir`, `python3`).
- **Qisqa bayroqlar (Short flags):** Bitta tire `-` bilan yoziladi va birlashtirish mumkin (`ls -l -a` ➔ `ls -la`).
- **Uzun bayroqlar (Long flags):** Ikkita tire `--` bilan to'liq so'z ko'rinishida yoziladi (`ls --all --human-readable`).
- **Argumentlar:** Buyruq kim/nima ustida amal bajarishi kerakligi (`/var/log`, `main.py`).

### 3. Muhim Muhit O'zgaruvchilari (Environment Variables)

Linux tizimi muhim parametrlarni maxsus o'zgaruvchilarda saqlaydi:
- `$HOME` — Joriy foydalanuvchining uy katalogi (`/home/shamsiddin`).
- `$USER` — Tizimga kirgan foydalanuvchi logini.
- `$SHELL` — Ishlatilayotgan faol shell dasturi (`/bin/bash` yoki `/bin/zsh`).
- `$PATH` — Terminalda buyruq kiritilganda tizim qidiradigan kataloglar ro'yxati (ikki nuqta `:` bilan ajratilgan).

## Amaliy misol

```bash
# 1. Faol shell va foydalanuvchini bilish
echo "Mening shellim: $SHELL"
echo "Foydalanuvchi: $USER"
echo "Uy katalogi: $HOME"

# 2. PATH o'zgaruvchisini ko'rish
echo $PATH

# 3. Buyruq tarixini ko'rish va qidirish
history | tail -n 10
```

### ⚡ Eng muhim tezkor tugmalar (Hotkeys):
- `Ctrl + C` — Ishlayotgan jarayonni darhol to'xtatish (SIGINT).
- `Ctrl + L` — Ekranni tozalash (`clear` buyrug'i ekvivalenti).
- `Tab` — Buyruq yoki fayl nomini avtomatik to'ldirish (Auto-complete). Bosh harfini yozib `Tab`ni 2 marta bossangiz, mos variantlarni ko'rsatadi.
- `Ctrl + R` — Avval ishlatilgan buyruqlarni interaktiv qidirish (Reverse-i-search).
- `Ctrl + A` / `Ctrl + E` — Kursorni qator boshiga / oxiriga o'tkazish.
- `Ctrl + U` / `Ctrl + K` — Kursordan chapdagi / o'ngdagi butun matnni o'chirish.

## Keng tarqalgan xatolar

**Xato 1:** Linuxda registr (katta/kichik harflar) farqiga e'tibor bermaslik.
- ❌ `Cd /Home` yoki `Ls -La` deb yozish.
- ✅ **Sabab:** Linuxda barcha buyruqlar va fayl nomlari **case-sensitive** (harf registriga sezgir). `File.txt`, `file.txt` va `FILE.TXT` — butunlay boshqa-boshqa 3 ta fayldir.

**Xato 2:** `Tab` tugmasidan foydalanmasdan uzun yo'llarni qo'lda xato bilan yozish.
- ❌ `/var/log/nginx/access.log` ni qo'lda yozib harfiy xatoga yo'l qo'yish.
- ✅ **Sabab:** Har doim `cd /v` + `Tab` + `l` + `Tab` + `n` + `Tab` orqali to'ldiring — bu ham tez, ham xatosiz.

## Mashq/topshiriq

1. **(Oson)** Terminalda `echo $USER` va `echo $SHELL` buyruqlarini bajaring.
2. **(O'rtacha)** `Ctrl + R` tugmalarini bosib, tarixdan avval kiritgan `uname` buyrug'ingizni toping va ishga tushiring.
3. **(Qiyin)** Terminalda `echo "Salom Linux" > test.txt` orqali fayl yarating va `cat test.txt` orqali uni o'qing.

## Qisqacha xulosa

Terminal — Linux boshqaruvining eng tezkor va qudratli vositasidir. Buyruqlar sintaksisi, `Tab` avtomatik to'ldirish va `Ctrl+R` qidiruvi orqali terminalda ishlash grafik interfeysdan bir necha barobar unumli bo'ladi.

## Bog'liq

- Oldingi dars: [0.1. Linux nima, tarixi va tizim arxitekturasi](0.1-linux-nima-tarixi-arxitekturasi.md)
- Keyingi dars: [1.1. Linux fayl daraxti (FHS) va muhim kataloglar tuzilishi](../01-bob-fayl-tizimi/1.1-fayl-daraxti-tuzilishi.md)
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
                "name": "1.1. Linux fayl daraxti (FHS) va muhim kataloglar tuzilishi",
                "content": """# Linux fayl daraxti (FHS) va muhim kataloglar tuzilishi

## Bu darsda nimalarni o'rganasiz

- Linux Fayl Tizimi Ierarxiyasi Standarti (FHS — Filesystem Hierarchy Standard)
- Windows disklaridan (C:, D:) Linux yagona ildiz tizimi (`/`)ning farqi
- Tizimdagi eng muhim kataloglar (`/etc`, `/var`, `/home`, `/root`, `/opt`, `/tmp`)ning vazifalari
- Absolyut (to'liq) va Nisbiy (nisbiy) yo'llar (Absolute vs Relative paths)

## Nazariy qism

### 1. Yagona Ildiz (`/`) Tushunchasi

Windows tizimida har bir qattiq disk alohida harf bilan belgilanadi (`C:\\`, `D:\\`). Linuxda esa **barcha qurilmalar, disklar va bo'limlar** yagona daraxt — **`/` (root/ildiz)** katalogiga ulanadi (mount qilinadi).

```
                      / (Ildiz katalogi)
  ┌─────────┬─────────┼─────────┬─────────┬─────────┐
 /bin      /etc      /home     /var      /opt      /tmp
           │         │         │
      nginx.conf  shamsiddin  /log
                     │         │
                 Documents  nginx/access.log
```

### 2. Standart Kataloglarning Aniq Vazifalari

| Katalog | Vazifasi va Tavsifi |
|---|---|
| **`/`** | Butun operatsion tizimning boshlang'ich nuqtasi (Root directory). |
| **`/home`** | Oddiy foydalanuvchilarning shaxsiy ma'lumotlari (`/home/shamsiddin`). |
| **`/root`** | Superadmin (root) foydalanuvchisining shaxsiy uyi (oddiy foydalanuvchilar kira olmaydi). |
| **`/etc`** | Tizim va dasturlarning barcha **konfiguratsiya fayllari** (`nginx.conf`, `hosts`, `passwd`). |
| **`/var`** | O'zgaruvchan ma'lumotlar: log fayllar (`/var/log`), ma'lumotlar bazasi fayllari, veb-saytlar (`/var/www`). |
| **`/opt`** | Ixtiyoriy va uchinchi tomon yirik dasturlari (Optional software, shaxsiy loyihalar). |
| **`/tmp`** | Vaqtinchalik fayllar (Temporary). Tizim qayta yuklanganda odatda tozalanadi. |
| **`/bin` & `/usr/bin`** | Tizimning barcha bajariluvchi buyruqlari (`ls`, `cp`, `python3`, `git`). |
| **`/dev`** | Uskunalar va qurilmalar fayllari (`/dev/sda`, `/dev/null`, `/dev/random`). |
| **`/proc` & `/sys`** | Virtual fayl tizimlari: Yadro va apparatura holati to'g'ridan-to'g'ri xotiradan aks etadi. |

### 3. Absolyut va Nisbiy Yo'llar

- **Absolyut yo'l (Absolute path):** Har doim ildiz `/` dan boshlanadi va qayerda turganingizdan qat'i nazar bir xil manzilni ko'rsatadi:
  - Misol: `/var/log/nginx/error.log`
- **Nisbiy yo'l (Relative path):** Hozir turgan papkangizga nisbatan hisoblanadi:
  - `.` — Joriy katalog
  - `..` — Bitta yuqoridagi ota-katalog
  - `~` — Foydalanuvchining uy katalogi (`$HOME`)
  - Misol: Agar `/var` da tursangiz, `log/nginx/error.log` deb yozish yetarli.

## Amaliy misol

```bash
# 1. Ildiz katalogidagi barcha bo'limlarni ko'rish
ls -la /

# 2. Qayerda turganimizni aniqlash
pwd

# 3. Uy katalogiga o'tish (3 xil usul)
cd /home/$USER   # Absolyut yo'l
cd ~             # Tilda qisqartmasi
cd               # Hech narsa yozmasdan cd bossangiz ham uyga qaytadi

# 4. Ikki daraja yuqoriga chiqish
cd ../..
```

## Keng tarqalgan xatolar

**Xato 1:** `/root` bilan `/` (root directory)ni adashtirish.
- ❌ `/root` papkasi — butun tizim ildizi deb o'ylash.
- ✅ **Sabab:** `/` — bu butun tizimning ildizi. `/root` esa faqat superadmin (root)ning uy papkasidir (`shamsiddin` uchun `/home/shamsiddin` bo'lgani kabi).

**Xato 2:** Nisbiy yo'lda boshidagi `/` ni unutish yoki ortiqcha qo'yish.
- ❌ `/home/shamsiddin` da turib, ichidagi `loyiha` papkasiga `cd /loyiha` deb kirishga urinish.
- ✅ **Sabab:** `cd /loyiha` tizim ildizidan qidiradi va `No such file or directory` xatosini beradi. To'g'risi: `cd loyiha` yoki `cd ./loyiha`.

## Mashq/topshiriq

1. **(Oson)** `pwd` buyrug'i orqali joriy papkangizni chiqaring va uning absolyut yo'lini aniqlang.
2. **(O'rtacha)** `cd /etc` orqali konfiguratsiyalar papkasiga kiring, keyin `cd ../var/log` orqali loglar papkasiga nisbiy yo'l bilan o'ting.
3. **(Qiyin)** `/proc/cpuinfo` va `/proc/meminfo` fayllarining dastlabki 5 qatorini o'qib, protsessor va operativ xotira hajmini ko'ring.

## Qisqacha xulosa

Linux fayl tizimi yagona ildiz (`/`) atrofida standartlashtirilgan. Konfiguratsiyalar `/etc`, loglar `/var/log`, shaxsiy fayllar `/home` da saqlanadi. Yo'llarni to'g'ri tushunish tizimda adashib qolmaslikning kalitidir.

## Bog'liq

- Oldingi dars: [0.2. Ubuntu 24.04 LTS tizimi, Terminal va Shell asoslari](../00-bob-kirish/0.2-ubuntu-24-04-terminal-shell-asoslari.md)
- Keyingi dars: [1.2. Fayllar va papkalarni ko'rish va navigatsiya](1.2-navigatsiya-va-fayllarni-korish.md)
"""
            },
            {
                "fn": "1.2-navigatsiya-va-fayllarni-korish.md",
                "name": "1.2. Fayllar va papkalarni ko'rish va navigatsiya (pwd, ls, cd, cat, less, head, tail)",
                "content": """# Fayllar va papkalarni ko'rish va navigatsiya

## Bu darsda nimalarni o'rganasiz

- Kataloglar bo'ylab tezkor harakatlanish (`pwd`, `cd`)
- Fayllar ro'yxatini batafsil ko'rish (`ls`, `ls -lah`, `tree`)
- Katta va kichik matnli fayllarni o'qish (`cat`, `less`, `more`)
- Loglarni real-vaqtda jonli monitoring qilish (`head`, `tail -f`)

## Nazariy qism

### 1. `ls` Buyrug'i va Uning Quvvati

Oddiy `ls` faqat fayl nomlarini chiqaradi. Professional administratorlar har doim kengaytirilgan bayroqlardan foydalanadi:

```bash
ls -lah
```
- `-l` (long format): Ruxsatlar, fayl egasi, hajmi va o'zgarish sanasi bilan to'liq jadval.
- `-a` (all): Yashirin fayllarni ham ko'rsatadi (nuqta `.` bilan boshlanuvchi fayllar, masalan `.bashrc`, `.env`).
- `-h` (human-readable): Fayl o'lchamlarini baytlarda emas, `4.2K`, `15M`, `2.1G` ko'rinishida chiqaradi.

### 2. Fayllarni O'qish Vositalari Taqqoslanishi

```
┌─────────┬─────────────────────────┬──────────────────────────────────────────┐
│ Buyruq  │ Qachon ishlatiladi      │ Xususiyati                               │
├─────────┼─────────────────────────┼──────────────────────────────────────────┤
│ cat     │ Kichik fayllar uchun    │ Butun faylni bittada terminalga to'kadi  │
│ less    │ Katta fayllar/kod uchun │ Sahifama-sahifa o'qish, qidirish (/so'z) │
│ head    │ Fayl boshi uchun        │ Standart 10 qatorni chiqaradi (-n 20)   │
│ tail    │ Fayl oxiri va LOGLAR    │ Oxirgi qatorlar, -f bilan real vaqtda    │
└─────────┴─────────────────────────┴──────────────────────────────────────────┘
```

## Amaliy misol

```bash
# 1. Yashirin va o'lchamlari bilan saralab ko'rish (hajmi bo'yicha kamayish tartibida: -S)
ls -laSh /var/log

# 2. Katta log faylini less bilan ochish
less /var/log/dpkg.log
# less ichida:
#   '/' bosib qidiruv so'zini yozing (masalan /install)
#   'n' keyingi natijaga o'tadi
#   'q' dasturdan chiqadi

# 3. Faylning boshidan 5 ta qator
head -n 5 /etc/passwd

# 4. Nginx yoki tizim loglarini jonli kuzatish (serverga so'rov kelganda darhol yangilanadi)
tail -f /var/log/syslog
# To'xtatish uchun: Ctrl + C
```

## Keng tarqalgan xatolar

**Xato 1:** Katta (masalan 1GB) log faylini `cat` bilan ochish.
- ❌ `cat /var/log/huge_access.log`
- ✅ **Sabab:** `cat` butun faylni xotiraga yuklab terminalga oqizadi, terminal muzlab qoladi va sekinlashadi. Katta fayllar uchun FAQAT `less` yoki `tail` ishlating!

**Xato 2:** `tail -f` dan chiqishni bilmaslik.
- ❌ Terminal qotib qoldi deb oynani yopib yuborish.
- ✅ **Sabab:** `tail -f` doimiy oqim rejimida ishlaydi, undan chiqish uchun `Ctrl + C` bosiladi.

## Mashq/topshiriq

1. **(Oson)** Uy katalogingizdagi barcha yashirin fayllarni `ls -la ~` orqali ko'ring.
2. **(O'rtacha)** `/etc/passwd` faylining faqat oxirgi 7 qatorini `tail -n 7 /etc/passwd` orqali ekranga chiqaring.
3. **(Qiyin)** `less /etc/services` faylini oching va ichidan `/http` deb qidirib, HTTP qaysi portda ishlashini toping.

## Qisqacha xulosa

Kichik konfiguratsiyalarni `cat`, sahifalab o'rganishni `less`, server loglarini jonli tahlil qilishni esa `tail -f` orqali amalga oshiramiz. `ls -lah` esa har qanday katalogda ilk ishlatiladigan asosiy buyruqdir.

## Bog'liq

- Oldingi dars: [1.1. Linux fayl daraxti (FHS) va muhim kataloglar tuzilishi](1.1-fayl-daraxti-tuzilishi.md)
- Keyingi dars: [1.3. Fayl va papkalar ustida amallar](1.3-fayl-va-papkalarni-boshqarish.md)
"""
            },
            {
                "fn": "1.3-fayl-va-papkalarni-boshqarish.md",
                "name": "1.3. Fayl va papkalar ustida amallar (mkdir, touch, cp, mv, rm, rmdir)",
                "content": """# Fayl va papkalar ustida amallar (mkdir, touch, cp, mv, rm)

## Bu darsda nimalarni o'rganasiz

- Yangi fayl va chuqur papkalar ierarxiyasini yaratish (`mkdir -p`, `touch`)
- Fayllar va butun kataloglarni xavfsiz nusxalash (`cp`, `cp -r`, `cp -a`)
- Fayllarni ko'chirish va nomini o'zgartirish (`mv`)
- Fayllarni xavfsiz o'chirish va xavfli `rm -rf` xatolaridan saqlanish

## Nazariy qism

### 1. Yaratish va Strukturani Qurish

- `touch fayl_nomi` — Agar fayl mavjud bo'lmasa, yangi bo'sh fayl yaratadi; agar mavjud bo'lsa, uning so'nggi o'zgarish vaqtini (timestamp) yangilaydi.
- `mkdir papka_nomi` — Yangi katalog yaratadi.
- `mkdir -p a/b/c/d` — `-p` (parents) bayrog'i yo'ldagi barcha yetishmayotgan ota-papkalarni bittada yaratadi.

### 2. Nusxalash (`cp`) va Ko'chirish (`mv`)

```
┌──────────────────────────────────────┐     cp -r app app_backup
│  app/                                │ ─────────────────────────► ┌────────────────────┐
│   ├── main.py                        │                            │ app_backup/        │
│   └── utils.py                       │                            │  ├── main.py       │
└──────────────────────────────────────┘                            │  └── utils.py      │
                                                                    └────────────────────┘
```

- `cp fayl.txt nusxa.txt` — Bitta fayldan nusxa olish.
- `cp -r papka yangi_papka` — `-r` (recursive) bayrog'i papkani barcha ichki fayllari bilan birga nusxalaydi.
- `mv eski_nom.py yangi_nom.py` — Nomini o'zgartirish (Rename).
- `mv fayl.py /opt/app/` — Boshqa manzilga ko'chirish (Move).

### 3. O'chirish (`rm`)

> [!CAUTION]
> Linuxda `rm` orqali o'chirilgan fayllar "Korzinka"ga (Trash) tushmaydi! Ular darhol diskdan o'chiriladi va ularni qaytarish juda qiyin.

- `rm fayl.txt` — Bitta faylni o'chirish.
- `rm -r papka` — Papka va uning ichidagi barcha narsalarni o'chirish.
- `rm -f fayl` — `-f` (force) tasdiqlash so'ramasdan majburiy o'chiradi.
- `rm -rf papka` — Eng ko'p ishlatiladigan, lekin eng ehtiyotkorlik talab qiluvchi buyruq.

## Amaliy misol

```bash
# 1. Murakkab loyiha strukturasini bitta buyruq bilan qurish
mkdir -p ~/my_project/{src,tests,docs,config}
touch ~/my_project/src/{__init__.py,main.py,utils.py}
touch ~/my_project/config/settings.env

# 2. Strukturani tekshirish
ls -R ~/my_project

# 3. Zaxira nusxa yaratish
cp -r ~/my_project ~/my_project_backup

# 4. Fayl nomini o'zgartirish va ko'chirish
mv ~/my_project/config/settings.env ~/my_project/config/.env

# 5. Sinov loyihasini tozalash
rm -rf ~/my_project_backup
```

## Keng tarqalgan xatolar

**Xato 1:** `rm -rf /` yoki `rm -rf /*` kabi buyruqlarni ishlatish.
- ❌ Noto'g'ri probel qo'yish: `rm -rf / tmp/mydata` (bunda `/` ildiz papkasi ham o'chib ketadi!).
- ✅ **Sabab:** `rm -rf` oldidan har doim yo'lni 2 marta tekshiring. Hech qachon o'zgaruvchilarni bo'sh holda `rm -rf "$DIR/*"` qilib ishlatmang.

**Xato 2:** Papkani nusxalashda `-r` bayrog'ini unutish.
- ❌ `cp my_folder my_folder2` ➔ `cp: -r not specified; omitting directory 'my_folder'`.
- ✅ **Sabab:** Papkalarni nusxalash uchun doimo `cp -r` (rekursiv) yozish shart.

## Mashq/topshiriq

1. **(Oson)** Uy katalogingizda `linux_dars` nomli papka va ichida `dars1.txt` fayli yarating.
2. **(O'rtacha)** `mkdir -p` yordamida `app/backend/api/v1` papkalar zanjirini yarating va ichiga `views.py` faylini qo'ying.
3. **(Qiyin)** `app` papkasini `app_v1` ga nusxalang, so'ng `app` papkasini to'liq o'chirib tashlang.

## Qisqacha xulosa

`mkdir -p` papkalar zanjirini, `touch` fayllarni yaratadi. `cp -r` kataloglarni nusxalaydi, `mv` esa ko'chiradi yoki nomini o'zgartiradi. `rm -rf` buyrug'idan doimo ehtiyotkorlik bilan foydalanish lozim.

## Bog'liq

- Oldingi dars: [1.2. Fayllar va papkalarni ko'rish va navigatsiya](1.2-navigatsiya-va-fayllarni-korish.md)
- Keyingi dars: [1.4. Qidiruv va filtrlar (find, grep, ripgrep)](1.4-qidiruv-buyruqlari-find-grep.md)
"""
            },
            {
                "fn": "1.4-qidiruv-buyruqlari-find-grep.md",
                "name": "1.4. Qidiruv va filtrlar (find, grep, which, whereis, xargs)",
                "content": """# Qidiruv va filtrlar (find, grep, which, xargs)

## Bu darsda nimalarni o'rganasiz

- Fayllarni nomi, o'lchami, turi va o'zgarish vaqti bo'yicha topish (`find`)
- Matn ichidan qidiruv va filtrlash (`grep`, `grep -rn`)
- Dasturlar va buyruqlar joylashuvini aniqlash (`which`, `whereis`)
- Quvurlar (Pipe `|`) va topilgan natijalar ustida amallar bajarish (`xargs`, `-exec`)

## Nazariy qism

### 1. `find` — Fayl Tizimi Bo'yicha Qidiruv

`find` buyrug'i disk bo'ylab fayl yoki papkalarni atributlari bo'yicha qidiradi:

```bash
find [qayerdan] [qanday mezon] [amal]
```

- **Nomi bo'yicha:** `find . -name "*.py"` (yoki registrga qaramasdan `-iname "*.PNG"`).
- **Turi bo'yicha:** `-type f` (faqat fayllar), `-type d` (faqat papkalar).
- **Hajmi bo'yicha:** `-size +100M` (100MB dan katta fayllar), `-size -10k` (10KB dan kichik).
- **Vaqti bo'yicha:** `-mtime -7` (oxirgi 7 kunda o'zgarganlar), `-mmin -60` (oxirgi 1 soatda).

### 2. `grep` — Matn Ichidan Qidiruv (Global Regular Expression Print)

Fayl yoki buyruq natijasi ichidan qatorlarni qidiradi:
- `-i` — Registrga sezgir emas (Ignore case).
- `-r` yoki `-R` — Papkalar ichidan rekursiv qidirish.
- `-n` — Qaysi qatorda ekanini raqami bilan ko'rsatish.
- `-v` — Teskari qidiruv (Mos KELMAYDIGAN qatorlarni chiqarish).

```
[ps aux buyrug'i natijasi]  ──►  | (Pipe)  ──►  [grep python]  ──► Faqat python qatorlari
```

## Amaliy misol

```bash
# 1. /var katalogidan 50MB dan katta bo'lgan barcha fayllarni topish
find /var -type f -size +50M

# 2. Joriy loyihadagi barcha .env fayllarni qidirish
find ~ -name ".env"

# 3. Butun loyiha kodidan "SECRET_KEY" so'zini qator raqami bilan topish
grep -rn "SECRET_KEY" /opt/yordamchi/

# 4. Pipe (|) orqali Nginx logidan faqat 404 xatolarini sanash
cat /var/log/nginx/access.log | grep " 404 " | wc -l

# 5. Qidirib topilgan barcha .log fayllarni bittada arxivlash (xargs)
find /var/log -name "*.log" | xargs tar -czvf logs_backup.tar.gz
```

## Keng tarqalgan xatolar

**Xato 1:** `find` da fayl shablonini qo'shtirnoqsiz yozish.
- ❌ `find . -name *.py`
- ✅ **Sabab:** Agar joriy papkada `a.py` va `b.py` bo'lsa, Shell ularni kengaytirib `find . -name a.py b.py` ga aylantiradi va sintaktik xato beradi. Doimo qo'shtirnoqda yozing: `find . -name "*.py"`.

**Xato 2:** `grep` o'rniga `find` yoki aksincha ishlatish.
- ❌ Fayl ichidagi so'zni topish uchun `find` ishlatish.
- ✅ **Farqi:** `find` — faylning **O'ZINI** (nomi, sanasi, hajmi) qidiradi. `grep` — faylning **ICHIDAGI MATNNI** qidiradi.

## Mashq/topshiriq

1. **(Oson)** `which python3` va `which git` buyruqlari orqali ularning qayerda o'rnatilganini aniqlang.
2. **(O'rtacha)** `/etc` papkasi ichidan nomi `.conf` bilan tugaydigan barcha fayllarni `find /etc -name "*.conf"` orqali toping.
3. **(Qiyin)** `/etc/passwd` faylidan `/bin/bash` qobig'iga ega bo'lgan foydalanuvchilar ro'yxatini `grep "/bin/bash" /etc/passwd` orqali chiqaring.

## Qisqacha xulosa

`find` fayllarni o'lchami, sanasi va nomi bo'yicha qidirishda tengsizdir. `grep` esa kod va loglar ichidan kerakli satrlarni lahzada filtrlash imkonini beradi.

## Bog'liq

- Oldingi dars: [1.3. Fayl va papkalar ustida amallar](1.3-fayl-va-papkalarni-boshqarish.md)
- Keyingi dars: [2.1. Foydalanuvchilar va guruhlar boshqaruvi](../02-bob-ruxsatlar/2.1-foydalanuvchilar-va-guruhlar.md)
"""
            }
        ]
    },
    {
        "dir": "02-bob-ruxsatlar",
        "title": "02. Foydalanuvchilar, Guruhlar va Ruxsatlar (Permissions)",
        "lessons": [
            {
                "fn": "2.1-foydalanuvchilar-va-guruhlar.md",
                "name": "2.1. Foydalanuvchilar va guruhlar boshqaruvi (adduser, usermod, sudo, /etc/passwd)",
                "content": """# Foydalanuvchilar va guruhlar boshqaruvi

## Bu darsda nimalarni o'rganasiz

- Linux ko'p foydalanuvchili xavfsizlik modeli (Multi-user model)
- Yangi foydalanuvchi yaratish (`adduser` vs `useradd`), parol o'rnatish va o'chirish
- Superadmin (sudo / root) huquqlarini xavfsiz boshqarish
- `/etc/passwd`, `/etc/shadow` va `/etc/group` konfiguratsiya fayllarining tuzilishi

## Nazariy qism

### 1. Foydalanuvchi va Guruh Tushunchasi

Linuxda har bir fayl va har bir ishlayotgan jarayon aniq bir **User (UID)** va **Group (GID)** ga tegishli bo'ladi.
- **Root (UID 0):** Cheklanmagan mutlaq huquqqa ega tizim boshqaruvchisi.
- **Tizim foydalanuvchilari (UID 1-999):** Xizmatlar uchun ajratilgan maxsus foydalanuvchilar (`www-data`, `postgres`, `nobody`). Ular tizimga parol bilan kira olmaydi (nologin).
- **Oddiy foydalanuvchilar (UID 1000+):** Siz va boshqa xodimlar uchun yaratilgan hisoblar (`shamsiddin`, `developer`).

### 2. `adduser` vs `useradd` Farqi

- `useradd` — Quyi darajadagi (low-level) buyruq. Standart holda uy papkasi yoki parolni avtomatik yaratmaydi.
- `adduser` — Ubuntu 24.04 dagi interaktiv, qulay skript. Uy papkasini (`/home/nomi`) ochadi, standart `.bashrc` ni nusxalaydi va parolni darhol so'raydi.

### 3. Sudo (Superuser Do) Huquqi

Hech qachon serverda doimiy ravishda `root` sifatida ishlamang! Buning o'rniga oddiy foydalanuvchiga `sudo` guruhiga kirish huquqi beriladi.

```bash
# Foydalanuvchini sudo guruhiga qo'shish
sudo usermod -aG sudo developer
```
`-aG` — Append Group (Mavjud guruhlarini o'chirmasdan, yangi guruhni qo'shish).

## Amaliy misol

```bash
# 1. Yangi ishlab chiquvchi uchun hisob yaratish
sudo adduser devuser

# 2. Uni sudo va docker guruhlariga a'zo qilish
sudo usermod -aG sudo,docker devuser

# 3. Foydalanuvchi qaysi guruhlarga tegishli ekanini tekshirish
groups devuser

# 4. Foydalanuvchi hisobiga o'tish (Switch User)
su - devuser

# 5. Hisobni barcha fayllari bilan o'chirish
sudo userdel -r devuser
```

## Keng tarqalgan xatolar

**Xato 1:** `usermod` da `-a` (append) bayrog'ini unutib, faqat `-G` yozish.
- ❌ `sudo usermod -G docker devuser`
- ✅ **Sabab:** Bu buyruq foydalanuvchini oldingi BARCHA guruhlaridan (jumladan `sudo` dan) chiqarib, faqat `docker` guruhida qoldiradi! Doimo `sudo usermod -aG guruh_nomi` deb yozing.

**Xato 2:** Parollarni `/etc/passwd` faylidan qidirish.
- ❌ Xavfsizlik sababli parollarning xesh (hash) nusxalari faqat root o'qiy oladigan `/etc/shadow` faylida saqlanadi.

## Mashq/topshiriq

1. **(Oson)** `id` va `whoami` buyruqlari orqali o'z UID, GID va guruhlaringizni ko'ring.
2. **(O'rtacha)** `sudo addgroup developers` buyrug'i bilan yangi guruh oching va o'zingizni unga a'zo qiling.
3. **(Qiyin)** `/etc/passwd` faylini ochib, undagi oxirgi qatordan yangi qo'shilgan foydalanuvchi ma'lumotlarini tahlil qiling.

## Qisqacha xulosa

Xavfsiz Linux ma'muriyati oddiy foydalanuvchilar va `sudo` guruhidan to'g'ri foydalanishga asoslanadi. `adduser` yangi hisoblarni qulay yaratadi, `usermod -aG` esa xavfsiz tarzda guruhlarga a'zo qiladi.

## Bog'liq

- Oldingi dars: [1.4. Qidiruv va filtrlar](../01-bob-fayl-tizimi/1.4-qidiruv-buyruqlari-find-grep.md)
- Keyingi dars: [2.2. Fayl ruxsatlari: Read, Write, Execute (chmod)](2.2-fayl-ruxsatlari-chmod-chown.md)
"""
            },
            {
                "fn": "2.2-fayl-ruxsatlari-chmod-chown.md",
                "name": "2.2. Fayl ruxsatlari: Read, Write, Execute va raqamli tizim (chmod 755/644)",
                "content": """# Fayl ruxsatlari: Read, Write, Execute va raqamli tizim

## Bu darsda nimalarni o'rganasiz

- Linux ruxsatlar triadasini: Read (r), Write (w), Execute (x)
- Foydalanuvchilar toifalarini: Owner (u), Group (g), Others (o)
- Raqamli (Oktal: 755, 644, 600, 700) va Belgili (Symbolic: +x, u+rw) `chmod` usullari
- Papka va Fayllar uchun Execute (x) ruxsatining muhim farqi

## Nazariy qism

### 1. `ls -l` Ruxsatlar qatorining tahlili

`ls -l` buyrug'ini bajarganingizda har bir fayl oldida 10 ta belgi ko'rinadi:

```
 -  r w x  r - x  r - -    1  shamsiddin  developers  4096  deploy.sh
┬  ─────┬  ─────┬  ─────┬
│       │       │       └── 3. Boshqalar (Others - o): Faqat o'qish (r--)
│       │       └────────── 2. Guruh (Group - g): O'qish va bajarish (r-x)
│       └────────────────── 1. Egasi (Owner - u): O'qish, yozish, bajarish (rwx)
└────────────────────────── Turi: '-' oddiy fayl, 'd' katalog/papka, 'l' havola (symlink)
```

### 2. Raqamli (Oktal) Ruxsatlar Tizimi

Har bir huquq aniq raqamli qiymatga ega:
- **Read (r)** = **4** (O'qish)
- **Write (w)** = **2** (Yozish / O'zgartirish)
- **Execute (x)** = **1** (Dastur/skript sifatida ishga tushirish)
- **Ruxsat yo'q (-)** = **0**

Uchta raqam qo'shilib yagona sonni hosil qiladi:
- `rwx` = 4 + 2 + 1 = **7** (To'liq huquq)
- `rw-` = 4 + 2 + 0 = **6** (O'qish va yozish)
- `r-x` = 4 + 0 + 1 = **5** (O'qish va ishga tushirish)
- `r--` = 4 + 0 + 0 = **4** (Faqat o'qish)
- `---` = 0 + 0 + 0 = **0** (Hech qanday huquq yo'q)

### 3. Standart va Xavfsiz Ruxsat Shabloni

| Rejim | Qayerda ishlatiladi | Xavfsizlik darajasi |
|---|---|---|
| **`644`** (`rw-r--r--`) | Standart veb-fayllar, matnlar, rasmlar | Egasi o'zgartiradi, boshqalar faqat o'qiydi |
| **`755`** (`rwxr-xr-x`) | Standart papkalar va umumiy skriptlar | Egasi to'liq, boshqalar kiradi va o'qiydi |
| **`600`** (`rw-------`) | Maxfiy fayllar (SSH `.pem`, `.env`, parollar) | FAQAT egasi o'qiydi va yozadi, boshqalarga yopiq |
| **`700`** (`rwx------`) | Maxfiy papkalar (`~/.ssh`) | FAQAT egasi kira oladi |
| **`777`** (`rwxrwxrwx`) | **MUTLAQO TAQIQLANADI!** | Har qanday begona faylni o'chira yoki buzishi mumkin |

## Amaliy misol

```bash
# 1. Skriptga ishga tushirish ruxsatini berish (+x)
chmod +x deploy.sh

# 2. Maxfiy SSH kalitiga to'g'ri xavfsiz ruxsat o'rnatish
chmod 600 ~/.ssh/id_ed25519

# 3. Papka va ichidagi barcha fayllarga rekursiv ruxsat berish
chmod -R 755 /var/www/html/

# 4. Belgili usulda guruhdan yozish huquqini olib tashlash
chmod g-w settings.py
```

## Keng tarqalgan xatolar

**Xato 1:** Muammo chiqsa darhol `chmod 777` berib yuborish.
- ❌ `sudo chmod -R 777 /var/www` yoki `sudo chmod -R 777 /`
- ✅ **Sabab:** Bu eng xavfli xato! Serverga kirgan har qanday buzg'unchi barcha fayllarni o'zgartira oladi. Agar ruxsat yetishmasa, `777` emas, fayl egasini `chown` orqali to'g'rilash kerak.

**Xato 2:** Papkaga `Execute (x)` huquqi bermaslik.
- ❌ Papkaga `chmod 644 my_folder` qilish.
- ✅ **Sabab:** Linuxda papka ichiga kirish (`cd`) uchun unda albatta **`x` (Execute)** huquqi bo'lishi shart! Papkalar har doim `755` yoki `700` bo'lishi kerak.

## Mashq/topshiriq

1. **(Oson)** `echo 'echo "Hello Linux"' > script.sh` buyrug'i bilan fayl yarating va unga `chmod +x script.sh` berib, `./script.sh` orqali ishga tushiring.
2. **(O'rtacha)** `test.env` fayli yarating va unga `chmod 600 test.env` o'rnating. `ls -l test.env` orqali ruxsatni tekshiring.
3. **(Qiyin)** `rwxr-xr--` ruxsati qanday raqamli ko'rinishga ega bo'lishini hisoblang (Javob: 754).

## Qisqacha xulosa

Linux ruxsatlari uch guruh (Owner, Group, Others) va uch huquq (Read=4, Write=2, Execute=1)dan iborat. Maxfiy fayllar uchun `600`, veb-fayllar uchun `644`, papkalar uchun `755` ishlatiladi. `777` hech qachon ishlatilmasligi kerak.

## Bog'liq

- Oldingi dars: [2.1. Foydalanuvchilar va guruhlar boshqaruvi](2.1-foydalanuvchilar-va-guruhlar.md)
- Keyingi dars: [2.3. Fayl egaligi va maxsus ruxsatlar](2.3-fayl-egaligi-chown-umask.md)
"""
            },
            {
                "fn": "2.3-fayl-egaligi-chown-umask.md",
                "name": "2.3. Fayl egaligi va maxsus ruxsatlar (chown, chgrp, umask, SUID)",
                "content": """# Fayl egaligi va maxsus ruxsatlar (chown, chgrp, umask)

## Bu darsda nimalarni o'rganasiz

- `chown` yordamida fayl va papka egasini hamda guruhini o'zgartirish
- Rekursiv egalik o'rnatish (`chown -R user:group`)
- Standart yaratiladigan fayl ruxsatlarini boshqaruvchi `umask` tushunchasi
- Maxsus ruxsatlar: SUID, SGID va Sticky Bit (`/tmp` dagi kabi)

## Nazariy qism

### 1. `chown` (Change Owner) — Egalikni o'zgartirish

Fayl ruxsatlarini `chmod 777` qilish o'rniga, fayl egasini uni ishlatishi kerak bo'lgan xizmatga (masalan Nginx uchun `www-data`, PostgreSQL uchun `postgres`) o'tkazish professional standart hisoblanadi.

```bash
sudo chown [yangi_ega]:[yangi_guruh] [fayl/papka]
```

Misollar:
- `sudo chown shamsiddin main.py` — Faqat egasini o'zgartirish.
- `sudo chown :developers main.py` — Faqat guruhini o'zgartirish (`chgrp` kabi).
- `sudo chown -R www-data:www-data /var/www/html` — Butun papka va ichidagi barcha fayllar egasi va guruhini `www-data` ga o'tkazish.

### 2. `umask` (User Mask) Tushunchasi

Yangi yaratilgan har qanday fayl yoki papka standart qanday ruxsat olishini `umask` belgilaydi:
- Standart maksimal ruxsat: Fayl uchun `666`, Papka uchun `777`.
- Agar `umask` = `022` bo'lsa:
  - Yangi fayl: `666 - 022 = 644` (`rw-r--r--`)
  - Yangi papka: `777 - 022 = 755` (`rwxr-xr-x`)

### 3. Maxsus Ruxsatlar (Special Permissions)

- **Sticky Bit (+t, 1000):** Papkaga o'rnatiladi. Unga hamma yoza oladi, lekin birovning faylini faqat uning O'Z EGASI o'chira oladi. `/tmp` papkasida aynan shu rejim ishlatiladi (`drwxrwxrwt`).

## Amaliy misol

```bash
# 1. Veb loyiha papkasi egasini joriy foydalanuvchiga, guruhini www-data ga o'tkazish
sudo chown -R $USER:www-data /var/www/my_site

# 2. Joriy umask qiymatini ko'rish
umask

# 3. /tmp papkasi ruxsatlarini ko'rish (Sticky bit 't' ni ko'rish)
ls -ld /tmp
```

## Keng tarqalgan xatolar

**Xato 1:** `root` huquqi bilan fayl yaratib, keyin oddiy foydalanuvchi bilan o'zgartira olmaslik.
- ❌ `sudo touch config.json` qilinsa, uning egasi `root` bo'lib qoladi. Keyin oddiy tahrirlovchi `Permission denied` beradi.
- ✅ **Yechim:** `sudo chown $USER:$USER config.json` orqali egalikni o'zingizga qaytaring.

## Mashq/topshiriq

1. **(Oson)** `/tmp/sinov.txt` faylini yarating va `ls -l /tmp/sinov.txt` orqali uning egasi kim bo'lganini ko'ring.
2. **(O'rtacha)** `sudo chown $USER:nogroup /tmp/sinov.txt` buyrug'i bilan uning guruhini o'zgartiring.
3. **(Qiyin)** `umask 077` buyrug'ini kiritib, yangi fayl yarating va uning ruxsati `600` bo'lganini tekshiring.

## Qisqacha xulosa

`chown` fayl va kataloglarning haqiqiy egasini belgilaydi. Veb-dasturlar va ma'lumotlar bazalarida ruxsat xatoliklari eng avvalo `chown` yordamida to'g'ri foydalanuvchi va guruhni belgilash orqali bartaraf etiladi.

## Bog'liq

- Oldingi dars: [2.2. Fayl ruxsatlari (chmod)](2.2-fayl-ruxsatlari-chmod-chown.md)
- Keyingi dars: [3.1. Jarayonlar boshqaruvi va signallar](../03-bob-jarayonlar-monitoring/3.1-jarayonlarni-boshqarish-ps-top-kill.md)
"""
            }
        ]
    },
    {
        "dir": "03-bob-jarayonlar-monitoring",
        "title": "03. Jarayonlar, Resurslar va Monitoring",
        "lessons": [
            {
                "fn": "3.1-jarayonlarni-boshqarish-ps-top-kill.md",
                "name": "3.1. Jarayonlar (Processes) boshqaruvi va signallar (ps, top, htop, kill, pkill)",
                "content": """# Jarayonlar (Processes) boshqaruvi va signallar

## Bu darsda nimalarni o'rganasiz

- Linux jarayonlari tuzilishi, Process ID (PID) va Ota-bola jarayonlar (PPID)
- Jarayonlar holatini tahlil qilish (`ps aux`, `top`, `htop`)
- Linux signallari: SIGTERM (15), SIGKILL (9), SIGHUP (1)
- Jarayonlarni xavfsiz va majburiy to'xtatish (`kill`, `pkill`, `killall`)

## Nazariy qism

### 1. Jarayon (Process) Nima?

Diskda turgan dastur kodi — bu fayl. U xotiraga yuklanib, protsessor tomonidan bajarila boshlaganda **Jarayon (Process)**ga aylanadi. Har bir jarayonga yagona **PID (Process ID)** raqami beriladi.

Linuxda 1-raqamli eng birinchi jarayon — **`systemd` (PID 1)** bo'lib, qolgan barcha jarayonlar uning bolalari hisoblanadi.

```
                  systemd (PID 1)
          ┌──────────────┼──────────────┐
     sshd (PID 840) nginx (PID 1120) postgres (PID 950)
          │
     bash (PID 2450)
          │
     python3 main.py (PID 3102)
```

### 2. Jarayonlarni Ko'rish Vositalari

- `ps aux` — Barcha foydalanuvchilarning barcha faol jarayonlari bir martalik jadvali:
  - `USER` — Jarayon egasi
  - `PID` — Jarayon raqami
  - `%CPU` / `%MEM` — Protsessor va RAM ulushi
  - `COMMAND` — Ishga tushirilgan buyruq va argumentlar
- `top` / `htop` — Real-vaqtda yangilanib turuvchi interaktiv monitoring ekrani.

### 3. Linux Signallari va To'xtatish

Jarayonga signal yuborish orqali unga nima qilish kerakligini bildiramiz:

| Signal | Raqami | Vazifasi | Tavsifi |
|---|---|---|---|
| **SIGTERM** | `15` | Xushmuomalalik bilan to'xtatish | Standart signal. Jarayonga ulanishlarni yopish va ma'lumotlarni saqlash imkonini beradi. |
| **SIGKILL** | `9` | Majburiy o'ldirish | Jarayonni darhol xotiradan o'chiradi. Unga qarshilik qilib bo'lmaydi. |
| **SIGHUP** | `1` | Qayta yuklash (Reload) | Jarayonni to'xtatmasdan konfiguratsiyani qayta o'qish. |

## Amaliy misol

```bash
# 1. Python yoki Gunicorn jarayonlarini qidirish
ps aux | grep python3

# 2. Interaktiv htop dasturini ishga tushirish
htop
# htop ichida:
#   F6 — CPU yoki MEM bo'yicha saralash
#   F9 — Jarayonga signal yuborish (Kill)
#   F10 yoki 'q' — Chiqish

# 3. PID orqali xavfsiz to'xtatish
kill 3102

# 4. Qotib qolgan jarayonni majburiy o'ldirish
kill -9 3102

# 5. Nomi bo'yicha barcha gunicorn jarayonlarini bittada to'xtatish
pkill -f gunicorn
```

## Keng tarqalgan xatolar

**Xato 1:** Har qanday jarayonni darhol `kill -9` bilan o'ldirish.
- ❌ `kill -9` ma'lumotlar bazasi (PostgreSQL) yoki faylga yozayotgan dasturni keskin to'xtatsa, ma'lumotlar buzilishi (data corruption) xavfi tug'iladi.
- ✅ **To'g'risi:** Avval oddiy `kill PID` (SIGTERM) bering. Faqat jarayon javob bermay qotib qolsagina `kill -9` ishlating.

## Mashq/topshiriq

1. **(Oson)** Terminalda `sleep 500 &` buyrug'i bilan orqa fonga sinov jarayoni yuboring va `ps aux | grep sleep` orqali uning PID raqamini toping.
2. **(O'rtacha)** Topilgan PID raqamini `kill PID` orqali to'xtating.
3. **(Qiyin)** `htop` ni ochib, eng ko'p operativ xotira (RAM) ishlatayotgan 3 ta dasturni aniqlang.

## Qisqacha xulosa

Jarayonlar PID orqali boshqariladi. `ps aux` va `htop` jarayonlarni tahlil qilish, `kill` (SIGTERM) va `pkill` esa ularni xavfsiz to'xtatish uchun asosiy qurollardir.

## Bog'liq

- Oldingi dars: [2.3. Fayl egaligi va maxsus ruxsatlar](../02-bob-ruxsatlar/2.3-fayl-egaligi-chown-umask.md)
- Keyingi dars: [3.2. Fon rejimi, ustuvorlik va uzluksizlik](3.2-fon-rejimi-tmux-nohup.md)
"""
            },
            {
                "fn": "3.2-fon-rejimi-tmux-nohup.md",
                "name": "3.2. Fon rejimi, ustuvorlik va uzluksizlik (jobs, bg, fg, nohup, tmux)",
                "content": """# Fon rejimi, ustuvorlik va uzluksizlik (jobs, bg, fg, nohup, tmux)

## Bu darsda nimalarni o'rganasiz

- Buyruqlarni orqa fonga (Background) yuborish va qaytarish (`&`, `jobs`, `bg`, `fg`, `Ctrl+Z`)
- SSH sessiyasi yopilganda ham dastur ishlashini ta'minlash (`nohup`, `disown`)
- Terminal multipleksori: **Tmux** orqali uzluksiz sessiyalar boshqaruvi
- Jarayonlar ustuvorligi (CPU Priority)ni sozlash (`nice`, `renice`)

## Nazariy qism

### 1. Old fon (Foreground) vs Orqa fon (Background)

- **Foreground:** Buyruq terminalni band qiladi, u tugamaguncha yangi buyruq yozib bo'lmaydi.
- **Background (`&`):** Buyruq orqa fonda ishlaydi, terminal esa boshqa ishlar uchun ochiq qoladi.

```
  Klaviatura ──► [Ctrl + Z] (To'xtatib turish - Stopped)
                      │
                      ├──► bg (Orqa fonda davom ettirish)
                      └──► fg (Old fonga qaytarish)
```

### 2. Muammo — SSH uzilganda dastur to'xtab qolishi

Agar masofaviy serverda Python skriptini ishga tushirsangiz va internet uzilsa yoki SSH oynasini yopsangiz, Linux unga **SIGHUP** signalini yuboradi va skript darhol o'chadi.

Yechimlar:
1. `nohup` (No Hang Up) — SIGHUP signalini e'tiborsiz qoldiradi va chiqishlarni `nohup.out` fayliga yo'naltiradi.
2. **Tmux** — Serverda virtual terminal sessiyasi ochadi. Siz kompyuteringizni o'chirib yoqsangiz ham, serverdagi Tmux sessiyasi va undagi dasturlar haftalab ishlab turadi.

### 3. Tmux Asosiy Boshqaruvi

Tmux boshqaruv tugmasi: **`Ctrl + B`**
- `tmux new -s bot` — "bot" nomli yangi sessiya ochish.
- `Ctrl + B`, keyin `D` (Detach) — Sessiyadan dasturni to'xtatmasdan chiqish.
- `tmux ls` — Faol sessiyalar ro'yxatini ko'rish.
- `tmux attach -t bot` — Chiqib ketilgan sessiyaga qayta ulanish.

## Amaliy misol

```bash
# 1. Katta arxivlash jarayonini orqa fonda ishga tushirish
tar -czvf backup_full.tar.gz /var/www &

# 2. Faol fon vazifalarini ko'rish
jobs

# 3. Nohup orqali skriptni uzluksiz ishga tushirish
nohup python3 bot.py > bot.log 2>&1 &

# 4. Tmux bilan professional ishlash
tmux new -s mysession
# Sessiya ichida kodni ishga tushirasiz: python3 main.py
# Chiqish uchun: Ctrl+B, so'ng D
# Qayta ulanish:
tmux attach -t mysession
```

## Keng tarqalgan xatolar

**Xato 1:** `nohup` ishlatganda chiqish oqimlarini (`stdout`/`stderr`) yo'naltirmaslik.
- ❌ `nohup python3 app.py &`
- ✅ **Sabab:** Dastur barcha loglarni joriy papkada `nohup.out` degan ulkan faylga to'kib tashlaydi. Doimo log faylini ko'rsating: `nohup python3 app.py > app.log 2>&1 &`.

## Mashq/topshiriq

1. **(Oson)** `sudo apt install tmux` orqali Tmux o'rnating va `tmux new -s test` bilan sessiya oching.
2. **(O'rtacha)** Sessiya ichida `top`ni ishga tushiring, `Ctrl+B` so'ng `D` bilan chiqib keting, keyin `tmux attach -t test` orqali qayta ulaning.
3. **(Qiyin)** `jobs`, `bg` va `fg` buyruqlari yordamida jarayonni orqa va old fonga o'tkazishni sinab ko'ring.

## Qisqacha xulosa

`&` va `jobs` fon vazifalarini boshqaradi. Uzoq davom etadigan ishlar va serverdagi skriptlar uchun **Tmux** eng xavfsiz va qulay vositadir.

## Bog'liq

- Oldingi dars: [3.1. Jarayonlar boshqaruvi va signallar](3.1-jarayonlarni-boshqarish-ps-top-kill.md)
- Keyingi dars: [3.3. Tizim resurslari va xotira monitoringi](3.3-resurslar-monitoringi-df-du-free.md)
"""
            },
            {
                "fn": "3.3-resurslar-monitoringi-df-du-free.md",
                "name": "3.3. Tizim resurslari va xotira monitoringi (free, df, du, uptime, vmstat)",
                "content": """# Tizim resurslari va xotira monitoringi (free, df, du, uptime)

## Bu darsda nimalarni o'rganasiz

- Operativ xotira (RAM) va Swap holatini to'g'ri tahlil qilish (`free -h`, `available` vs `free`)
- Qattiq disk xotirasi to'lishini nazorat qilish (`df -h`)
- Qaysi papka yoki fayl eng ko'p joy olayotganini aniqlash (`du -sh`)
- Protsessor yuki (Load Average) va serverning uzluksiz ishlash vaqti (`uptime`, `vmstat`)

## Nazariy qism

### 1. Operativ Xotira (RAM) va `free -h` Tahlili

Linux operativ xotiradan maksimal unumli foydalanish uchun bo'sh turgan RAMni disk keshiga (Buff/Cache) oladi. Shuning uchun Linuxda "free" xotira kam bo'lishi bu muammo emas!

```bash
free -h
```
Chiqish namunasi:
```
               total        used        free      shared  buff/cache   available
Mem:            15Gi       4.2Gi       1.1Gi       240Mi        10Gi        11Gi
Swap:          4.0Gi       200Mi       3.8Gi
```
- **Total:** Jami RAM hajmi (15 GB).
- **Used:** Dasturlar ishlatayotgan haqiqiy xotira (4.2 GB).
- **Buff/Cache:** Linux tomonidan keshga olingan fayllar (10 GB). Agar dasturga RAM kerak bo'lsa, Linux bu keshni bir zumda bo'shatib beradi.
- **Available:** **Eng muhim ustun!** Yangi dasturlar uchun mavjud haqiqiy erkin xotira (11 GB).
- **Swap:** Qattiq diskdagi virtual xotira (RAM to'lganda ishlatiladi).

### 2. Disk Xotirasi: `df` vs `du`

```
┌────────┬─────────────────────────────┬──────────────────────────────────────────┐
│ Buyruq │ Maqsadi                     │ Ishlatish uslubi                         │
├────────┼─────────────────────────────┼──────────────────────────────────────────┤
│ df -h  │ Disk BO'LIMLARI to'lishi    │ "Diskda necha foiz joy qoldi?" (Global)  │
│ du -sh │ PAPKA va FAYLLAR o'lchami   │ "Bu papka qancha joy egallayapti?"       │
└────────┴─────────────────────────────┴──────────────────────────────────────────┘
```

### 3. Load Average (Server Yuki)

`uptime` buyrug'i natijasidagi oxirgi 3 ta son:
`load average: 0.45, 0.80, 1.10`
- Oxirgi **1 daqiqa**, **5 daqiqa** va **15 daqiqa**dagi yuklanish.
- Agar sizda 4 ta CPU yadrosi bo'lsa, Load Average `4.00` gacha bo'lishi normal (100% band). Agar `8.00` bo'lsa — server 2 barobar ortiqcha yuklangan.

## Amaliy misol

```bash
# 1. RAM va Swap holatini ko'rish
free -h

# 2. Disk bo'limlari to'lish foizini tekshirish
df -hT /

# 3. Joriy papkadagi har bir narsaning hajmini ko'rish
du -sh *

# 4. /var katalogidagi eng katta 5 ta papkani topish
sudo du -sh /var/* | sort -hr | head -n 5

# 5. Protsessor yadrolari sonini bilish
nproc
```

## Keng tarqalgan xatolar

**Xato 1:** `free` ustunini ko'rib "Menda atigi 1GB RAM qolibdi, xotira yetmayapti" deb vahimaga tushish.
- ❌ Faqat `free` ustuniga qarash.
- ✅ **Sabab:** Doimo `available` ustuniga qarang. Linux keshdagi (`buff/cache`) xotirani dasturlar talab qilganda darhol bo'shatadi.

**Xato 2:** Disk 100% to'lib qolganda server qotishini oldindan bilmaslik.
- ❌ Log fayllar `/var/log` da yig'ilib diskni 100% to'ldirsa, ma'lumotlar bazasi (PostgreSQL) va tizim ishdan to'xtaydi.
- ✅ **Yechim:** `df -h` orqali diskni muntazam tekshirib turing va `logrotate` ni sozlang.

## Mashq/topshiriq

1. **(Oson)** `free -h` va `df -h` buyruqlarini bajaring va mavjud RAM hamda asosiy disk bo'sh joyini aniqlang.
2. **(O'rtacha)** `uptime` va `nproc` orqali serveringiz yadrolar soni va Load Average ko'rsatkichini taqqoslang.
3. **(Qiyin)** `sudo du -sh /var/log/* | sort -hr | head -n 3` orqali eng ko'p joy olayotgan 3 ta log faylni toping.

## Qisqacha xulosa

`free -h` dagi `available` ustuni haqiqiy erkin xotirani ko'rsatadi. `df -h` disk bo'limlarini, `du -sh` esa aniq papkalar hajmini tahlil qiladi. Load Average protsessor yadrolariga nisbatan baholanadi.

## Bog'liq

- Oldingi dars: [3.2. Fon rejimi, ustuvorlik va uzluksizlik](3.2-fon-rejimi-tmux-nohup.md)
- Keyingi dars: [4.1. APT va DPKG paket boshqaruvi](../04-bob-paketlar/4.1-apt-va-dpkg-paket-boshqaruvi.md)
"""
            }
        ]
    },
    {
        "dir": "04-bob-paketlar",
        "title": "04. Paketlar va Dasturlar Boshqaruvi (Package Management)",
        "lessons": [
            {
                "fn": "4.1-apt-va-dpkg-paket-boshqaruvi.md",
                "name": "4.1. APT va DPKG paket boshqaruvi (Ubuntu 24.04 deb822 manbalari, apt install)",
                "content": """# APT va DPKG paket boshqaruvi

## Bu darsda nimalarni o'rganasiz

- Linux paket boshqaruv tizimi va `.deb` paketlar tushunchasi
- Ubuntu 24.04 LTS ning yangi **deb822** repozitoriyalar formati (`/etc/apt/sources.list.d/ubuntu.sources`)
- `apt update`, `apt upgrade`, `apt install`, `apt purge` va `apt autoremove` farqlari
- `.deb` fayllarini to'g'ridan-to'g'ri o'rnatish (`dpkg -i`)

## Nazariy qism

### 1. Paket Menejeri Nima?

Windowsda dasturlar internetdan `.exe` yoki `.msi` yuklab olinib o'rnatiladi (viruslar xavfi yuqori). Linuxda esa markaziy, tekshirilgan va xavfsiz **Repozitoriyalar (Omborlar)** mavjud bo'lib, ular orqali barcha dasturlar, kutubxonalar va xavfsizlik yangilanishlari yagona buyruq bilan boshqariladi.

- **DPKG (Debian Package):** Quyi darajadagi menejer. `.deb` faylni o'rnatadi, lekin qaramliklarni (dependencies) avtomatik internetdan tortib keltirmaydi.
- **APT (Advanced Package Tool):** Yuqori darajadagi aqlli vosita. Dastur uchun kerak bo'lgan barcha qo'shimcha kutubxonalarni avtomatik topadi, yuklaydi va o'rnatadi.

### 2. Ubuntu 24.04 LTS dagi Yangilik: deb822 Formati

Oldingi Ubuntu versiyalarida repozitoriyalar `/etc/apt/sources.list` faylida bir qatorli ko'rinishda saqlanardi. **Ubuntu 24.04 LTS** da standart format **deb822** (`/etc/apt/sources.list.d/ubuntu.sources`) ga o'tdi:

```ini
Types: deb
URIs: http://archive.ubuntu.com/ubuntu/
Suites: noble noble-updates noble-security
Components: main restricted universe multiverse
Signed-By: /usr/share/keyrings/ubuntu-archive-keyring.gpg
```

Bu yangi format xavfsizroq va o'qish uchun ancha qulaydir.

### 3. Asosiy APT Buyruqlari Qadamma-qadam

```
1. sudo apt update       ──► Repozitoriyalardagi yangi versiyalar RO'YXATINI yangilaydi
2. sudo apt upgrade -y   ──► O'rnatilgan barcha dasturlarni yangi versiyaga KO'TARADI
3. sudo apt install pkg  ──► Yangi dastur va uning barcha qaramliklarini O'RNATADI
4. sudo apt purge pkg    ──► Dastur va uning barcha sozlamalarini TO'LIQ O'CHIRADI
5. sudo apt autoremove   ──► Keraksiz qolgan eski qaramliklarni TOZALAYDI
```

## Amaliy misol

```bash
# 1. Indekslarni yangilash va tizimni to'liq yangilash
sudo apt update && sudo apt upgrade -y

# 2. Veb dasturchi uchun kerakli to'plamni o'rnatish
sudo apt install -y nginx git curl htop ufw build-essential

# 3. Paket haqida batafsil ma'lumot olish
apt show nginx

# 4. Paket qaysi repozitoriyadan kelishini tekshirish
apt policy nginx

# 5. Dasturni barcha konfiguratsiyalari bilan birga tozalash
sudo apt purge nginx -y
sudo apt autoremove -y
```

## Keng tarqalgan xatolar

**Xato 1:** `apt install` qilishdan oldin `apt update` ni unutish.
- ❌ To'g'ridan-to'g'ri `sudo apt install python3-pip` qilish va `404 Not Found` yoki `Unable to locate package` xatosini olish.
- ✅ **Sabab:** `apt update` qilmasangiz, kompyuteringizdagi repozitoriyalar ro'yxati eskirgan bo'ladi. Har doim avval `sudo apt update` bajaring!

**Xato 2:** `apt remove` bilan `apt purge` farqini bilmaslik.
- ❌ `apt remove` faqat dastur binar faylini o'chiradi, `/etc` dagi sozlamalari qolib ketadi. Dasturni noldan toza o'rnatish uchun `apt purge` ishlatish kerak.

## Mashq/topshiriq

1. **(Oson)** `sudo apt update` buyrug'ini bajaring va tizimingizda nechta paket yangilanishi mumkinligini ko'ring.
2. **(O'rtacha)** `apt show git` buyrug'i orqali Git paketining hajmi va versiyasini ko'ring.
3. **(Qiyin)** `/etc/apt/sources.list.d/ubuntu.sources` faylini `cat` orqali ochib, Ubuntu 24.04 manbalarini ko'zdan kechiring.

## Qisqacha xulosa

Ubuntu 24.04 da APT tizimning yuragi hisoblanadi. Dasturlarni o'rnatishdan oldin doimo `apt update`, o'rnatgandan so'ng ortiqcha fayllarni tozalash uchun `apt autoremove` ishlatiladi.

## Bog'liq

- Oldingi dars: [3.3. Tizim resurslari va xotira monitoringi](../03-bob-jarayonlar-monitoring/3.3-resurslar-monitoringi-df-du-free.md)
- Keyingi dars: [4.2. Arxivlar va tarmoq orqali yuklash](4.2-arxivlar-va-yuklab-olish-curl-wget-tar.md)
"""
            },
            {
                "fn": "4.2-arxivlar-va-yuklab-olish-curl-wget-tar.md",
                "name": "4.2. Arxivlar va tarmoq orqali yuklash (tar, gzip, zip, curl, wget)",
                "content": """# Arxivlar va tarmoq orqali yuklash (tar, zip, curl, wget)

## Bu darsda nimalarni o'rganasiz

- Linuxda arxivlash (`tar`) va siqish (`gzip`, `xz`) tushunchasi
- `.tar.gz`, `.tar.xz`, `.zip` arxivlarini yaratish va ochish
- Internetdan fayllarni to'g'ridan-to'g'ri yuklab olish (`wget`, `curl`)
- `curl` orqali API so'rovlarini yuborish va sarlavhalarni (headers) tekshirish

## Nazariy qism

### 1. Arxivlash (`tar`) vs Siqish (`gzip`)

- **Tar (Tape Archive):** Yuzlab fayl va papkalarni ruxsatlari va egalik huquqlari bilan birga **bitta faylga** birlashtiradi (lekin siqmaydi).
- **Gzip:** Bitta fayl hajmini siqadi (`.gz`).
- Shuning uchun Linuxda ular birga ishlatiladi: **`.tar.gz`** (yoki `.tgz`).

### 2. `tar` Sehrli Bayroqlari

```bash
# Arxiv YARATISH (Create):
tar -czvf arxiv_nomi.tar.gz /manzil/papka

# Arxivni OCHISH (eXtract):
tar -xzvf arxiv_nomi.tar.gz -C /qayerga_ochish/
```

- `-c` — Create (Yangi arxiv yaratish)
- `-x` — eXtract (Arxivni ochish)
- `-z` — Gzip yordamida siqish/ochish
- `-v` — Verbose (Jarayonni ekranda ko'rsatish)
- `-f` — File (Arxiv fayli nomi ko'rsatilishi shart)
- `-C` — Directory (Boshqa katalog ichiga ochish)

### 3. `wget` vs `curl`

- **`wget`:** Fayllarni internetdan to'g'ridan-to'g'ri yuklab olish uchun eng qulay utilita (uzilib qolsa `-c` bilan davom ettiradi).
- **`curl` (Client URL):** Tarmoq protokollari (HTTP, HTTPS, FTP) orqali ma'lumot uzatish uchun qudratli vosita (API testlari, POST/GET so'rovlar, headerlar).

## Amaliy misol

```bash
# 1. Loyiha papkasini to'liq .tar.gz formatida arxivlash
tar -czvf my_project_2026.tar.gz ~/my_project/

# 2. Arxiv ichidagi fayllarni ochmasdan ro'yxatini ko'rish (-t)
tar -tzvf my_project_2026.tar.gz

# 3. Arxivni /tmp papkasi ichiga ochish
tar -xzvf my_project_2026.tar.gz -C /tmp/

# 4. Faylni internetdan yuklab olish
wget https://github.com/fastfetch-cli/fastfetch/releases/latest/download/fastfetch-linux-amd64.deb

# 5. curl orqali tashqi IP manzilni aniqlash
curl -s https://api.ipify.org
echo ""

# 6. curl orqali sayt javob sarlavhasini (HTTP status) tekshirish
curl -I https://google.com
```

## Keng tarqalgan xatolar

**Xato 1:** `tar` buyrug'ida `-f` bayrog'ini boshqa bayroqlardan oldin qo'yish.
- ❌ `tar -fczv archive.tar.gz folder`
- ✅ **Sabab:** `-f` har doim oxirida, bevosita arxiv fayli nomidan oldin turishi kerak! Chunki `-f` dan keyingi birinchi so'z fayl nomi deb qabul qilinadi. To'g'risi: `tar -czvf archive.tar.gz ...`

## Mashq/topshiriq

1. **(Oson)** `curl -s https://httpbin.org/ip` buyrug'ini ishga tushirib, JSON formatidagi javobni ko'ring.
2. **(O'rtacha)** Sinov uchun 3 ta fayl yarating va ularni `test_archive.tar.gz` fayliga arxivlang.
3. **(Qiyin)** Arxivni `mkdir /tmp/test_unpack` papkasi ochib, o'sha papka ichiga oching (`tar -xzvf test_archive.tar.gz -C /tmp/test_unpack`).

## Qisqacha xulosa

`tar -czvf` arxivlaydi, `tar -xzvf` ochadi. `wget` fayllarni yuklaydi, `curl` esa veb-saytlar va API lar bilan muloqot qilishning standart vositasidir.

## Bog'liq

- Oldingi dars: [4.1. APT va DPKG paket boshqaruvi](4.1-apt-va-dpkg-paket-boshqaruvi.md)
- Keyingi dars: [5.1. Systemd va systemctl boshqaruvi](../05-bob-systemd-cron/5.1-systemd-va-systemctl-servislar.md)
"""
            }
        ]
    },
    {
        "dir": "05-bob-systemd-cron",
        "title": "05. Systemd Servislar va Avtomatlashtirish (Cron)",
        "lessons": [
            {
                "fn": "5.1-systemd-va-systemctl-servislar.md",
                "name": "5.1. Systemd va systemctl boshqaruvi (Servislar, daemon-reload, enable/start)",
                "content": """# Systemd va systemctl boshqaruvi

## Bu darsda nimalarni o'rganasiz

- Systemd tizim va servislar menejeri arxitekturasi (PID 1)
- `systemctl` yordamida xizmatlarni boshqarish: start, stop, restart, reload, status
- Avtomatik yuklanish (Autostart on boot): `enable` vs `disable`
- Servis holatlarini to'g'ri o'qish (Active, Inactive, Failed)

## Nazariy qism

### 1. Systemd Nima va Nega U Muhim?

Kompyuter yoki server yoqilganda, Linux yadrosi birinchi bo'lib **Systemd (PID 1)** dasturini ishga tushiradi. Qolgan barcha fon xizmatlari (Nginx, PostgreSQL, Docker, Telegram botlar, SSH server) aynan Systemd tomonidan tartib bilan ishga tushiriladi va nazorat qilinadi.

Agar biror servis xatolik tufayli to'xtab qolsa (crash), Systemd uni avtomatik qayta ishga tushiradi (Restart policy).

```
                        Linux Yadrosi (Kernel)
                                  │
                          systemd (PID 1)
           ┌──────────────────────┼──────────────────────┐
    ssh.service             nginx.service          mybot.service
 (Tarmoqdan kirish)       (Veb-sayt xizmati)      (Telegram botimiz)
```

### 2. `start` vs `enable` — Muhim Farq

Boshlovchilar eng ko'p chalkashtiradigan ikki buyruq:
- **`sudo systemctl start nginx`** — Servisni **HOZIR, SHU ZAXOTI** ishga tushiradi (lekin server o'chib-yonsa o'zi yoqilmaydi).
- **`sudo systemctl enable nginx`** — Servisni server **O'CHIB-YONGANDA AVTOMATIK** ishga tushadigan qilib tizimga ulaydi (Symlink yaratadi).
- **`sudo systemctl enable --now nginx`** — Ham hozir ishga tushiradi, ham avtoyuklanishga qo'shadi!

## Amaliy misol

```bash
# 1. Nginx yoki SSH servisining to'liq holatini ko'rish
sudo systemctl status ssh

# 2. Servisni qayta ishga tushirish (Restart)
sudo systemctl restart ssh

# 3. Servisni to'xtatmasdan konfiguratsiyani yangilash (Reload)
sudo systemctl reload nginx

# 4. Tizimda ishlamay qolgan (Failed) servislarni topish
systemctl --failed

# 5. Yangi servis fayli yozilganda systemd keshini yangilash
sudo systemctl daemon-reload
```

## Keng tarqalgan xatolar

**Xato 1:** `.service` faylini o'zgartirgandan keyin `daemon-reload` qilmaslik.
- ❌ Servis faylini tahrirlab, to'g'ridan-to'g'ri `systemctl restart` berish.
- ✅ **Sabab:** `Warning: The unit file changed on disk.` xabari chiqadi. Systemd fayllarni keshda saqlaydi. Har qanday o'zgarishdan keyin `sudo systemctl daemon-reload` kiritish shart!

## Mashq/topshiriq

1. **(Oson)** `sudo systemctl status ssh` buyrug'ini ishga tushirib, SSH server ishlayotganini (active / running) tasdiqlang.
2. **(O'rtacha)** `systemctl list-units --type=service --state=running` orqali ayni paytda serveringizda ishlayotgan barcha xizmatlar ro'yxatini ko'ring.
3. **(Qiyin)** `systemctl is-enabled ssh` va `systemctl is-active ssh` buyruqlarining chiqishini tahlil qiling.

## Qisqacha xulosa

Systemd server xizmatlarining boshqaruvchisi. `start`/`stop` hozirgi holatni, `enable`/`disable` esa server qayta yongandagi holatni boshqaradi. `daemon-reload` o'zgarishlarni kuchga kiritadi.

## Bog'liq

- Oldingi dars: [4.2. Arxivlar va tarmoq orqali yuklash](../04-bob-paketlar/4.2-arxivlar-va-yuklab-olish-curl-wget-tar.md)
- Keyingi dars: [5.2. Shaxsiy systemd servis yaratish](5.2-shaxsiy-systemd-servis-yaratish.md)
"""
            },
            {
                "fn": "5.2-shaxsiy-systemd-servis-yaratish.md",
                "name": "5.2. Shaxsiy systemd servis yaratish (Python/Django/Bot misolida)",
                "content": """# Shaxsiy systemd servis yaratish (Python/Django/Bot)

## Bu darsda nimalarni o'rganasiz

- Nega production muhitida dasturlarni `nohup` emas, Systemd servisi sifatida yurgizish kerak
- `.service` fayli anatomiyasi: `[Unit]`, `[Service]`, `[Install]` bo'limlari
- `Restart=always`, `RestartSec`, `EnvironmentFile` parametrlarining ishlashi
- Python/Django yoki Aiogram Telegram bot uchun to'liq ishchi servis faylini yozish va ishga tushirish

## Nazariy qism

### 1. Nega Aynan Systemd Servis?

Terminalda `python3 bot.py &` qilib qo'yilsa, botda xato yuz berganda u o'chib qoladi va siz bilmaysiz.
Systemd servisi sifatida sozlanganda:
1. Server o'chib-yonsa, bot **avtomatik qayta yoqiladi**.
2. Dastur xato berib to'xtasa, Systemd uni 5 soniyada **o'zi qayta tiriltiradi**.
3. Barcha xatolar va loglar markazlashgan `journalctl` tizimida saqlanadi.

### 2. `.service` Fayli Tuzilishi

Barcha shaxsiy servislar `/etc/systemd/system/` katalogida saqlanadi.

```ini
[Unit]
Description=Yordamchi Sayt Backend API
After=network.target postgresql.service

[Service]
Type=simple
User=shamsiddin
Group=shamsiddin
WorkingDirectory=/opt/yordamchi/Yordamchisayt/backend_py
EnvironmentFile=/opt/yordamchi/Yordamchisayt/backend_py/.env
ExecStart=/opt/yordamchi/Yordamchisayt/backend_py/.venv/bin/python main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### Bo'limlar tahlili:
- **`[Unit]`**:
  - `Description`: Servis haqida qisqa ma'lumot.
  - `After=network.target`: Tarmoq to'liq ulangandan va baza yoqilgandan keyingina bu servisni yoqish.
- **`[Service]`**:
  - `User`/`Group`: Servis root emas, xavfsiz oddiy foydalanuvchi nomidan ishlaydi.
  - `WorkingDirectory`: Dasturning asosiy papkasi.
  - `ExecStart`: Dasturni ishga tushiruvchi **ABSOLYUT** buyruq (virtual muhitdagi python yo'li).
  - `Restart=always`: Har qanday holatda o'chib qolsa, darhol qayta yoqish.
  - `RestartSec=5`: Qayta yoqishdan oldin 5 soniya kutish.
- **`[Install]`**:
  - `WantedBy=multi-user.target`: Ko'p foydalanuvchili standart tizim rejimida yuklanish.

## Amaliy misol

Qadamma-qadam shaxsiy servisni ishga tushiramiz:

```bash
# 1. Servis faylini yaratish
sudo nano /etc/systemd/system/mybot.service

# 2. Systemd konfiguratsiyasini yangilash
sudo systemctl daemon-reload

# 3. Servisni yoqish va avtoyuklanishga qo'shish
sudo systemctl start mybot
sudo systemctl enable mybot

# 4. Holatini tekshirish
sudo systemctl status mybot
```

## Keng tarqalgan xatolar

**Xato 1:** `ExecStart` da nisbiy yo'l yoki faqat `python3` deb yozish.
- ❌ `ExecStart=python3 main.py`
- ✅ **Sabab:** Systemd muhitida `$PATH` cheklangan bo'ladi. Har doim to'liq absolyut yo'llarni yozing: `ExecStart=/home/shamsiddin/project/.venv/bin/python /home/shamsiddin/project/main.py`.

## Mashq/topshiriq

1. **(Oson)** `/etc/systemd/system/` papkasini ochib, ichidagi mavjud servis fayllari nomlarini ko'ring.
2. **(O'rtacha)** Sinov uchun har 10 soniyada sana yozib turadigan oddiy Python skripti uchun `.service` faylini yozing.
3. **(Qiyin)** Servisni ishga tushiring, so'ng `pkill -9 python3` orqali jarayonni majburan o'ldiring va Systemd uni 5 soniyada yana qayta yoqqanini `systemctl status` orqali tekshiring!

## Qisqacha xulosa

Productiondagi barcha Python, Django va Bot loyihalari `/etc/systemd/system/` da `.service` fayl sifatida boshqariladi. `Restart=always` va to'liq absolyut yo'llar xizmatning 24/7 barqaror ishlashini kafolatlaydi.

## Bog'liq

- Oldingi dars: [5.1. Systemd va systemctl boshqaruvi](5.1-systemd-va-systemctl-servislar.md)
- Keyingi dars: [5.3. Journalctl loglar va Crontab avtomatlashtirish](5.3-journalctl-loglar-crontab.md)
"""
            },
            {
                "fn": "5.3-journalctl-loglar-crontab.md",
                "name": "5.3. Journalctl bilan loglarni tahlil qilish va Crontab avtomatlashtirish",
                "content": """# Journalctl bilan loglarni tahlil qilish va Crontab avtomatlashtirish

## Bu darsda nimalarni o'rganasiz

- `journalctl` yordamida systemd xizmatlarining loglarini real vaqtda o'qish
- Vaqt bo'yicha (`--since`), xatolik darajasi bo'yicha (`-p err`) loglarni filtrlash
- **Crontab** nima va uning 5 ta pozitsiyali vaqt sintaksisi
- Rejalashtirilgan zaxira nusxalash (Backup) va davriy skriptlarni sozlash

## Nazariy qism

### 1. `journalctl` — Markazlashgan Tizim Loglari

Systemd boshqarayotgan barcha servislar va tizim yadrosi loglari binar jurnalda saqlanadi. `journalctl` ularni qulay o'qish imkonini beradi:
- `-u unit_nomi` — Faqat ko'rsatilgan servis loglari.
- `-f` (follow) — Real vaqtda jonli kuzatish (xuddi `tail -f` kabi).
- `-n 50` — Oxirgi 50 ta qator.
- `--since "1 hour ago"` — Oxirgi 1 soatdagi voqealar.
- `-p err` — Faqat xatoliklar (Priority: emerg, alert, crit, err, warning, notice, info, debug).

### 2. Crontab — Vaqt Bo'yicha Rejalashtiruvchi

Crontab har qanday vazifani belgilangan vaqtda (har daqiqa, har kecha, har hafta) avtomatik ishga tushirish uchun xizmat qiladi.

```
┌───────────── Daqiqa (0 - 59)
│ ┌────────────── Soat (0 - 23)
│ │ ┌─────────────── Oyning kuni (1 - 31)
│ │ │ ┌──────────────── Oy (1 - 12)
│ │ │ │ ┌───────────────── Hafta kuni (0 - 7, 0 va 7 = Yakshanba)
│ │ │ │ │
* * * * *  /bajarilishi/kerak/bo'lgan/buyruq
```

### Mashhur Cron intervallari:
- `* * * * *` — Har daqiqada
- `*/15 * * * *` — Har 15 daqiqada bir marta
- `0 3 * * *` — Har kecha soat 03:00 da (Zaxira nusxalar uchun eng ma'qul vaqt)
- `0 9 * * 1` — Har dushanba soat 09:00 da
- `@reboot` — Server yoqilganda bir marta

## Amaliy misol

```bash
# 1. Shaxsiy botimizning loglarini jonli kuzatish
sudo journalctl -u mybot.service -f

# 2. Bugun ertalabdan beri bo'lgan barcha xatoliklarni ko'rish
sudo journalctl -u nginx --since today -p err

# 3. Foydalanuvchi crontab jadvalini tahrirlash
crontab -e

# Crontab fayli ichiga yozamiz:
# Har kuni tuni soat 02:30 da ma'lumotlar bazasidan zaxira olish:
# 30 2 * * * /opt/scripts/backup_db.sh >> /var/log/backup.log 2>&1

# 4. Mavjud cron vazifalarini ko'rish
crontab -l
```

## Keng tarqalgan xatolar

**Xato 1:** Crontab ichida to'liq yo'llarni yozmaslik.
- ❌ `0 3 * * * python3 backup.py`
- ✅ **Sabab:** Cron juda cheklangan muhitda ishlaydi, `python3` yoki `backup.py` qayerda ekanini bilmay qoladi. Doimo absolyut yo'llarni yozing: `0 3 * * * /usr/bin/python3 /home/shamsiddin/backup.py`.

## Mashq/topshiriq

1. **(Oson)** `sudo journalctl -n 20` orqali tizimning oxirgi 20 ta logini o'qing.
2. **(O'rtacha)** `crontab -l` orqali joriy foydalanuvchida qanday rejali vazifalar borligini tekshiring.
3. **(Qiyin)** Har soatning 30-daqiqasida ishlaydigan cron ifodasini yozing (Javob: `30 * * * *`).

## Qisqacha xulosa

`journalctl -u service -f` xatoliklarni aniqlashning 1-raqamli vositasidir. `crontab` esa muntazam zaxira olish va davriy vazifalarni avtomatlashtiradi.

## Bog'liq

- Oldingi dars: [5.2. Shaxsiy systemd servis yaratish](5.2-shaxsiy-systemd-servis-yaratish.md)
- Keyingi dars: [6.1. Tarmoq konfiguratsiyasi va diagnostikasi](../06-bob-tarmoq-ssh-xavfsizlik/6.1-tarmoq-konfiguratsiyasi-diagnostika.md)
"""
            }
        ]
    },
    {
        "dir": "06-bob-tarmoq-ssh-xavfsizlik",
        "title": "06. Tarmoq (Networking), SSH va Server Xavfsizligi",
        "lessons": [
            {
                "fn": "6.1-tarmoq-konfiguratsiyasi-diagnostika.md",
                "name": "6.1. Tarmoq konfiguratsiyasi va diagnostikasi (ip, ss, ping, curl, dig, Netplan)",
                "content": """# Tarmoq konfiguratsiyasi va diagnostikasi (ip, ss, Netplan)

## Bu darsda nimalarni o'rganasiz

- Ubuntu 24.04 da tarmoqni boshqarish: **Netplan** (`/etc/netplan/`) va `iproute2` vositalari
- IP manzil, tarmoq interfeyslari va shlyuz (Gateway)ni aniqlash (`ip a`, `ip r`)
- Ochiq portlar va tinglanayotgan servislarni tahlil qilish (`ss -tulpn`)
- Tarmoq aloqasi va DNS diagnostikasi (`ping`, `curl`, `dig`, `traceroute`)

## Nazariy qism

### 1. `ifconfig` Eskirdi — Yangi Standart: `iproute2`

Zamonaviy Linuxda eski `net-tools` (`ifconfig`, `netstat`, `route`) to'plami eskirgan deb topilgan. Ularning o'rniga tezkor va zamonaviy buyruqlar ishlatiladi:
- `ifconfig` ➔ **`ip a`** (ip address)
- `route -n` ➔ **`ip r`** (ip route)
- `netstat -tulpn` ➔ **`ss -tulpn`** (Socket Statistics)

### 2. Ochiq Portlar va Socketlar (`ss -tulpn`)

Serverda qaysi dastur qaysi portda so'rovlarni kutayotganini (Listening) aniqlash:

```bash
sudo ss -tulpn
```
- `-t` — TCP portlar
- `-u` — UDP portlar
- `-l` — Faqat tinglanayotgan (Listening) portlar
- `-p` — Qaysi dastur va PID ekanligini ko'rsatish
- `-n` — Port nomini emas, sonini ko'rsatish (`80`, `443`, `22`, `5432`)

### 3. Ubuntu 24.04 Netplan Konfiguratsiyasi

Ubuntu tarmoq sozlamalarini `/etc/netplan/*.yaml` fayllari orqali boshqaradi:

```yaml
network:
  version: 2
  renderer: networkd
  ethernets:
    eth0:
      dhcp4: true
```

Sozlamalarni qo'llash: `sudo netplan apply`

## Amaliy misol

```bash
# 1. Barcha tarmoq interfeyslari va IP manzillarini ko'rish
ip -br a

# 2. Serverda ochiq barcha portlar va dasturlarni ko'rish
sudo ss -tulpn

# 3. Google DNS bilan aloqa bormi tekshirish
ping -c 4 8.8.8.8

# 4. Domen DNS IP sini aniqlash
dig +short y.wstore.uz

# 5. Muayyan port ochiq ekanini tekshirish (masalan PostgreSQL 5432)
nc -zv 127.0.0.1 5432
```

## Keng tarqalgan xatolar

**Xato 1:** `ss` buyrug'ini `sudo`siz ishlatib, dastur nomlarini ko'ra olmaslik.
- ❌ Oddiy foydalanuvchi sifatida `ss -tulpn` bajarsangiz, PID va Process ustuni bo'sh chiqadi. Barcha dasturlarni ko'rish uchun `sudo ss -tulpn` qiling.

## Mashq/topshiriq

1. **(Oson)** `ip -br a` buyrug'i orqali asosiy tarmoq kartangiz (masalan `eth0` yoki `wlan0`)ning IP manzilini toping.
2. **(O'rtacha)** `sudo ss -tulpn | grep 22` orqali SSH porti ochiq ekanini tasdiqlang.
3. **(Qiyin)** `dig google.com` orqali Google serverlarining A-yozuvlari (IP manzillari) ro'yxatini chiqaring.

## Qisqacha xulosa

`ip a` IP manzillarni, `ss -tulpn` ochiq portlar va ularga bog'langan dasturlarni ko'rsatadi. `ping` va `dig` tarmoq va DNS diagnostikasining asosiy qurollaridir.

## Bog'liq

- Oldingi dars: [5.3. Journalctl loglar va Crontab avtomatlashtirish](../05-bob-systemd-cron/5.3-journalctl-loglar-crontab.md)
- Keyingi dars: [6.2. SSH xavfsiz boshqaruvi va kalitlar](6.2-ssh-boshqaruvi-va-kalitlar.md)
"""
            },
            {
                "fn": "6.2-ssh-boshqaruvi-va-kalitlar.md",
                "name": "6.2. SSH xavfsiz boshqaruvi va kalitlar (ssh-keygen, ssh-copy-id, SSH config, SCP, Rsync)",
                "content": """# SSH xavfsiz boshqaruvi va kalitlar (ssh-keygen, config, scp)

## Bu darsda nimalarni o'rganasiz

- SSH (Secure Shell, Port 22) qanday ishlashi va simmetrik/asimmetrik shifrlash
- Zamonaviy **Ed25519** va RSA kalitlarini yaratish (`ssh-keygen`)
- Parolsiz xavfsiz kirishni sozlash (`ssh-copy-id`)
- `~/.ssh/config` fayli orqali bitta qisqa nom bilan serverlarga ulanish
- Serverlar o'rtasida tezkor va xavfsiz fayl almashish (`scp`, `rsync`)

## Nazariy qism

### 1. Parol vs SSH Kalit

Parol bilan kirish zaif hisoblanadi (Brute-force hujumlari orqali parolni topish mumkin).
**SSH Kalitlar juftligi:**
1. **Private Key (Maxfiy kalit):** Faqat sizning shaxsiy kompyuteringizda saqlanadi (`~/.ssh/id_ed25519`). Uni HECH KIMGA bermang!
2. **Public Key (Ochiq kalit):** Serverga (`~/.ssh/authorized_keys` fayliga) joylashtiriladi (`id_ed25519.pub`).

```
  Shaxsiy Kompyuter                          Masofaviy Server
┌────────────────────┐   SSH Ulanish (Port 22)   ┌──────────────────────┐
│  id_ed25519 (MAXFIY)│ ────────────────────────► │ authorized_keys (OCHIQ)│
└────────────────────┘    Matematik tasdiq       └──────────────────────┘
                          (Parol yuborilmaydi)
```

### 2. `~/.ssh/config` — Hayotni yengillashtiruvchi vosita

Har safar `ssh -i ~/.ssh/oracle_key opc@82.70.41.85 -p 22` deb yozish o'rniga, shaxsiy kompyuteringizdagi `~/.ssh/config` fayliga yozib qo'yasiz:

```ini
Host yordamchi
    HostName 82.70.41.85
    User opc
    IdentityFile ~/.ssh/oracle_key
```

Shundan so'ng terminalda shunchaki:
```bash
ssh yordamchi
```
deb yozish kifoya!

## Amaliy misol

```bash
# 1. Zamonaviy, eng kuchli Ed25519 kalitini yaratish
ssh-keygen -t ed25519 -C "shamsiddin-laptop"

# 2. Ochiq kalitni yangi serverga bitta buyruq bilan nusxalash
ssh-copy-id -i ~/.ssh/id_ed25519.pub user@server_ip

# 3. SCP orqali faylni serverga yuborish
scp my_project.zip yordamchi:/opt/

# 4. Rsync orqali faqat o'zgargan fayllarni sinxronlash (juda tez)
rsync -avz --progress ./src/ yordamchi:/opt/my_project/src/
```

## Keng tarqalgan xatolar

**Xato 1:** Maxfiy kalit ruxsatlarini ochiq qoldirish (`Permissions are too open`).
- ❌ `WARNING: UNPROTECTED PRIVATE KEY FILE!`
- ✅ **Sabab:** SSH maxfiy kalit boshqalar uchun o'qishga ochiq bo'lsa, xavfsizlik yuzasidan ishlashdan bosh tortadi. Ruxsatni to'g'rilang: `chmod 600 ~/.ssh/id_ed25519` va `chmod 700 ~/.ssh`.

**Xato 2:** Maxfiy kalitni (`id_ed25519`) ochiq kalit (`.pub`) o'rniga serverga nusxalash.
- ❌ Maxfiy kalitni serverga yubormang! Serverga faqat `.pub` bilan tugovchi ochiq kalit boradi.

## Mashq/topshiriq

1. **(Oson)** `ls -la ~/.ssh` orqali o'z kompyuteringizdagi SSH kalitlar ro'yxatini ko'ring.
2. **(O'rtacha)** `~/.ssh/config` faylini ochib, uning tuzilishini ko'rib chiqing.
3. **(Qiyin)** `scp` orqali sinov faylini serverga yuklab, keyin uni serverdan qayta yuklab olishni sinab ko'ring.

## Qisqacha xulosa

SSH kalitlar xavfsiz va parolsiz ishlash standarti. `~/.ssh/config` ulanishlarni soddalashtiradi, `scp` va `rsync` esa fayllarni bir zumda uzatadi.

## Bog'liq

- Oldingi dars: [6.1. Tarmoq konfiguratsiyasi va diagnostikasi](6.1-tarmoq-konfiguratsiyasi-diagnostika.md)
- Keyingi dars: [6.3. Server xavfsizligi va UFW Firewall](6.3-xavfsizlik-va-ufw-firewall.md)
"""
            },
            {
                "fn": "6.3-xavfsizlik-va-ufw-firewall.md",
                "name": "6.3. Server xavfsizligi, UFW Firewall va Fail2ban (Ubuntu 24.04)",
                "content": """# Server xavfsizligi, UFW Firewall va Fail2ban (Ubuntu 24.04)

## Bu darsda nimalarni o'rganasiz

- Linux serverlariga qilinadigan asosiy xakerlik hujumlari (Brute-force, port scanning)
- **UFW (Uncomplicated Firewall)** yordamida portlarni to'liq himoyalash
- **Fail2ban** orqali parolni noto'g'ri tergan tajovuzkor IP larni avtomatik bloklash
- SSH serverni qat'iy xavfsizlash qoidalari (`sshd_config`)

## Nazariy qism

### 1. Server Xavfsizligining "Oltin Qoidalari"

Har qanday yangi Linux server ochilganda quyidagi 4 ta qoida darhol joriy etilishi shart:

```
┌────────────────────────────────────────────────────────────────────────┐
│ 1. Root orqali to'g'ridan-to'g'ri SSH ga kirishni TAQIQLASH            │
│ 2. Parol bilan kirishni o'chirib, FAQAT SSH KALIT bilan kirishni yoqish │
│ 3. UFW Firewall: Barcha kiruvchi portlarni yopib, faqat kerakligini ochish│
│ 4. Fail2ban: Botnet va skanerlarni avtomatik qora ro'yxatga kiritish    │
└────────────────────────────────────────────────────────────────────────┘
```

### 2. UFW (Uncomplicated Firewall) Sozlash

UFW — iptables/nftables ustiga qurilgan juda sodda va ishonchli devordir.

Xavfsiz sozlash ketma-ketligi:
```bash
# 1. Standart qoidalar: kiruvchilarni BLOKLASH, chiquvchilarga RUXSAT
sudo ufw default deny incoming
sudo ufw default allow outgoing

# 2. ENG MUHIM: Avval SSH ga ruxsat bering (yo'qsa o'zingiz serverdan haydalasiz!)
sudo ufw allow 22/tcp

# 3. Veb portlarga ruxsat berish
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 4. Firewallni yoqish
sudo ufw enable
```

### 3. SSH Konfiguratsiyasini Xavfsizlash

Fayl: `/etc/ssh/sshd_config` yoki `/etc/ssh/sshd_config.d/50-cloud-init.conf`
- `PermitRootLogin no` — Root kirishi taqiqlanadi.
- `PasswordAuthentication no` — Parol bilan kirish o'chiriladi (faqat SSH kalit).

Sozlamadan so'ng: `sudo systemctl restart ssh`

## Amaliy misol

```bash
# 1. UFW holati va barcha qoidalarni raqamlari bilan ko'rish
sudo ufw status numbered

# 2. Muayyan IP manzilga PostgreSQL portiga kirishga ruxsat berish
sudo ufw allow from 82.70.41.85 to any port 5432 proto tcp

# 3. Qoidani raqami bo'yicha o'chirish
sudo ufw delete 3

# 4. Fail2ban holatini tekshirish (qancha xaker bloklanganini ko'rish)
sudo fail2ban-client status sshd
```

## Keng tarqalgan xatolar

**Xato 1:** UFW ni yoqishdan oldin SSH portiga ruxsat bermaslik.
- ❌ `sudo ufw default deny incoming` va `sudo ufw enable` qilib, SSH ga ruxsat bermaslik.
- ✅ **Natija:** Server sessiyasi darhol uziladi va unga qayta ulanib bo'lmaydi (faqat hosting konsoli orqali kirishga to'g'ri keladi). Doimo avval `sudo ufw allow 22/tcp` bering!

**Xato 2:** Parol bilan kirishni o'chirishdan oldin SSH kalit ishlayotganini tekshirmaslik.
- ❌ Kalit ishlamasdan turib `PasswordAuthentication no` qilib qo'yish.
- ✅ **Tavsiya:** Yangi SSH oynasida kirib ko'rib, kalit bilan kirayotganiga 100% ishonch hosil qilmaguncha, joriy oynani yopmang!

## Mashq/topshiriq

1. **(Oson)** `sudo ufw status verbose` orqali kompyuteringiz yoki serveringizda firewall holatini ko'ring.
2. **(O'rtacha)** `/etc/ssh/sshd_config` faylini `less` orqali ko'zdan kechirib, xavfsizlik parametrlarini o'rganing.
3. **(Qiyin)** UFW da port ochish, holatini tekshirish va uni qayta o'chirish amallarini to'liq bajaring.

## Qisqacha xulosa

Server xavfsizligi UFW firewall orqali faqat kerakli portlarni ochiq qoldirish, parolsiz SSH kalitlaridan foydalanish va Fail2ban orqali botnet hujumlarini bloklashga tayanadi.

## Bog'liq

- Oldingi dars: [6.2. SSH xavfsiz boshqaruvi va kalitlar](6.2-ssh-boshqaruvi-va-kalitlar.md)
"""
            }
        ]
    }
]

def main():
    os.makedirs(BASE_DIR, exist_ok=True)
    print(f"Boshlandi: {BASE_DIR}")
    
    mundarija_lines = [
        "# Linux & Ubuntu 24.04 LTS darsligi — Barcha mavzular (to'liq, 7 bo'lim, 17 dars)",
        "",
        "_Ushbu darslik noldan boshlab Ubuntu 24.04 LTS (Noble Numbat) operatsion tizimi, Linux yadrosi, fayl tizimi ierarxiyasi, ruxsatlar, jarayonlar monitoringi, APT paket menejeri, Systemd servislar, Crontab avtomatlashtirish, tarmoq va SSH/UFW xavfsizligigacha bo'lgan barcha professional bilimlarni qamrab oladi._",
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
            print(f"  ✅ Yaratildi [{total_lessons}]: {chap['dir']}/{lesson['fn']} ({len(lesson['content'])} bayt)")

        mundarija_lines.append("")

    mundarija_path = os.path.join(BASE_DIR, "00-linux-darslik-mundarija.md")
    with open(mundarija_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(mundarija_lines))

    print(f"\n🎉 Muvaffaqiyatli yakunlandi! Jami {total_lessons} ta mukammal Linux darsi va mundarija fayli yaratildi.")

if __name__ == '__main__':
    main()
