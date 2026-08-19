# 🗺️ Linux va Ubuntu 24.04 — Vizual Xaritalar, Daraxtlar va Tushunchalar Qo'llanmasi

> **Ushbu qo'llanmaning maqsadi:** Linuxdagi barcha murakkab atamalar (terminlar), fayllar joylashuvi, ruxsatlar, jarayonlar va tarmoq tushunchalarini **chizmalar, daraxtlar (ASCII trees) va oddiy hayotiy analogiyalar** orqali 100% vizual tushunib olish.

---

## 🌳 1-QISM: Linux Tizimining Katta Xaritasi (Big Picture)

Linux qanday qatlamlardan iborat va siz yozgan buyruq qanday qilib apparaturagacha yetib boradi?

```
┌─────────────────────────────────────────────────────────────────────────┐
│ 👤 SIZ (Dasturchi / Foydalanuvchi)                                      │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │ Buyruq yozasiz (masalan: `ls -la`)
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 🖥️ TERMINAL (Oyna / Ekran) ➔ SHELL (Bash / Zsh - Tarjimon)             │
│   - Matnni tahlil qiladi, buyruqni topadi va yadroga uzatadi            │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │ Tizim chaqiruvi (System Call)
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 🧠 LINUX YADROSI (Kernel - Tizimning "Miyya"si)                         │
│   ├── 🗂️ Fayl tizimi (Ext4, Btrfs) ➔ Fayllarni topadi va o'qiydi        │
│   ├── ⚡ Jarayonlar boshqaruvi ➔ CPU vaqtini taqsimlaydi               │
│   ├── 💾 Xotira menejeri ➔ RAM'dan joy ajratadi (va bo'shatadi)        │
│   └── 🌐 Tarmoq steki (TCP/IP) ➔ Internet paketlarini uzatadi          │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │ Elektr signallari
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ ⚙️ APPARATURA (Hardware: Intel/AMD CPU, RAM, NVMe SSD, Tarmoq kartasi)   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📂 2-QISM: Linux Fayl Daraxti — "Katta Shaharcha" Analogiyasi

Windowsdagi kabi `C:`, `D:` disklar yo'q. Hamma narsa **`/` (Ildiz / Root)** dan shoxlanib ketadi:

```
                                  / (ILDIZ - Shahar markazi)
  ┌──────────────┬──────────────┬──────────────┬──────────────┬──────────────┬──────────────┐
  │              │              │              │              │              │              │
 /bin           /etc           /home          /var           /opt           /tmp           /root
 (Asboblar)  (Sozlamalar)    (Aholi uyi)    (Ombor/Loglar) (Zavodlar)     (Chiqindi)    (Hokim uyi)
