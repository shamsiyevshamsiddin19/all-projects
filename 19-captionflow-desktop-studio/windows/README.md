# Subtitr Desktop — Windows

Sinalgan: Windows 10/11 (x64).

## 1. Kerakli dasturlar

- **Flutter SDK** (3.27+) — [flutter.dev/docs/get-started/install/windows](https://docs.flutter.dev/get-started/install/windows)
- **Visual Studio 2022** + "Desktop development with C++" ish yuki
- **Python 3.10+** — [python.org](https://www.python.org/downloads/windows/)
  (o'rnatishda "Add Python to PATH" ni belgilang)
- **Inno Setup 6** — o'rnatuvchi (`SubtitrSetup.exe`) yasash uchun:
  `winget install JRSoftware.InnoSetup`

Tekshirish: `flutter doctor` da "Visual Studio" yashil bo'lsin.

## 2. Binar fayllarni qo'yish

Linux/macOS dan farqli o'laroq, Windows'da ffmpeg dastur bilan birga
yuboriladi. Ularni repoga qo'shmaymiz (hajmi katta), shuning uchun qo'lda
`tools\` papkasiga qo'ying:

```
subtitr-desktop\tools\ffmpeg.exe
subtitr-desktop\tools\ffprobe.exe
subtitr-desktop\tools\yt-dlp.exe
```

- ffmpeg/ffprobe: [gyan.dev/ffmpeg/builds](https://www.gyan.dev/ffmpeg/builds/)
  ("release essentials" arxividagi `bin\` papkasidan)
- yt-dlp: [github.com/yt-dlp/yt-dlp/releases](https://github.com/yt-dlp/yt-dlp/releases/latest)
  (`yt-dlp.exe`)

## 3. Yig'ish

```powershell
git clone https://github.com/shamsiyevshamsiddin19/vibe-coding.git
cd vibe-coding\subtitr-desktop
.\windows\build.ps1
```

Natija:

- `installer\SubtitrSetup.exe` — o'rnatuvchi (tarqatish uchun)
- `Subtitr-Release.zip` — portativ arxiv (o'rnatishsiz ishlaydi)

Python protsessor PyInstaller bilan bitta `desktop_processor.exe` ga
qotiriladi — foydalanuvchida Python bo'lishi shart emas.

## 4. O'rnatish

`SubtitrSetup.exe` ni ishga tushiring. Administrator huquqi **shart emas** —
dastur foydalanuvchi papkasiga o'rnatiladi.

Portativ variant: `Subtitr-Release.zip` ni ochib, `subtitr_app.exe` ni
ishga tushiring.

## 5. SmartScreen ogohlantirishi

Fayllar kod-imzolash sertifikati bilan imzolanmagan, shuning uchun Windows
**"Noma'lum nashriyot"** deb ogohlantiradi. Bu normal:
**Batafsil → Baribir ishga tushirish**.

Sertifikatingiz bo'lsa, yig'ishdan oldin:

```powershell
$env:SUBTITR_SIGN_PFX  = "C:\yo'l\cert.pfx"
$env:SUBTITR_SIGN_PASS = "parol"
# yoki Windows sertifikat do'konidan:
$env:SUBTITR_SIGN_THUMB = "<thumbprint>"
```

## 6. Birinchi ishga tushirish

Ilova ichida kalit tugmasini bosib **Groq** kalitini kiriting
([console.groq.com](https://console.groq.com) — bepul).

To'liq qo'llanma: [`../ISHLATISH_DESKTOP.txt`](../ISHLATISH_DESKTOP.txt)

## 7. Muammolar

**`ISCC.exe topilmadi`** — Inno Setup o'rnatilmagan. O'rnatuvchisiz ham
`Subtitr-Release.zip` yasaladi.

**`flutter build windows` yiqiladi** — Visual Studio'da "Desktop development
with C++" ish yuki o'rnatilganini tekshiring.

**ffmpeg topilmadi deydi** — `tools\` papkasiga `ffmpeg.exe` va
`ffprobe.exe` ni qo'yganingizni tekshiring (2-bo'limga qarang).
