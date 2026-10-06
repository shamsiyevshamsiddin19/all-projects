# Albomlar — musiqa albomlari sayti

Django 6.1 + SQLite (yoki PostgreSQL). Backend, frontend va Deezer/Spotify
importi tayyor.

## Ishga tushirish

### Windows (eng oson yo'l)

Loyiha papkasida `ishga-tushir.ps1` faylini o'ng tugma bilan bosib
**"Run with PowerShell"** ni tanlang. Yoki VS Code terminalida:

```powershell
.\ishga-tushir.ps1
```

Skript hammasini o'zi qiladi: Python topadi, `venv` yaratadi,
kutubxonalarni o'rnatadi, `.env` ni yasab `SECRET_KEY` generatsiya
qiladi, bazani tayyorlaydi va serverni ishga tushirib brauzerni ochadi.

Foydali variantlar:

```powershell
.\ishga-tushir.ps1 -Albom       # mashhur albomlarni ham yuklaydi
.\ishga-tushir.ps1 -Admin       # admin foydalanuvchi yaratadi
.\ishga-tushir.ps1 -Tarmoq      # telefondan ham ochish uchun
.\ishga-tushir.ps1 -Port 8080   # boshqa port
```

**"Running scripts is disabled" xatosi chiqsa** — Windows sukut
bo'yicha skriptlarni bloklaydi. Bir martalik ruxsat:

```powershell
powershell -ExecutionPolicy Bypass -File .\ishga-tushir.ps1
```

