# Quick Translate — ekran tarjimoni (GNOME Shell kengaytmasi)

Ikki yo'l bilan tarjima qiladigan GNOME Shell kengaytmasi:

| Yorliq | Nima qiladi |
| :-- | :-- |
| **`Ctrl + Alt + Z`** | Sichqoncha bilan **belgilangan matnni** kursor yonida tarjima qiladi |
| **`Ctrl + Alt + X`** | Ekranni **qotiradi**, mediani pauzaga qo'yadi; siz matn turgan **maydonni belgilaysiz** va faqat o'sha joy o'qiladi |

Qotirish rejimiga kirilganda ekran chetida **gradient halqa** yonadi va u holatni ham aytadi:

| Rang | Ma'nosi |
| :-- | :-- |
| 🟠 sariq, tez puls | matn o'qilmoqda |
| 🔵 ko'k-siyoh, sokin puls | belgilashga tayyor |
| 🔴 qizil, pulssiz | xato (matn topilmadi yoki OCR yiqildi) |

`Ctrl+Alt+X` — Windows'dagi PowerToys *Text Extractor* ning shu desktopdagi varianti: videodagi subtitr, slayddagi yozuv yoki skrinshotdagi matn piksel bo'lsa ham nusxalanadigan matnga aylanadi.

Oqim: **`Ctrl+Alt+X`** → ekran qotadi, video to'xtaydi → sichqoncha bilan **maydonni sudrab belgilaysiz** → o'sha bo'lak o'qiladi → **Nusxalash** / **Tarjima qil** chiqadi.

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

# Chetdagi gradient halqani o'chirish (juda sust grafikada)
gsettings --schemadir $EXT/schemas set org.gnome.shell.extensions.quick-translate \
  glow-enabled false
```

Mavjud tillar: `eng`, `rus`, `uzb`, `uzb_cyrl`, `osd`.

## Qotirilgan ekranda tugmalar

| Tugma | Amal |
| :-- | :-- |
| sichqonchani sudrash | o'qiladigan maydonni belgilash (qayta sudrab o'zgartirish mumkin) |
| `Ctrl + A` | butun ekranni maydon sifatida olish |
| `Ctrl + C` | o'qilgan matnni nusxalab chiqish |
| `Esc` / o'ng tugma / `Ctrl+Alt+X` | chiqish (media davom etadi) |
| **Tarjima qil** | tarjima kartasi chiqadi — media **karta yopilgunicha pauzada qoladi** |
| **Nusxalash** | matn clipboardga tushadi va media darhol davom etadi |

---

## Arxitektura

Qatlamlar ataylab ajratilgan: har bir modul bitta vazifa bajaradi va yuqori qatlam quyi detalga bog'lanmaydi.

| Fayl | Qatlam | Vazifasi |
| :-- | :-- | :-- |
| `extension.js` | Kirish | Yorliqlarni ro'yxatga oladi, ikki yo'lni tarjimada birlashtiradi |
| `freeze-service.js` | Facade | Qotirish → pauza → OCR → belgilash → amal paneli |
| `region-selector.js` | Taqdimot | Sudrab maydon tanlash, atrofini qoraytirish |
| `region-geometry.js` | Sof funksiya | Sudrash → to'rtburchak, chegaraga qisish; `gi://` yo'q |
| `ocr-service.js` | Query | Maydonni PNG'ga kesish, Tesseract'ni chaqirish |
| `tsv-parser.js` | Sof funksiya | Tesseract TSV → so'zlar; `gi://` import qilmaydi |
| `media-service.js` | Command | MPRIS2 orqali pauza/davom (D-Bus, `playerctl`siz) |
| `glow-overlay.js` | Taqdimot | Chetdagi gradient halqa va holat rangi |
| `translation-service.js` | Query | Gemini / Claude / Google Translate |
| `popup.js` | Taqdimot | Tarjima oynasi |

To'rtta qaror alohida izohga arziydi:

