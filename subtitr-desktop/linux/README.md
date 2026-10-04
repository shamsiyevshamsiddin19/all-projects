# Subtitr Desktop — Linux

Sinalgan: Ubuntu 24.04 (x86_64), GNOME/Wayland. Boshqa distrolarda ham
ishlashi kerak — paket nomlari farq qilishi mumkin.

## 1. Kerakli dasturlar

```bash
sudo apt install ffmpeg python3-venv
```

Qo'shimcha:

- **Flutter SDK** (3.27+) — [flutter.dev/docs/get-started/install/linux](https://docs.flutter.dev/get-started/install/linux)
  va Linux desktop uchun: `sudo apt install clang cmake ninja-build pkg-config libgtk-3-dev`
- **Python 3.10+** (Ubuntu 24.04 da 3.12 keladi)
- PDF uchun kirill harflari bor serif shrift:
  `sudo apt install fonts-noto-serif` (odatda allaqachon bor)

Tekshirish: `flutter doctor` da "Linux toolchain" yashil bo'lsin.

## 2. Yig'ish

```bash
git clone https://github.com/shamsiyevshamsiddin19/vibe-coding.git
cd vibe-coding/subtitr-desktop
./linux/build.sh
```

Skript o'zi bajaradi: Flutter release build, Python virtual muhiti,
yt-dlp yuklab olish, va hammasini bitta papkaga yig'ish.

Natija:

- `dist/SubtitrDesktop/` — tayyor papka
- `dist/SubtitrDesktop-linux-x64.tar.gz` — arxiv (~220 MB)

Birinchi yig'ish 5-15 daqiqa oladi (Flutter va pip yuklab oladi).

## 3. O'rnatish

```bash
./dist/SubtitrDesktop/install.sh
```

Administrator huquqi **shart emas**. Dastur `~/.local/share/SubtitrDesktop`
ga tushadi va menyuda **"Subtitr Desktop"** bo'lib chiqadi.

Terminal'dan ishga tushirish:

```bash
~/.local/share/SubtitrDesktop/subtitr-desktop
```

O'chirish:

```bash
~/.local/share/SubtitrDesktop/uninstall.sh
```

## 4. Birinchi ishga tushirish

Ilova ichida kalit tugmasini bosib **Groq** kalitini kiriting
([console.groq.com](https://console.groq.com) — bepul). Kalitsiz ham ishlaydi:
lokal `faster-whisper` bilan oflayn transkripsiya, lekin sekinroq va tarjima
to'liq bo'lmaydi.

Papkalar:

| | |
|---|---|
| Dastur | `~/.local/share/SubtitrDesktop` |
| Natijalar | `~/Videos/Subtitr natijalar` |
| Ishchi fayllar va AI modellar | `~/.cache/SubtitrDesktop` |

To'liq qo'llanma: [`../ISHLATISH_LINUX.txt`](../ISHLATISH_LINUX.txt)

## 5. Muammolar

**`venv yaratilmadi`** — `sudo apt install python3-venv`

**Video render sekin** — apparat kodlash topilmagan bo'lishi mumkin.
AMD/Intel uchun VAAPI: `ls /dev/dri/renderD128` bor-yo'qligini tekshiring,
foydalanuvchi `video`/`render` guruhida bo'lsin. Majburlash:
`SUB_ENCODER=vaapi`.

**PDF yasalmadi, shrift haqida xato** — `sudo apt install fonts-noto-serif`

**Wayland'da oyna g'alati** — `GDK_BACKEND=x11` bilan ishga tushirib ko'ring.
