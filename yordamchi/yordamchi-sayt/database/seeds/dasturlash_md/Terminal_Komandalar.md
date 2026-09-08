# 🐧 Linux Terminal Komandalar (Mukammal Qo'llanma)

> Unitib qo'yganingizda shu yerdan qarang. `Ctrl + F` bosib tezda qidiring.
> Barcha buyruqlar Ubuntu, Debian, Oracle Linux, CentOS, Arch va boshqa barcha Linux distributivlarida (Bash / Zsh) ishlaydi.

---

## 📍 Qayerdaman va Kimman?

```bash
pwd                              # Hozirgi to'liq yo'lni ko'rsatish (Print Working Directory)
whoami                           # Joriy tizim foydalanuvchisi nomi (masalan: opc, ubuntu, root)
hostname                         # Server yoki kompyuter nomi
uname -a                         # Linux yadrosi (kernel) va tizim arxitekturasi
```

---

## 📂 Papkaga o'tish (cd)

```bash
cd papka                         # Papkaga kirish (nisbiy yo'l)
cd Documents                     # Documents papkasiga o'tish
cd "Mening Loyiham"              # Bo'shliqli nom — qo'shtirnoq bilan!
cd papka1/papka2/papka3          # Ichma-ich papkaga (Linux'da / ishlatiladi, \ emas!)
cd /var/www/html                 # To'liq (absolyut) yo'l bilan ildizdan boshlab
cd ~                             # Foydalanuvchining Asosiy (Home) papkasiga (`/home/username`)
cd                               # Parametrsiz — xuddi shunday Home papkasiga o'tadi
cd -                             # Oxirgi bo'lgan oldingi papkaga qaytish (juda qulay!)
cd ..                            # 1 daraja yuqoriga (ota papkaga)
cd ../..                         # 2 daraja yuqoriga
cd ../../..                      # 3 daraja yuqoriga
cd /                             # Butun tizimning eng yuqori ildiziga (root /)
```

```
.    = hozirgi papka
..   = ota papka (bir daraja yuqori)
~    = joriy foydalanuvchi home papkasi (/home/user)
/    = tizim ildizi (root filesystem)
```

---

## 📋 Papka ichidagilarni ko'rish (ls)

```bash
ls                               # Oddiy fayl va papkalar ro'yxati
ls -l                            # Katta batafsil ro'yxat (huquqlar, egasi, hajm, sana)
ls -la                           # Yashirin fayllar (`.` bilan boshlanadigan) bilan birga
ls -lh                           # Hajmlarni tushunarli ko'rsatish (KB, MB, GB)
ls -lt                           # O'zgartirilgan vaqti bo'yicha (eng yangilari tepada)
ls -lrt                          # Vaqti bo'yicha teskari (eng yangilari pastda — qulay!)
ls -lS                           # Fayl hajmi bo'yicha (eng kattasi tepada)
ls -R                            # Barcha ichki papkalari bilan birga (rekursiv)
ls *.py                          # Faqat .py fayllarni ko'rsatish
ls -ld papka/                    # Papkaning ichini emas, o'zining ma'lumotini ko'rish
```

---

## 📁 Papka yaratish (mkdir)

```bash
mkdir loyiha                     # Bitta papka yaratish
mkdir -p loyiha/src/components   # Ichma-ich barcha papkalarni avtomatik bir yo'la yaratish (-p)
mkdir papka1 papka2 papka3       # Bir vaqtda bir nechta alohida papka yaratish
```

---

## 📄 Fayl yaratish va tahrirlash

```bash
touch fayl.txt                   # Bo'sh fayl yaratish yoki mavjud fayl vaqtini yangilash
touch a.py b.py c.py             # Bir vaqtda bir nechta fayl yaratish
echo "Salom Dunyo" > fayl.txt    # Matn bilan fayl yaratish (eski matn ustiga yozadi!)
echo "Yangi qator" >> fayl.txt   # Fayl oxiriga yangi qator qo'shish

# Ko'p qatorli matn yozish (Heredoc):
cat << 'EOF' > config.env
PORT=8000
DEBUG=True
DATABASE_URL=postgresql://localhost:5432/db
EOF

# Terminal ichida matn muharrirlari:
nano fayl.txt                    # Oddiy va qulay muharrir (Chiqish: Ctrl+X, Saqlash: Y, Enter)
vim fayl.txt                     # Kuchli professional muharrir (Chiqish: :q!, Saqlash: :wq)
code .                           # Hozirgi papkani VS Code'da ochish
```

