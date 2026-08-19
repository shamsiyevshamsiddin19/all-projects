# Seed skriptlari

Bu yerdagi skriptlar bazaga **boshlang'ich kontent** kiritadi (mashqlar,
tavsiflar, media). Kod emas, KONTENT — shuning uchun `schema.sql` dan
alohida turadi.

## Nega kerak

Sport mashqlari `sport_exercises` jadvalida yashaydi, ya'ni faqat bazada.
Kunlik zaxira (`/opt/yordamchi/backup.sh`, systemd timer) server yo'qolishidan
himoya qiladi, lekin **noldan qayta o'rnatishda** kontent tiklanmaydi.
Shu skriptlar aynan shu bo'shliqni yopadi.

## Ishlatish (serverda)

```bash
cd /opt/yordamchi/Yordamchisayt/backend_py
.venv/bin/python ../database/seeds/press_exercises.py
```

Har bir skript **qayta ishga tushirishga chidamli**: mavjud yozuv ustidan
nusxa qo'shmaydi, faqat yetishmayotganini qo'shadi.

## Fayllar

| Fayl | Nima qiladi |
|---|---|
| `press_exercises.py` | "Press / Qorin" kategoriyasiga 12 ta mashq (tavsif, set/takror) |
| `press_rolik.py` | "Rolik (ab wheel)" mashqi + rasm va video |
| `press_media.py` | 12 ta press mashqiga YouTube darsligi va old ko'rinish rasmi |
| `squat_bodyweight.py` | Prisedaniye (squat) — shtangadan O'Z VAZNI bilan takrorga o'tkazish |
| `aiogram_lessons.py` | Learn > Dasturlash > "Aiogram" papkasiga 18 ta dars (manba: mahalliy `.md` fayllar, `sys.argv[1]` bilan yo'l beriladi) |

## Eslatma — mashq NOMINI o'zgartirmang

`squat_bodyweight.py` mashq turini o'zgartiradi, lekin **nomiga tegmaydi**.
Sabab: `activity_log` yozuvlari va Boostday↔Sport bog'lanishi NOM bo'yicha
ishlaydi (`backend_py/app/handlers/sport.py::_today_boost_done`). Nom
o'zgarsa bajarilgan kunlar tarixi uzilib qoladi va Telegramda belgilangan
vazifa saytdagi mashq bilan mos kelmay qo'yadi.

## Eslatma — video ID lari

Skriptlardagi barcha YouTube ID lari qo'shishdan oldin oEmbed orqali
tekshirilgan (mavjudligi va mavzuga mosligi). Yangi video qo'shsangiz
shuni takrorlang, aks holda saytda ishlamaydigan havola paydo bo'ladi:

```bash
curl -s "https://www.youtube.com/oembed?url=https%3A//www.youtube.com/watch%3Fv%3D<ID>&format=json"
```

HTTP 200 va mos sarlavha qaytsa — ID to'g'ri.
