# Subtitr Desktop

Video subtitr/tarjima qiluvchi desktop ilova (Flutter GUI + Python backend). Windows va Linux.

- Video/audio transkripsiya (Groq Whisper / faster-whisper)
- Tarjima (OpenAI / Anthropic Claude / Google Gemini / Groq)
- Lug'at (lemma + chastota) va o'quv uchun so'z animatsiyasi
- Subtitr kuydirish (ffmpeg, apparat kodlash: NVENC/QSV/AMF)
- YouTube/Instagram va boshqa saytlardan video yuklash (yt-dlp)
- Chrome kengaytmasi (`chrome-extension/`) — sahifadagi video oqim havolasini topib beradi

## Tuzilma

- `desktop_processor.py` — Python backend (PyInstaller bilan `.exe`ga qotiriladi)
- `subtitr_app/` — Flutter desktop GUI (Windows + Linux)
- `chrome-extension/` — "Subtitr Grabber" Chrome kengaytmasi
- `build_release.ps1` — Windows release (`.exe` + installer + zip) yig'ish skripti
- `installer.iss` — Inno Setup skripti (Windows)
- `build_release.sh` — Linux release (`dist/SubtitrDesktop` + tar.gz) yig'ish skripti
- `install.sh` — Linux o'rnatuvchi (menyu yorlig'i bilan, sudo shart emas)
- `ISHLATISH_LINUX.txt` — Linux uchun qo'llanma

## Eslatma

Bu papkada faqat manba kod bor. Katta binary fayllar (`ffmpeg.exe`, `ffprobe.exe`, `yt-dlp.exe`,
build/dist chiqishlari, o'rnatuvchi) reponing hajmini shishirmasligi uchun qo'shilmagan — build
qilishdan oldin ularni `tools/` papkasiga qo'lda qo'shish kerak. API kalitlar (`.env`) hech qachon
repoga qo'shilmaydi — faqat bo'sh namuna `.env.example` bor.