---

## 👀 Fayl ichini ko'rish va o'qish

```bash
cat fayl.txt                     # Butun fayl matnini terminalga chiqarish
less fayl.txt                    # Katta fayllarni sahifama-sahifa o'qish (Chiqish: 'q', Qidirish: '/soz')
head -n 20 fayl.txt              # Faylning birinchi 20 qatorini ko'rish
tail -n 20 fayl.txt              # Faylning oxirgi 20 qatorini ko'rish
tail -f /var/log/nginx/error.log # Jonli loglarni real vaqtda kuzatib borish (To'xtatish: Ctrl+C)
wc -l fayl.txt                   # Fayldagi qatorlar sonini sanash
```

---

## 📋 Nusxalash (cp va rsync)

```bash
# Fayllarni nusxalash:
cp fayl.txt nusxa.txt            # Shu papkada yangi nom bilan nusxa olish
cp fayl.txt /opt/loyiha/         # Boshqa papkaga nusxalash
cp *.txt /opt/backup/            # Barcha .txt fayllarni nusxalash

# Papkalarni nusxalash (ichidagilari bilan -r):
cp -r papka/ /opt/backup/        # Papka va uning butun ichini rekursiv nusxalash
cp -a loyiha/ zaxira_loyiha/     # Barcha ruxsatlar va sanalarni saqlagan holda to'liq nusxalash

# Professional sinxronizatsiya (rsync):
rsync -avz loyiha/ /opt/loyiha/  # Tezkor va tejamkor nusxalash
```

---

## ✂️ Ko'chirish va Nomini o'zgartirish (mv)

```bash
# Fayl yoki papka nomini o'zgartirish:
mv eski_nom.txt yangi_nom.txt    # Nomini o'zgartirish
mv eski_papka yangi_papka        # Papka nomini o'zgartirish

# Ko'chirish:
mv fayl.txt /var/www/            # Faylni boshqa papkaga ko'chirish
mv fayl.txt /var/www/yangi.txt   # Ko'chirib, nomini ham o'zgartirish
mv *.log /tmp/logs/              # Barcha loglarni ko'chirish
mv papka/ /opt/yordamchi/        # Butun papkani ko'chirish
```

---

## 🗑️ O'chirish (rm va rmdir)

```bash
rm fayl.txt                      # Bitta faylni o'chirish
rm -f fayl.txt                   # Majburiy o'chirish (savolsiz, force)
rm *.tmp *.log                   # Bir nechta kengaytmadagi fayllarni o'chirish
rmdir bosh_papka                 # Faqat BO'SH papkani o'chirish

# Ichida fayli bor papkalarni o'chirish (-rf):
rm -rf papka/                    # Papkani barcha ichidagi fayllari bilan qaytarib bo'lmas qilib o'chirish!
rm -rf .venv/ build/ dist/       # Kesh va virtual muhit papkalarini tozalash
```

> ⚠️ **DIQQAT!** Linux'da o'chirilgan fayllar "Savatcha" (Trash)ga tushmaydi — darhol butunlay o'chadi. `rm -rf /` yoki `rm -rf *` yozishda o'ta ehtiyot bo'ling!

---

## 🔍 Qidirish (find va grep)

### 1. Fayl va papkalarni qidirish (`find`):
```bash
find . -name "main.py"           # Hozirgi papkadan "main.py" faylini topish
find . -iname "*.JPG"            # Katta-kichik harf farqsiz qidirish
find . -type f -name "*.json"    # Faqat fayllar orasidan .json larni topish
find . -type d -name "tests"     # Faqat papkalar orasidan "tests" ni topish
find /var/log -size +50M         # Hajmi 50 MB dan katta fayllarni topish
find . -mtime -1                 # Oxirgi 24 soat ichida o'zgargan fayllar
```

