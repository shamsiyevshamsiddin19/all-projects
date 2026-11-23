# Quick Translate — ekran tarjimoni (GNOME Shell kengaytmasi)

Ikki yo'l bilan tarjima qiladigan GNOME Shell kengaytmasi:

| Yorliq | Nima qiladi |
| :-- | :-- |
| **`Ctrl + Alt + Z`** | Sichqoncha bilan **belgilangan matnni** kursor yonida tarjima qiladi |
| **`Ctrl + Alt + X`** | Ekranni **qotiradi**, mediani pauzaga qo'yadi va **rasmdagi matnni** (videodagi subtitr, slayd, skrinshot) belgilanadigan matnga aylantiradi |

`Ctrl+Alt+X` — Windows'dagi PowerToys *Text Extractor* yoki macOS *Live Text* ning shu desktopdagi varianti: matn piksel bo'lsa ham brauzerdagidek sudrab belgilanadi.

---

## Talablar

```bash
sudo apt install tesseract-ocr tesseract-ocr-rus tesseract-ocr-eng tesseract-ocr-uzb tesseract-ocr-uzb-cyrl tesseract-ocr-osd
sudo apt install wl-clipboard
```

- GNOME Shell **46+** (Wayland sinovdan o'tgan)
- Tarjima uchun `~/.config/quick-translate/providers.json` da API kalit:
  ```json
  { "apiKey": "<Gemini kaliti>", "claudeApiKey": "<Claude kaliti>" }
  ```
  Kalit bo'lmasa tarjima Google Translate'ning ochiq endpointiga tushadi; OCR esa kalitsiz ham ishlaydi (Tesseract lokal).

## O'rnatish

```bash
./install.sh
```

Keyin **tizimdan chiqib qaytib kirish shart** (logout → login). Wayland'da GNOME Shell'ni qayta ishga tushirmasdan kengaytma kodi yuklanmaydi — `Alt+F2 r` Wayland'da yo'q, `gnome-extensions disable/enable` esa ES modulini registridan qayta o'qimaydi.

## Sozlamalar

```bash
EXT=~/.local/share/gnome-shell/extensions/quick-translate@shamsiddin

# OCR tillari (ko'p til = sekinroq OCR)
gsettings --schemadir $EXT/schemas set org.gnome.shell.extensions.quick-translate \
  ocr-languages 'rus+eng'

# Yorliqni o'zgartirish
gsettings --schemadir $EXT/schemas set org.gnome.shell.extensions.quick-translate \
  freeze-ocr "['<Control><Alt>x']"
```

Mavjud tillar: `eng`, `rus`, `uzb`, `uzb_cyrl`, `osd`.

## Qotirilgan ekranda tugmalar

| Tugma | Amal |
| :-- | :-- |
| sichqonchani sudrash | matnni belgilash (o'qish tartibida) |
| `Ctrl + A` | butun ekran matnini belgilash |
| `Ctrl + C` | nusxalab chiqish |
| `Esc` / o'ng tugma / `Ctrl+Alt+X` | chiqish (media davom etadi) |

---

## Arxitektura

Qatlamlar ataylab ajratilgan: har bir modul bitta vazifa bajaradi va yuqori qatlam quyi detalga bog'lanmaydi.

| Fayl | Qatlam | Vazifasi |
| :-- | :-- | :-- |
| `extension.js` | Kirish | Yorliqlarni ro'yxatga oladi, ikki yo'lni tarjimada birlashtiradi |
| `freeze-service.js` | Facade | Qotirish → pauza → OCR → belgilash → amal paneli |
| `text-layer.js` | Taqdimot | Live Text belgilash: so'z to'rtburchaklari, yoritish |
| `ocr-service.js` | Query | Kadrni PNG'ga yozish, Tesseract'ni chaqirish |
| `tsv-parser.js` | Sof funksiya | Tesseract TSV → so'zlar; `gi://` import qilmaydi |
| `media-service.js` | Command | MPRIS2 orqali pauza/davom (D-Bus, `playerctl`siz) |
| `translation-service.js` | Query | Gemini / Claude / Google Translate |
| `popup.js` | Taqdimot | Tarjima oynasi |

Uchta qaror alohida izohga arziydi:

1. **Kadr qayta suratga olinmaydi.** OCR aynan ekranda qotib turgan teksturadan (`composite_to_stream`) olinadi. Aks holda video siljib, so'z koordinatalari ko'rinayotgan tasvirga mos kelmay qolardi.
2. **Belgilash to'rtburchak kesishishi bilan emas, o'qish tartibi bilan.** Anchor so'zdan joriy so'zgacha oradagi hammasi tanlanadi — shuning uchun ikki satrni qiyshiq sudraganda ham matn uzilmaydi.
3. **Tesseract, vision model emas.** Live Text uchun har bir so'zning aniq piksel to'rtburchagi kerak; Tesseract `tsv` rejimida shuni beradi, vision modellar esa matnni yaxshi o'qisa-da koordinatani ishonchli bermaydi. Qo'shimcha foyda: oflayn ishlaydi.

Ekranda shaxsiy ma'lumot bo'lishi mumkin, shuning uchun vaqtinchalik PNG `XDG_RUNTIME_DIR` ga `PRIVATE` huquqi bilan yoziladi va OCR tugashi bilan darhol o'chiriladi.

## Sinovlar

```bash
node tests/tsv-parser.cjs     # 14 chegaraviy holat + haqiqiy tesseract integratsiyasi
node tests/gemini-utils.cjs
node tests/translation-orchestrator.cjs
```

`tests/tsv-parser.cjs` rasm generatsiya qilib (ImageMagick) uni haqiqiy Tesseract'ga o'qitadi va natijani tekshiradi — ya'ni OCR quvuri Shell'ni ishga tushirmasdan sinaladi.

## Diagnostika

```bash
journalctl --user -f -o cat | grep -i quicktranslate
```

`console.log` journalga tushmaydi — kengaytma shu sababdan `console.warn` ishlatadi.
