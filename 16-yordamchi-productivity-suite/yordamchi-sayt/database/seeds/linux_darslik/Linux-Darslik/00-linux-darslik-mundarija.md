# Linux & Ubuntu 24.04 LTS darsligi — Barcha mavzular (to'liq, 7 bo'lim, 17 dars)

_Ushbu darslik noldan boshlab Ubuntu 24.04 LTS (Noble Numbat) operatsion tizimi, Linux yadrosi, fayl tizimi ierarxiyasi, ruxsatlar, jarayonlar monitoringi, APT paket menejeri, Systemd servislar, Crontab avtomatlashtirish, tarmoq va SSH/UFW xavfsizligigacha bo'lgan barcha professional bilimlarni qamrab oladi._

---

## 00. Kirish va Ubuntu 24.04 Asoslari

| № | Mavzu | Fayl |
|---|---|---|
| 0.1 | Linux nima, tarixi va tizim arxitekturasi | 0.1-linux-nima-tarixi-arxitekturasi.md |
| 0.2 | Ubuntu 24.04 LTS tizimi, Terminal va Shell (Bash/Zsh) asoslari | 0.2-ubuntu-24-04-terminal-shell-asoslari.md |

## 01. Fayl Tizimi va Asosiy Buyruqlar

| № | Mavzu | Fayl |
|---|---|---|
| 1.1 | Linux fayl daraxti (FHS) va muhim kataloglar tuzilishi | 1.1-fayl-daraxti-tuzilishi.md |
| 1.2 | Fayllar va papkalarni ko'rish va navigatsiya (pwd, ls, cd, cat, less, head, tail) | 1.2-navigatsiya-va-fayllarni-korish.md |
| 1.3 | Fayl va papkalar ustida amallar (mkdir, touch, cp, mv, rm, rmdir) | 1.3-fayl-va-papkalarni-boshqarish.md |
| 1.4 | Qidiruv va filtrlar (find, grep, which, whereis, xargs) | 1.4-qidiruv-buyruqlari-find-grep.md |

## 02. Foydalanuvchilar, Guruhlar va Ruxsatlar (Permissions)

| № | Mavzu | Fayl |
|---|---|---|
| 2.1 | Foydalanuvchilar va guruhlar boshqaruvi (adduser, usermod, sudo, /etc/passwd) | 2.1-foydalanuvchilar-va-guruhlar.md |
| 2.2 | Fayl ruxsatlari: Read, Write, Execute va raqamli tizim (chmod 755/644) | 2.2-fayl-ruxsatlari-chmod-chown.md |
| 2.3 | Fayl egaligi va maxsus ruxsatlar (chown, chgrp, umask, SUID) | 2.3-fayl-egaligi-chown-umask.md |

## 03. Jarayonlar, Resurslar va Monitoring

| № | Mavzu | Fayl |
|---|---|---|
| 3.1 | Jarayonlar (Processes) boshqaruvi va signallar (ps, top, htop, kill, pkill) | 3.1-jarayonlarni-boshqarish-ps-top-kill.md |
| 3.2 | Fon rejimi, ustuvorlik va uzluksizlik (jobs, bg, fg, nohup, tmux) | 3.2-fon-rejimi-tmux-nohup.md |
| 3.3 | Tizim resurslari va xotira monitoringi (free, df, du, uptime, vmstat) | 3.3-resurslar-monitoringi-df-du-free.md |

## 04. Paketlar va Dasturlar Boshqaruvi (Package Management)

| № | Mavzu | Fayl |
|---|---|---|
| 4.1 | APT va DPKG paket boshqaruvi (Ubuntu 24.04 deb822 manbalari, apt install) | 4.1-apt-va-dpkg-paket-boshqaruvi.md |
| 4.2 | Arxivlar va tarmoq orqali yuklash (tar, gzip, zip, curl, wget) | 4.2-arxivlar-va-yuklab-olish-curl-wget-tar.md |

## 05. Systemd Servislar va Avtomatlashtirish (Cron)

| № | Mavzu | Fayl |
|---|---|---|
| 5.1 | Systemd va systemctl boshqaruvi (Servislar, daemon-reload, enable/start) | 5.1-systemd-va-systemctl-servislar.md |
| 5.2 | Shaxsiy systemd servis yaratish (Python/Django/Bot misolida) | 5.2-shaxsiy-systemd-servis-yaratish.md |
| 5.3 | Journalctl bilan loglarni tahlil qilish va Crontab avtomatlashtirish | 5.3-journalctl-loglar-crontab.md |

## 06. Tarmoq (Networking), SSH va Server Xavfsizligi

| № | Mavzu | Fayl |
|---|---|---|
| 6.1 | Tarmoq konfiguratsiyasi va diagnostikasi (ip, ss, ping, curl, dig, Netplan) | 6.1-tarmoq-konfiguratsiyasi-diagnostika.md |
| 6.2 | SSH xavfsiz boshqaruvi va kalitlar (ssh-keygen, ssh-copy-id, SSH config, SCP, Rsync) | 6.2-ssh-boshqaruvi-va-kalitlar.md |
| 6.3 | Server xavfsizligi, UFW Firewall va Fail2ban (Ubuntu 24.04) | 6.3-xavfsizlik-va-ufw-firewall.md |