### 2. Fayl ichidagi matnlarni qidirish (`grep`):
```bash
grep "xatolik" app.log           # Bitta fayldan so'zni qidirish
grep -i "error" app.log          # Katta-kichik harf farqsiz (-i)
grep -n "def main" script.py     # Qator raqami bilan (-n)
grep -rnw "DATABASE_URL" .       # Hozirgi papkadagi barcha fayllardan rekursiv so'zni qidirish
grep -rnwi "FastAPI" /opt/app/   # Butun loyihadan so'zni topish
```

---

## 🗂️ Papkalar daraxti (tree)

```bash
tree                             # Barcha papkalar daraxti
tree -L 2                        # Faqat 2-darajali chuqurlikkacha ko'rsatish
tree -a                          # Yashirin fayllar bilan
tree -d                          # Faqat papkalarni ko'rsatish
tree -I "node_modules|venv|__pycache__" # Keraksiz papkalarni chetlab o'tish
```

---

## 🔐 Ruxsatlar va Huquqlar (chmod, chown, sudo)

Linux'da har bir faylda 3 ta huquq bor: `r` (o'qish=4), `w` (yozish=2), `x` (ishga tushirish=1).

```bash
chmod +x script.sh               # Skriptga ishga tushirish (execute) huquqini berish
chmod 644 fayl.txt               # Standart fayl huquqi (Egasi o'qiydi+yozadi, qolganlar faqat o'qiydi)
chmod 755 script.sh              # Standart bajariluvchi fayl / papka huquqi
chmod -R 755 /var/www/loyiha     # Butun papkaga rekursiv huquq berish

# Egasi (Owner)ni o'zgartirish:
chown opc:opc fayl.txt           # Egasi va guruhini opc qilish
chown -R opc:opc /opt/loyiha/    # Butun papka egasini o'zgartirish

# Administrator (Root) huquqi bilan bajarish:
sudo apt update                  # Root nomidan bajarish
sudo su                          # To'liq root foydalanuvchisiga o'tish
```

---

## ⚙️ Jarayonlar (Process) va Xizmatlar

```bash
# Jarayonlarni ko'rish:
ps aux                           # Tizimdagi barcha faol jarayonlar
ps aux | grep python             # Faqat Python dasturlarini topish
top                              # Tizim yuklanishini real vaqtda ko'rish
htop                             # Qulay va rangli jarayonlar dispetcheri

# Jarayonni to'xtatish:
kill <PID>                       # Jarayonni uning ID raqami bo'yicha to'xtatish
kill -9 <PID>                    # Majburiy darhol o'ldirish (Force Kill)
killall python3                  # Barcha python3 jarayonlarini to'xtatish
pkill -f "bot.py"                # Nomi bo'yicha qidirib to'xtatish

# Orqa fonda ishga tushirish (Background):
nohup python3 main.py > app.log 2>&1 & # Terminal yopilsa ham ishlashda davom etadi

# Systemd Servislarni boshqarish:
systemctl status nginx           # Nginx holatini ko'rish
systemctl start nginx            # Ishga tushirish
systemctl stop nginx             # To'xtatish
systemctl restart nginx          # Qayta ishga tushirish
systemctl enable nginx           # Server yonganda avtomatik yonadigan qilish
journalctl -u yordamchi-site -f  # Servisning jonli loglarini ko'rish
```

---

## 💾 Xotira, Disk va Tizim monitoringi

```bash
df -h                            # Diskdagi bo'sh va band joy (GB larda)
du -sh /opt/yordamchi            # Muayyan papkaning umumiy hajmi
du -sh * | sort -h               # Hozirgi papkadagi hamma narsani hajmi bo'yicha tartiblash
free -h                          # Operativ xotira (RAM) holati
uptime                           # Server qancha vaqtdan beri ishlayotgani va Load Average
lscpu                            # Protsessor (CPU) parametrlari
```

---

## 🌐 Tarmoq, Portlar va Server (Network)