```

### 🏢 Har bir papkaning oddiy tildagi ma'nosi:

```
📁 / (Slash / Root)
│   └── Butun koinotning boshi. Barcha disklar va papkalar shu yerga ulanadi.
│
├── 📁 /home ➔ "Aholi turar-joy massivi"
│   └── /home/shamsiddin ➔ Sizning shaxsiy xonangiz. Faqat sizga tegishli fayllar (Desktop, Downloads).
│
├── 📁 /root ➔ "Prezident / Superadmin xonasi"
│   └── Root foydalanuvchisining shaxsiy uyi. Oddiy odamlar bu yerga kira olmaydi.
│
├── 📁 /etc ➔ "Boshqaruv pulti / Sozlamalar arxivi"
│   ├── /etc/nginx/nginx.conf  ➔ Veb-server sozlamalari
│   ├── /etc/ssh/sshd_config   ➔ SSH kirish sozlamalari
│   └── /etc/passwd            ➔ Barcha foydalanuvchilar ro'yxati
│
├── 📁 /var ➔ "Kundalik o'zgaruvchan ombor" (Variable data)
│   ├── /var/log/              ➔ Tizim kundaliklari (Loglar, xatolar tarixi)
│   │   ├── /var/log/nginx/    ➔ Saytga kim kirdi, qanday xato bo'ldi
│   │   └── /var/log/syslog    ➔ Tizimning umumiy loglari
│   └── /var/www/              ➔ Sayt fayllari (HTML, JS, Media)
│
├── 📁 /opt ➔ "Qo'shimcha o'rnatilgan yirik loyihalar" (Optional)
│   └── /opt/yordamchi/        ➔ Masalan, bizning Yordamchi sayti kodi shu yerda turadi
│
├── 📁 /tmp ➔ "Vaqtinchalik xomaki qoralama" (Temporary)
│   └── Har qanday dastur vaqtincha fayl tashlaydi. Kompyuter o'chib-yonsa o'zi tozalanadi.
│
├── 📁 /bin & /usr/bin ➔ "Asosiy ish qurollari qutisi" (Binaries)
│   └── `python3`, `git`, `ls`, `mkdir`, `curl` kabi barcha buyruq dasturlari shu yerda turadi.
│
├── 📁 /dev ➔ "Uskunalar ko'rgazmasi" (Devices)
│   ├── /dev/sda, /dev/nvme    ➔ Qattiq disklar
│   └── /dev/null              ➔ "Qora tuynuk" (keraksiz chiqindini yutib yuboruvchi virtual manzil)
│
└── 📁 /proc & /sys ➔ "Tizimning ichki a'zolari rentgeni"
    └── Xotiradagi jonli holat (fayl ko'rinishida aks etadi): CPU, RAM holati.
```

---

## 🔐 3-QISM: Ruxsatlar (Permissions) — "Eshik Qulflari" Chizmasi

Terminalda `ls -l` yozganingizda chiqadigan belgilar nimani anglatadi?

```
                      rwx  r-x  r--
                      ──┬  ──┬  ──┬
                        │    │    └── 3. Boshqalar (Others - Dunyodagi barcha begona odamlar)
                        │    └─────── 2. Guruh (Group - Bir xonadagi hamkasblar)
                        └──────────── 1. Egasi (Owner / User - Faylni yaratgan shaxs)
```

### 🔢 3 ta asosiy harf va ularning raqamli kodi:

| Harf | Belgisi | Raqami | Nimaga ruxsat beradi? |
|:---:|:---:|:---:|---|
| **`r`** | **Read** | **`4`** | Faylni **o'qish** / Papka ichidagi fayllar ro'yxatini ko'rish |
| **`w`** | **Write** | **`2`** | Faylni **o'zgartirish** yoki o'chirish / Papkaga yangi fayl qo'shish |
| **`x`** | **Execute** | **`1`** | Skriptni **ishga tushirish** / Papka ichiga **kirish (`cd`)** |
| **`-`** | **Hech narsa** | **`0`** | Ruxsat yo'q |

### 🧮 Raqamlarni qo'shish formulasi:

```
  rwx  =  4 + 2 + 1  =  7  (Hamma narsaga ruxsat: O'qiydi + Yozadi + Ishga tushiradi)
  rw-  =  4 + 2 + 0  =  6  (O'qiydi va Yozadi, lekin dastur emas)
  r-x  =  4 + 0 + 1  =  5  (O'qiydi va Ishga tushiradi, lekin o'zgartira olmaydi)
  r--  =  4 + 0 + 0  =  4  (Faqat o'qiydi)
  ---  =  0 + 0 + 0  =  0  (Mutlaqo yopiq)
```

### 🛡️ Eng ko'p uchraydigan 3 ta standart:

```
┌───────────┬───────────────────┬────────────────────────────────────────────────────────┐
│ Raqam     │ Ko'rinishi        │ Qayerda ishlatiladi?                                   │
├───────────┼───────────────────┼────────────────────────────────────────────────────────┤
│ chmod 644 │ rw- r-- r--       │ Standart fayllar (Egasi o'zgartiradi, boshqalar o'qiydi)│
│ chmod 755 │ rwx r-x r-x       │ Standart papkalar va skriptlar (Hamma kiradi va o'qiydi)│
│ chmod 600 │ rw- --- ---       │ Maxfiy fayllar (.env, SSH kalitlar - Faqat egasi ko'radi)│
└───────────┴───────────────────┴────────────────────────────────────────────────────────┘
```

---

## ⚙️ 4-QISM: Jarayonlar (Processes) — "Oila Daraxti"

Linuxda dastur ishga tushganda unga **PID (Process ID)** raqami beriladi. Hamma jarayonlarning "bobosi" — **PID 1 (Systemd)** dir:

```
                           systemd (PID 1 - Bosh boshqaruvchi)
                                    │
         ┌──────────────────────────┼──────────────────────────┐
         │                          │                          │
    sshd (PID 820)             nginx (PID 1040)           postgres (PID 910)
  (SSH serveri)              (Veb-server ustasi)          (Ma'lumotlar bazasi)
         │                          │
    bash (PID 2300)            worker (PID 1041)
  (Sizning terminalingiz)      worker (PID 1042)
         │
    python3 main.py (PID 3150)
  (Siz ishga tushirgan bot)
```

### 🛑 Jarayonni to'xtatish signallari (Politsiya analogiyasi):

```
1. kill 3150  (SIGTERM - 15)
   └── "Iltimos, ishingizni xavfsiz saqlab, tinchgina yoping" (Xushmuomala)

2. kill -9 3150  (SIGKILL - 9)
   └── "Darhol to'xtat! Gaplashib o'tirilmaydi!" (Majburiy o'ldirish)
```

---

## 🌐 5-QISM: Tarmoq, Portlar va UFW — "Ko'p qavatli bino" Analogiyasi

Tasavvur qiling, server — bu bitta katta mehmonxona:
- **IP manzil (`82.70.41.85`)** ➔ Mehmonxonaning ko'chadagi **aniq manzili**.
- **Portlar (`22`, `80`, `443`, `5432`)** ➔ Binodagi **alohida xonalar raqamlari**.
- **UFW (Firewall)** ➔ Binoga kirishdagi **qattiqqo'l qorovul**.

```
                        🌐 INTERNET
                            │
                            ▼
              ┌──────────────────────────┐
              │ 🛡️ UFW FIREWALL (Qorovul)│
              │  "Kimga qayerga ruxsat?" │
              └─────────────┬────────────┘
                            │
       ┌────────────────────┼────────────────────┬────────────────────┐
       ▼ [Port 22 - SSH]    ▼ [Port 80/443 HTTP] ▼ [Port 5432 DB]     ▼ [Port 9999 Noma'lum]
  ┌──────────┐         ┌──────────┐         ┌──────────┐         ┌──────────┐
  │ SSHD     │         │ NGINX    │         │ POSTGRES │         │  BLOK!   │
  │ (Admin   │         │ (Saytga  │         │ (Ichki   │         │ ❌ Yopiq │
  │ kirishi) │         │ tashrif) │         │ baza)    │         │          │
  └──────────┘         └──────────┘         └──────────┘         └──────────┘
```

---

## 🔄 6-QISM: Systemd Servisining Hayot Sikli

Dasturingiz (masalan Telegram bot) server o'chib-yonsa ham, xato berib to'xtasa ham **o'zi avtomatik qayta yonishi** uchun Systemd xizmatiga aylanadi:

```
         sudo systemctl daemon-reload (Yangi sozlamani xotiraga olish)
                      │
                      ▼
         sudo systemctl enable mybot  (Kompyuter yoqilganda avtomatik yonish)
                      │
                      ▼
         sudo systemctl start mybot   (Hozir ishga tushirish)
                      │
                      ▼
      ┌───────────────────────────────┐
      │  🟢 ACTIVE (RUNNING)           │ ◄─── Bot 24/7 ishlab turibdi
      └──────────────┬────────────────┘
                     │
         Xatolik yuz bersa (Crash)
                     │
                     ▼
      ┌───────────────────────────────┐
      │  🔄 Restart=always (5 soniya)  │ ──► Darhol qaytadan ACTIVE holatiga qaytaradi!
      └───────────────────────────────┘
```

---

## 📑 7-QISM: Eng Ko'p Ishlatiladigan 30 ta Buyruqning Vizual Qomusi

| № | Buyruq | Hayotiy vazifasi | Qachon ishlatiladi? |
|:---:|---|---|---|
| 1 | **`pwd`** | Qayerdaman? | Hozir qaysi papkada turganingizni ko'rsatadi |
| 2 | **`ls -lah`** | Xonada nimalar bor? | Yashirin fayllar va o'lchamlari bilan to'liq ro'yxat |
| 3 | **`cd /manzil`** | Boshqa xonaga o'tish | Papkani almashtirish (`cd ..` = orqaga) |
| 4 | **`mkdir -p a/b`** | Yangi papkalar qurish | Ichma-ich papkalar zanjirini bittada ochish |
| 5 | **`touch fayl.txt`** | Bo'sh qog'oz olish | Yangi bo'sh fayl yaratish |
| 6 | **`cat fayl.txt`** | Matnni to'kib tashlash | Kichik fayl tarkibini ekranga chiqarish |
| 7 | **`less fayl.log`** | Kitobday sahifalab o'qish | Katta loglarni o'qish va qidirish (`q` bilan chiqish) |
| 8 | **`tail -f fayl.log`**| Jonli kamera monitoringi | Logga yangi yozuv tushishi bilan ekranda ko'rsatadi |
| 9 | **`cp -r a b`** | Nusxa ko'chirish | Papka va fayllarni nusxalash |
| 10 | **`mv a b`** | Joyini/nomini o'zgartirish | Faylni boshqa joyga ko'chirish yoki nomini o'zgartirish |
| 11 | **`rm -rf papka`** | Butunlay yo'q qilish | Papka va ichidagilarni o'chirish (Ehtiyot bo'ling!) |
| 12 | **`find . -name "*.py"`**| Izquvar qidiruvi | Fayllarni nomi yoki hajmi bo'yicha topish |
| 13 | **`grep -rn "kalit"`** | Kitob ichidan so'z qidirish | Kod yoki loglar ichidan matnni qator raqami bilan topish |
| 14 | **`chmod 755 fayl`** | Qulfni o'zgartirish | Faylga o'qish, yozish, ishga tushirish huquqini berish |
| 15 | **`chown user:group`**| Mulk egasini almashtirish | Faylning egasi va guruhini o'zgartirish |
| 16 | **`ps aux`** | Hozir kim nima qilyapti? | Barcha ishlayotgan jarayonlar ro'yxati |
| 17 | **`htop`** | Jonli asboblar paneli | CPU, RAM va jarayonlarni grafik interaktiv kuzatish |
| 18 | **`kill -9 PID`** | Majburiy to'xtatish | Qotib qolgan jarayonni xotiradan haydash |
| 19 | **`free -h`** | Qancha xotira qoldi? | Operativ xotira (RAM - `available`) holatini ko'rish |
| 20 | **`df -h`** | Qattiq disk to'ldimi? | Disk bo'limlarining bo'sh joy foizini ko'rish |
| 21 | **`du -sh *`** | Qaysi papka semirib ketdi?| Papkalar va fayllarning haqiqiy og'irligi |
| 22 | **`sudo apt update`** | Do'kon yangiliklarini bilish | Yangi paketlar versiyalari ro'yxatini yuklash |
| 23 | **`sudo apt install`**| Yangi uskuna sotib olish | Yangi dasturni o'rnatish |
| 24 | **`tar -czvf a.tar.gz`**| Chemodanga zichlab solish | Fayllarni arxivga siqish |
| 25 | **`tar -xzvf a.tar.gz`**| Chemodanni ochish | Arxivni chiqarish |
| 26 | **`systemctl status x`**| Xizmat sog'lommi? | Servis ishlayotgani yoki to'xtaganini tekshirish |
| 27 | **`systemctl restart x`**| Qayta o't oldirish | Servisni qayta ishga tushirish |
| 28 | **`journalctl -u x -f`**| Shifokor stetoskopik tahlili| Muayyan servis loglarini jonli o'qish |
| 29 | **`ip a`** | Mening manzilim qayerda? | Serverning IP manzillarini ko'rish |
| 30 | **`ss -tulpn`** | Qaysi eshiklar ochiq? | Ochiq portlar va ularga bog'langan dasturlar |

---

> 💡 **Maslahat:** Ushbu qo'llanmani xatcho'plarga saqlab qo'ying yoki Obsidian'da ochib, darslar davomida tushunarsiz termin chiqqanda chizmalarga qarang!