Yoki butunlay yechish (PowerShell'ni administrator sifatida oching):

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### VS Code

Loyihani ochib **F5** bosing. Uchta tayyor sozlama bor:
server, tarmoqqa ochiq server va albomlarni yuklash.

Birinchi marta "Python: Select Interpreter" so'ralsa — `venv` ichidagi
Python'ni tanlang.

### Linux / Mac (qo'lda)

```bash
cp .env.example .env          # keyin .env ni to'ldiring
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
./venv/bin/python manage.py migrate
./venv/bin/python manage.py createsuperuser
./venv/bin/python manage.py runserver
```

- Sayt: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/

## Musiqa xizmati (import)

`.env` da bitta qator hal qiladi:

```
MUSIC_PROVIDER=deezer     # kalitsiz, bepul, 30 soniyalik namuna beradi
MUSIC_PROVIDER=spotify    # SPOTIFY_CLIENT_ID + SECRET kerak
```

### Nega sukut bo'yicha Deezer?

Spotify 2025-yildan beri Web API uchun **ilova egasining akkaunti Premium
bo'lishini** talab qiladi. Premium bo'lmasa token olinadi, lekin har bir
so'rovga `403 Active premium subscription required` qaytadi — kalitlar
to'g'ri bo'lsa ham. Deezer'da bunday cheklov yo'q.

Spotify kodi joyida turibdi: Premium olsangiz `.env` dagi bitta qatorni
o'zgartirasiz, boshqa hech narsaga tegmaysiz. Ikkala klient ham bir xil
metodlarni (`search_albums`, `get_album`, `get_artist`) va bir xil shakldagi
`dict` ni qaytaradi.

### Import qilish

Brauzerda: **Import** sahifasi → nomini yozing → "Import qilish".

Terminalda:

```bash
./venv/bin/python manage.py import_album --search "the eminem show"
./venv/bin/python manage.py import_album 103248
./venv/bin/python manage.py import_album 103248 --provider spotify
```

Import albomni muqovasi, chiqqan sanasi, janrlari, ijrochisi (rasmi bilan)
va barcha qo'shiqlari bilan bazaga yozadi.

## Bazani to'ldirish

```bash
./venv/bin/python manage.py seed_albums            # ro'yxatdagi hammasini
./venv/bin/python manage.py seed_albums --limit 10 # faqat birinchi 10 tasi
```

Buyruq mashhur albomlar ro'yxatini katalogdan qidirib import qiladi.
Takroriy ishga tushirsa ham xavfsiz: bor albomni qayta qo'shmaydi.

Natijalardan **eng mosini** tanlaydi:

- karaoke, tribute, cover, lullaby nusxalari tashlanadi
- jonli yozuvlar tashlanadi (agar so'ralgan nomda "live" bo'lmasa)
- urg'u belgilari e'tiborga olinmaydi (`Beyonce` ↔ `Beyoncé`)
- ijrochi nomi mos kelmasa umuman olinmaydi

### Deezer kataloging cheklovi

Ba'zi mashhur albomlar bu yerdan **umuman ochilmaydi** — Dua Lipa,
Gorillaz, Coldplay, Linkin Park, Red Hot Chili Peppers, Ed Sheeran da
faqat singl va jonli yozuvlar ko'rinadi. Bu hududiy litsenziya cheklovi,
kodning xatosi emas. Yangi albom qo'shishdan oldin tekshiring:

```bash
./venv/bin/python manage.py import_album --search "albom nomi ijrochi"
```

### Albom nomlarini tozalash

Katalogda nomlar ko'pincha nashr qo'shimchasi bilan keladi:
`Nevermind (Remastered)`, `folklore (deluxe version)`. Import paytida
`clean_album_title()` ularni olib tashlaydi — sarlavha cho'zilib
dizaynni buzmasin.

Faqat **oxiridagi** qavs va faqat ichida nashr so'zi bo'lsa olinadi,
shuning uchun `(What's the Story) Morning Glory?` buzilmaydi.

## Ijrochi rasmlari (TheAudioDB)

Deezer ijrochi surati sifatida ko'pincha uning **albom muqovasini** beradi —
ayniqsa kam tanilgan ijrochilarda. Bosh sahifadagi katta blokka esa odamning
o'zi kerak. Shuning uchun rasmlar alohida xizmatdan olinadi:

| Maydon | Nimaligi | Qayerda ishlatiladi |
|---|---|---|
| `Artist.cutout` | foni kesilgan shaffof PNG | hero dagi asosiy figura |
| `Artist.banner` | keng surat (1920x1080) | hero orqa foni |
| `Artist.photo` | kvadrat portret | ijrochi kartalari va sahifasi |

Kalit kerak emas (ochiq `2` test kaliti ishlaydi). O'z kalitingiz bo'lsa
`.env` ga `AUDIODB_KEY=...` deb yozasiz.

```bash
# Bo'sh maydonlarni to'ldiradi
./venv/bin/python manage.py fetch_artist_art

# Eski rasmlar ustiga yozadi
./venv/bin/python manage.py fetch_artist_art --force

# Faqat bitta ijrochi
./venv/bin/python manage.py fetch_artist_art --name Queen
```

Yangi albom import qilinganda bu avtomatik chaqiriladi — buyruq faqat
**ilgari** qo'shilganlar uchun kerak.

Kam tanilgan ijrochi TheAudioDB da topilmasligi mumkin. Bu xato emas:
shunda hero eski rasmga qaytadi (portret → albom muqovasi).

## Papkalar

```
core/settings.py        sozlamalar (.env dan o'qiydi)
core/urls.py            asosiy manzillar -> music.urls
music/models.py         4 ta model: Genre, Artist, Album, Song
music/admin.py          admin paneli (SongInline: albom ichida qo'shiqlar)
music/forms.py          ArtistForm, AlbumForm, SongForm
music/views.py          sahifalar mantiqi + ImportView
music/urls.py           manzillar
music/context_processors.py   footer uchun janrlar (har sahifada)
music/services/
    spotify.py          Spotify API (modellarni bilmaydi)
    deezer.py           Deezer API (modellarni bilmaydi)
    providers.py        qaysi xizmat ishlashini hal qiladi
    artwork.py          TheAudioDB — ijrochi rasmlari (cutout/banner/portret)
    importers.py        API dict -> Django modellari
music/templates/music/  shablonlar
    partials/_album_card.html    bitta albom kartasi
    partials/_form_fields.html   forma maydonlari (as_p o'rniga)
static/css/style.css    butun dizayn
static/js/app.js        mobil menyu + namuna pleyeri
media/                  yuklangan rasmlar
```

## Manzillar

| URL | Nomi | Template |
|---|---|---|
| `/` | `music:album_list` | `album_list.html` |
| `/?q=...` | qidiruv (albom **yoki** ijrochi) | — |
| `/?genre=<slug>` | janr filtri | — |
| `/albom/<ijrochi>/<albom>/` | `music:album_detail` | `album_detail.html` |
| `/albom/qoshish/` | `music:album_create` | `album_form.html` |
| `/albom/<pk>/qoshiq-qoshish/` | `music:song_create` | `song_form.html` |
| `/ijrochi/` | `music:artist_list` | `artist_list.html` |
| `/ijrochi/<slug>/` | `music:artist_detail` | `artist_detail.html` |
| `/ijrochi/qoshish/` | `music:artist_create` | `artist_form.html` |
| `/import/` | `music:import` | `import.html` |
| `/albom/<pk>/tahrirlash/` | `music:album_update` | `album_form.html` |
| `/albom/<pk>/ochirish/` | `music:album_delete` | `confirm_delete.html` |
| `/ijrochi/<slug>/tahrirlash/` | `music:artist_update` | `artist_form.html` |
| `/ijrochi/<slug>/ochirish/` | `music:artist_delete` | `confirm_delete.html` |
| `/qoshiq/<pk>/tahrirlash/` | `music:song_update` | `song_form.html` |
| `/qoshiq/<pk>/ochirish/` | `music:song_delete` | `confirm_delete.html` |
| `/takliflar/?q=...` | `music:suggest` | JSON (shablon yo'q) |
| `/chiqish/` | `music:logout` | — (faqat POST) |

**DIQQAT:** `albom/<pk>/tahrirlash/` va `ochirish/` manzillari `urls.py` da
`album_detail` dan **yuqorida** turishi shart. `album_detail` manzili
`<slug>/<slug>` ko'rinishida, slug esa raqamni ham qabul qiladi —
aks holda `albom/5/tahrirlash/` noto'g'ri yo'lga tushib ketadi.

## CRUD jadvali

| Model | Ko'rish | Qo'shish | Tahrirlash | O'chirish |
|---|---|---|---|---|
| Albom | ✅ ro'yxat + sahifa | ✅ forma + katalog | ✅ | ✅ tasdiqlash bilan |
| Ijrochi | ✅ ro'yxat + sahifa | ✅ | ✅ | ✅ tasdiqlash bilan |
| Qo'shiq | ✅ albom ichida | ✅ | ✅ | ✅ tasdiqlash bilan |

O'chirish faqat **POST** so'rovda bajariladi: GET da tasdiqlash sahifasi
chiqadi. Busiz qidiruv roboti yoki brauzerning oldindan yuklash
funksiyasi havolani ochib, yozuvni o'chirib yuborishi mumkin edi.

Qo'shiq qatoridagi tahrir/o'chirish tugmalari qatorga sichqoncha
kelgandagina ko'rinadi (`.row-actions`).

## Avtoto'ldirish

`/takliflar/?q=...` JSON qaytaradi: mos albomlar va ijrochilar.
Ikki harfdan qisqa so'rovga bo'sh javob beradi — har bosilgan tugmada
bazaga so'rov ketmasligi uchun. JS tomonda yana 200 ms "debounce" bor.

Ikki joyda ishlatiladi:

- **Tepadagi qidiruv** (`[data-suggest]`) — rasmli ro'yxat chiqadi,
  bosilganda to'g'ridan-to'g'ri albom/ijrochi sahifasiga o'tadi.
  Klaviatura bilan ham boshqariladi (↑ ↓ Enter Esc).
- **Albom formasidagi ijrochi maydoni** — `<select>` qidiruvli ro'yxatga
  aylantiriladi. Select o'chirilmaydi, faqat yashiriladi: JavaScript
  ishlamasa forma baribir ishlayveradi.

## Modellardagi tashqi maydonlar

`Artist`, `Album`, `Song` da uchtadan maydon bor:

- `source` — `manual` / `spotify` / `deezer`
- `external_id` — o'sha xizmatdagi ID
- `Song.preview_url` — 30 soniyalik mp3 (Deezer beradi, Spotify yo'q)

`source` + `external_id` **birgalikda** unikal: Spotify'dagi "123" bilan
Deezer'dagi "123" boshqa-boshqa narsa. `external_id` bo'sh bo'lsa cheklov
ishlamaydi, shuning uchun qo'lda kiritilgan yozuvlarni istagancha qo'shish
mumkin.

## Kirish talab qilinadi

Sayt **yopiq**: tizimga kirmagan odam faqat kirish va ro'yxatdan o'tish
sahifalarini ko'radi, qolgan hamma manzil `/kirish/` ga yo'naltiriladi.

Buni Django ning tayyor `LoginRequiredMiddleware` i bajaradi
(`settings.py` dagi MIDDLEWARE ro'yxatida). Istisnolar
`@login_not_required` bilan belgilangan:

| Nima | Qayerda | Nega ochiq |
|---|---|---|
| `/kirish/` | `music/urls.py` | Aks holda cheksiz aylanma bo'lardi |
| `/royxatdan-otish/` | `SignupView` | Yangi odam hali kirmagan |
| `/google-kirish/` | `google_login()` | Kirish jarayonining bir qismi |
| `/chiqish/` | `logout_view()` | Chiqayotgan odam uchun |
| `/media/...` | `core/urls.py` | Rasmlar; static fayllar runserver tomonidan middleware dan oldin beriladi |

Kirgandan keyin odam qaysi sahifaga bormoqchi bo'lgan bo'lsa,
o'sha yerga qaytariladi.

### Nega manzilda `?next=` yo'q

Django ning tayyor `LoginRequiredMiddleware` i manzilga qo'shimcha
yozadi: `/kirish/?next=/ijrochi/`. Ishlaydi, lekin manzil chiroyli emas.

`music/middleware.py` dagi `KirishTalabMiddleware` xuddi shu ma'lumotni
manzilga emas, **sessiyaga** yozadi. Natijada manzil toza `/kirish/`
bo'ladi, xatti-harakat esa o'zgarmaydi.

`KirishView.get_success_url()` uni sessiyadan o'qiydi. Manzilda
qo'lda `?next=...` yozilsa — e'tiborga olinmaydi, ya'ni begona saytga
yo'naltirish ("open redirect") imkoni yo'q.

Faqat **GET** so'rovlar eslab qolinadi: POST ni kirgandan keyin qayta
yuborib bo'lmaydi, shuning uchun bunday holda bosh sahifaga tushiladi.

## Egalik — kim nimani o'zgartira oladi

Har bir albom va ijrochida **egasi** bor (`owner`). Kim qo'shsa —
o'sha ega bo'ladi.

| Amal | Kim qila oladi |
|---|---|
| Ko'rish, tinglash, qidirish | Tizimga kirgan **har kim** |
| Yangi albom/ijrochi qo'shish | Har kim (o'ziniki bo'ladi) |
| Tahrirlash, o'chirish | Faqat **egasi** |
| Albomga qo'shiq qo'shish | Faqat albom egasi |
| Hammasini boshqarish | **Administrator** (superuser) |

Qo'shiqning alohida egasi yo'q — u turgan albomning egasi hisoblanadi.

Mavjud 65 albom va 37 ijrochi migratsiya orqali birinchi
administratorga biriktirilgan (`0005_egasiz_yozuvlarni_adminga_berish`).

**Ikki qavat himoya:** shablon begona odamga tugmalarni ko'rsatmaydi,
lekin asosiy himoya server tomonda — `EgalikTalabi` mixin `dispatch()`
ichida tekshiradi, ya'ni sahifa chizilmasdan oldin. Tugmani yashirish
o'zi himoya emas: manzilni qo'lda yozib kirish mumkin.

Import orqali qo'shilgan albom ham import qilgan odamga tegishli
bo'ladi. Terminaldan (`seed_albums`, `import_album`) qo'shilganda
birinchi administratorga.

## Profil oynasi

Tepa o'ngdagi avatar bosilganda akkaunt paneli ochiladi: foydalanuvchi
ismi, e-pochtasi, "Administrator" belgisi (agar `is_staff` bo'lsa),
bazadagi albom/ijrochi/qo'shiq soni va tezkor havolalar.

Tizimga kirmagan bo'lsa — "Mehmon" deb ko'rsatadi va kirish havolasini
beradi.

**Chiqish faqat POST bilan** bajariladi (`music:logout`). Oddiy havola
bo'lsa brauzerning oldindan yuklash funksiyasi foydalanuvchini o'zi
bilmagan holda tizimdan chiqarib yuborishi mumkin edi. GET bilan
kelganda hech narsa qilmay bosh sahifaga qaytaradi.

Paneldagi raqamlar `context_processors.py` dan keladi — ya'ni **har
sahifada** uchta `COUNT` so'rovi ketadi. Baza kattalashsa keshga olish
kerak bo'ladi.

## Dizayn

Qorong'i tema. Ranglar `static/css/style.css` ning boshida `:root` ichida —
bitta joydan butun sayt rangini o'zgartirsa bo'ladi.

Namuna pleyeri ikki joydan ishga tushadi:

- **qo'shiqlar ro'yxatida** — qo'shiq yonidagi ▶
- **albom muqovasida** — albomning birinchi qo'shig'i chalinadi

Ikkovi bitta pleyerni boshqaradi: yangisi bosilsa avvalgisi to'xtaydi.
Probel tugmasi — to'xtatish/davom ettirish.

Muqovadagi tugma uchun har bir albomga birinchi qo'shig'ining namunasi
`preview_qoshish()` (views.py) orqali `Subquery` bilan qo'shiladi —
bitta so'rovda. Shablonda `album.songs.first` yozilsa har bir karta
uchun alohida so'rov ketardi (N+1 muammosi).

Karta `<div>`, havola esa `card__link::after` orqali butun kartani
qoplaydi. Sababi — havola ichiga tugma joylash HTML qoidasiga zid:
bosilganda ikkalasi ham ishlab ketardi. Tugma `z-index` bilan
qoplamaning ustida turadi.

Sensorli ekranda "hover" yo'q, shuning uchun `@media (hover: none)` da
tugma doim ko'rinadi.

Hero rasmiga maska qo'yilgan: chap, o'ng va pastki chekkasi fonga
singib ketadi (`mask-composite: intersect` bilan ikkita gradient).
Sababi — TheAudioDB dagi "cutout" rasmlarning hammasi ham to'liq
shaffof emas (masalan The Beatles rasmining pastki burchaklari
to'ldirilgan), maskasiz to'rtburchak chizig'i ko'rinib qolardi.

Bosh sahifadagi slayder 10 ta albomni har 6 soniyada almashtiradi.
Sarlavha o'lchami nom UZUNLIGIGA qarab tanlanadi (`hero__title--sm`,
`hero__title--xs`) — faqat ekran kengligiga bog'lasak, uzun nom to'rt
qatorga bo'linib hero dan oshib ketardi.
Sichqoncha ustida turganda va varaq fonda bo'lganda to'xtaydi.
Nuqtalar bosilsa sanoq yangidan boshlanadi.