```bash
ip a                             # Server / Kompyuter IP manzillarini ko'rish
curl ifconfig.me                 # Tashqi (Public) IP manzilni aniqlash
ping -c 4 google.com             # Tarmoq aloqasini tekshirish
ss -tulpn                        # Qaysi portlar ochiq va qaysi dastur eshitayotganini ko'rish
curl -sI https://example.com     # Saytning HTTP sarlavhalarini tekshirish
wget https://site.com/file.zip   # Internetdan fayl yuklab olish
ssh user@server_ip               # Masofaviy serverga ulanish
scp fayl.txt user@ip:/opt/       # Serverga fayl uzatish
```

---

## 📦 Arxivlash va Qisish (tar, zip)

```bash
# .tar.gz formatida:
tar -czvf arxiv.tar.gz papka/    # Papkani arxivlash va siqish
tar -xzvf arxiv.tar.gz           # Arxivni ochish (extract)
tar -tzvf arxiv.tar.gz           # Arxivni ochmasdan ichidagilarni ko'rish

# .zip formatida:
zip -r arxiv.zip papka/          # Zip arxiv yaratish
unzip arxiv.zip                  # Zip arxivni ochish
```

---

## ⌨️ Klaviatura Qisqartmalari va Quvvatli Usullar

| Tugma | Vazifasi |
|---|---|
| `Tab` | Fayl / Papka / Buyruq nomini avtomatik to'ldirish (Eng ko'p ishlatiladi!) |
| `Ctrl + C` | Hozir ishlab turgan jarayonni to'xtatish |
| `Ctrl + L` | Terminal ekranini tozalash (`clear` kabi) |
| `Ctrl + R` | Oldin yozilgan buyruqlar tarixidan tezkor qidirish |
| `Ctrl + A` | Kursorni qatorning eng boshiga olib o'tish |
| `Ctrl + E` | Kursorni qatorning eng oxiriga olib o'tish |
| `Ctrl + U` | Kursordan oldingi butun qatorni o'chirib tashlash |
| `↑` / `↓` | Oldingi bajarilgan buyruqlar tarixi bo'yicha harakatlanish |

---

## 🔗 Quvurlar (Pipe) va Qayta yo'naltirish

```bash
komanda1 && komanda2             # Birinchisi muvaffaqiyatli bo'lsagina ikkinchisini bajarish
komanda1 || komanda2             # Birinchisi xato bersagina ikkinchisini bajarish
komanda1 ; komanda2              # Ikkalasini ketma-ket har qanday holatda bajarish

# Chiqishni yo'naltirish:
ls -la > royxat.txt              # Natijani faylga yozish (ustiga yozadi)
ls -la >> royxat.txt             # Natijani fayl oxiriga qo'shish

# Quvur (Pipe |):
ps aux | grep python             # ps natijasini grep ga uzatish
ls -l /etc | less                # Uzun ro'yxatni less orqali sahifalab o'qish
cat access.log | grep "404" | wc -l # 404 xatolari sonini sanash
```

---

## 📝 Windows vs Linux Taqqoslash Jadvali

| Vazifa | Windows CMD | Linux (Bash/Zsh) |
|---|---|---|
| Hozirgi joyni ko'rish | `cd` | `pwd` |
| Fayllar ro'yxati | `dir` | `ls -la` |
| Papka yaratish | `mkdir papka` | `mkdir -p papka` |
| Bo'sh fayl yaratish | `type nul > f.txt` | `touch f.txt` |
| Fayl o'qish | `type f.txt` | `cat f.txt` yoki `less f.txt` |
| Nusxalash | `copy a b` / `xcopy` | `cp a b` / `cp -r a b` |
| Ko'chirish / Nom o'zgartirish | `move` / `ren` | `mv` |
| Fayl o'chirish | `del f.txt` | `rm f.txt` |
| Papka o'chirish | `rmdir /s /q papka` | `rm -rf papka/` |
| Qidirish | `findstr` | `grep -rnw` |
| Ekranni tozalash | `cls` | `clear` yoki `Ctrl + L` |
| Dastur qayerdaligi | `where python` | `which python3` |
| Jarayonlar | `tasklist` / `taskkill` | `ps aux` / `kill -9` / `pkill` |
| Administrator | Run as Administrator | `sudo` |

---

*💡 Maslahat: `man buyruq_nomi` (masalan: `man ls` yoki `ls --help`) orqali har qanday buyruqning rasmiy to'liq qo'llanmasini o'qishingiz mumkin.*