1. **Kadr qayta suratga olinmaydi.** OCR aynan ekranda qotib turgan teksturadan (`composite_to_stream`) olinadi. Aks holda video siljib, so'z koordinatalari ko'rinayotgan tasvirga mos kelmay qolardi.
2. **Butun ekran emas, belgilangan maydon o'qiladi.** Avvalgi variantda butun ekran OCR qilinardi va natijaga sarlavha, aktyor ismlari, tugma yozuvlari aralashib ketardi; ustiga 1920×1080 ni o'qish sekin edi. Maydon tanlansa natija toza va tez. Tesseract `--psm 6` ("yagona bir jinsli matn bloki") ishlatiladi — to'liq sahifa avtomatikasi kichik kesilgan bo'lakda satrlarni noto'g'ri ajratardi.
3. **Animatsiya ataylab arzon.** Bu noutbukda qotish muammosi iGPU VRAM'dan (512 MB) kelib chiqadi, shuning uchun halqada blur, soya va to'liq ekran qatlami yo'q — faqat 8 ta ingichka chet chizig'ining `opacity`si o'zgaradi va pulsni `auto_reverse` bilan kompozitorning o'zi yuritadi, JS tomonda har kadrda hech narsa hisoblanmaydi.
4. **Tesseract, vision model emas.** Live Text uchun har bir so'zning aniq piksel to'rtburchagi kerak; Tesseract `tsv` rejimida shuni beradi, vision modellar esa matnni yaxshi o'qisa-da koordinatani ishonchli bermaydi. Qo'shimcha foyda: oflayn ishlaydi.

**Karta o'lchami qat'iy: 480×300 px.** Matn uzunligidan qat'i nazar o'zgarmaydi — shunda karta kursor yonida sakrab turmaydi. Matn sig'masa moslashadigan narsa — **shrift**: `_fitTextToCard()` miqyosni 1 dan 0.05 qadam bilan kamaytiradi va har qadamda matnning haqiqiy balandligini so'raydi, sig'ishi bilan to'xtaydi. Qisqa matn asl o'lchamida qoladi.

Pastki chegara **0.55**: undan pastga tushirilmaydi, aks holda juda uzun matnda yozuv o'qib bo'lmas holga kelardi; shu chegarada ham sig'masa `ScrollView` aylantiradi. Faqat `font-size` o'zgaradi — rang va bo'shliqlar tegilmaydi.

Tarjima qilinayotgan matn kartaning eng tepasida, to'liq turadi: kesilmaydi va "..." qo'yilmaydi.

Media pauzasining egasi — qotirish overlayi, lekin uni **tarjima kartasi** bo'shatadi: karta ko'rinib turganda video o'ynab ketmasligi kerak. Shuning uchun `popup.js` da `setOnClosed` ilgagi bor va uni `extension.js` ulaydi — `freeze-service.js` popup haqida hech narsa bilmaydi, bog'liqlik yo'nalishi buzilmaydi.

Ekranda shaxsiy ma'lumot bo'lishi mumkin, shuning uchun vaqtinchalik PNG `XDG_RUNTIME_DIR` ga `PRIVATE` huquqi bilan yoziladi va OCR tugashi bilan darhol o'chiriladi.

## Sinovlar

```bash
for t in tests/*.cjs; do node "$t" || break; done   # 9 ta to'plam

node tests/tsv-parser.cjs        # 14 chegaraviy holat + haqiqiy tesseract
node tests/popup-layout.cjs      # o'lcham qat'iy, shrift sig'guncha kichrayadi
node tests/region-geometry.cjs   # sudrash yo'nalishi, ekran chegarasi
node tests/extension-lifecycle.cjs  # ikki yorliq, media pauzasi
```

`tests/tsv-parser.cjs` rasm generatsiya qilib (ImageMagick) uni haqiqiy Tesseract'ga o'qitadi va natijani tekshiradi — ya'ni OCR quvuri Shell'ni ishga tushirmasdan sinaladi.

## Diagnostika

```bash
journalctl --user -f -o cat | grep -i quicktranslate
```

`console.log` journalga tushmaydi — kengaytma shu sababdan `console.warn` ishlatadi.
