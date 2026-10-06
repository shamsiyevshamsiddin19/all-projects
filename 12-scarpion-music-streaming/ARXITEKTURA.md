# Fayl arxitekturasi

SCARPION Music loyihasidagi har bir faylning vazifasi.
Qator sonlari 2026-yil 15-sentabr holatiga ko'ra.

---

## Umumiy tuzilish

```
alboms/
│
├── manage.py                            22  Django buyruqlarini ishga tushiruvchi
├── requirements.txt                     15  kutubxonalar ro'yxati
├── ishga-tushir.ps1                    306  Windows uchun: hammasini o'rnatib ishga tushiradi
├── README.md                           385  o'rnatish va ishlatish yo'riqnomasi
├── ARXITEKTURA.md                      358  shu fayl
├── .env                                     maxfiy sozlamalar — git'ga TUSHMAYDI
├── .env.example                         45  .env uchun namuna (git'da bor)
├── .gitignore                           14  git nimalarni e'tiborsiz qoldirishi
├── db.sqlite3                               baza — git'ga tushmaydi
│
├── .vscode/                                 VS Code sozlamalari (F5 bilan ishga tushirish)
│   ├── launch.json                      39  uchta tayyor konfiguratsiya
│   └── settings.json                    23  shablonlarni django-html deb tanish
│
├── core/                                    LOYIHA KARKASI
│   ├── settings.py                     229  barcha sozlamalar, .env dan o'qiydi
│   ├── urls.py                          40  /admin/ va qolganini music.urls ga uzatadi
│   ├── wsgi.py                          16  serverga ulanish nuqtasi
│   ├── asgi.py                          16  asinxron ulanish nuqtasi
│   └── __init__.py                       0  papkani Python moduli qiladi
│
├── music/                                   ASOSIY ILOVA — butun mantiq shu yerda
│   │
│   ├── models.py                       447  4 ta model: Genre, Artist, Album, Song
│   ├── views.py                        819  sahifalar mantiqi + egalik tekshiruvi
│   ├── urls.py                          69  manzil -> view bog'lanishi
│   ├── forms.py                        206  albom/ijrochi/qo'shiq + kirish/ro'yxat formalari
│   ├── admin.py                         82  admin panel sozlamalari
│   ├── apps.py                           5  ilova nomi
│   ├── middleware.py                    44  saytga kirish uchun login talab qiladi
│   ├── auth_backends.py                 45  e-pochta bilan ham kirish
│   ├── password_validators.py           92  parol qoidalari, o'zbekcha xabarlar
│   ├── context_processors.py            51  har sahifaga: janrlar, statistika, Firebase
│   │
│   ├── services/                            TASHQI XIZMATLAR
│   │   ├── deezer.py                   144  Deezer API — kalitsiz, asosiy manba
│   │   ├── spotify.py                  181  Spotify API — bir xil interfeys, zaxira
│   │   ├── providers.py                 58  qaysi xizmat ishlashini hal qiladi
│   │   ├── artwork.py                   91  TheAudioDB — ijrochi rasmlari
│   │   ├── importers.py                279  API dict -> Django modellari (tarjimon)
│   │   └── __init__.py                   0
│   │
│   ├── management/commands/                 TERMINAL BUYRUQLARI
│   │   ├── seed_albums.py              247  bazani mashhur albomlar bilan to'ldiradi
│   │   ├── import_album.py              67  bitta albomni import qiladi
│   │   ├── fetch_artist_art.py          78  ijrochi rasmlarini oladi
│   │   └── __init__.py                   0
│   │
│   ├── migrations/                          BAZA O'ZGARISHLARI TARIXI
│   │   ├── 0001_initial.py              88  dastlabki 4 ta jadval
│   │   ├── 0002_..._spotify_id_...py    72  spotify_id -> source + external_id
│   │   ├── 0003_artist_banner_...py     23  Artist.cutout va Artist.banner
│   │   ├── 0004_album_owner_...py       26  owner maydoni (kim qo'shgan)
│   │   ├── 0005_egasiz_...py            54  mavjud yozuvlarni adminga biriktiradi
│   │   └── __init__.py                   0
│   │
│   └── templates/music/                     SAHIFALAR
│       ├── base.html                   220  BARCHA sahifalarning asosi
│       ├── album_list.html             239  bosh sahifa: slayder, grid, jadval
│       ├── album_detail.html           217  albom: qo'shiqlar, pleyer, ma'lumot
│       ├── artist_list.html             73  ijrochilar katalogi
│       ├── artist_detail.html           73  ijrochi va uning albomlari
│       ├── album_form.html              52  albom qo'shish VA tahrirlash
│       ├── artist_form.html             43  ijrochi qo'shish va tahrirlash
│       ├── song_form.html               54  qo'shiq qo'shish va tahrirlash
│       ├── confirm_delete.html          39  o'chirishni tasdiqlash (3 model uchun bitta)
│       ├── import.html                 110  katalogdan albom qidirish
│       │
│       ├── auth_base.html              114  kirish sahifalari qobig'i (base.html dan MEROS OLMAYDI)
│       ├── login.html                   38  kirish formasi
│       ├── signup.html                  38  ro'yxatdan o'tish formasi
│       │
│       └── partials/                         QAYTA ISHLATILADIGAN BO'LAKLAR
│           ├── _album_card.html         47  bitta albom kartasi — 4 joyda
│           ├── _form_fields.html        47  forma maydonlari (form.as_p o'rniga)
│           └── _google_button.html      36  "Google bilan kirish" + Firebase SDK
│
├── static/                                  BRAUZER FAYLLARI
│   ├── css/style.css                  1953  BUTUN DIZAYN — 15 ta raqamlangan bo'lim
│   └── js/
│       ├── app.js                      436  menyu, slayder, pleyer, avtoto'ldirish
│       └── firebase-auth.js            140  Google orqali kirish
│
└── media/                                   YUKLAB OLINGAN RASMLAR — git'ga tushmaydi
    ├── covers/                          65  albom muqovalari
    └── artists/                         37  ijrochi portretlari
        ├── cutouts/                     35  foni kesilgan PNG — hero uchun
        └── banners/                     37  keng suratlar — hero foni
```

**Asosiy qoida:** `core/` — loyihaning "karkasi", `music/` — uning
"go'shti". Yangi funksiya deyarli har doim `music/` ga qo'shiladi.

---

## `core/` — loyiha sozlamalari

| Fayl | Qator | Vazifasi |
|---|---|---|
| `settings.py` | 229 | Barcha sozlamalar: baza, ilovalar, shablon yo'llari, statik/media papkalari, `.env` dan o'qiladigan kalitlar (`MUSIC_PROVIDER`, `SPOTIFY_*`, `AUDIODB_KEY`), SQLite `timeout` |
| `urls.py` | 69 | Eng yuqori manzillar: `/admin/` va qolgan hammasini `music.urls` ga uzatadi. DEBUG rejimda media fayllarni ham tarqatadi |
| `wsgi.py` / `asgi.py` | 16+16 | Serverga ulanish nuqtalari. Django o'zi yaratgan, qo'l tegilmagan |
| `__init__.py` | 0 | Papkani Python moduliga aylantiradi |

---

## `music/` — asosiy ilova

### Ma'lumot qatlami

| Fayl | Qator | Vazifasi |
|---|---|---|
| `models.py` | 447 | **4 ta model + 1 ta ro'yxat.** `Source` (manba turlari), `Genre`, `Artist`, `Album`, `Song`. Bazadagi jadvallar shu yerdan tug'iladi |
| `migrations/0001_initial.py` | 88 | Dastlabki 4 ta jadval |
| `migrations/0002_...spotify_id...` | 72 | `spotify_id` → `source` + `external_id`, `Song.preview_url` qo'shildi |
| `migrations/0003_artist_banner_cutout.py` | 23 | `Artist.cutout` va `Artist.banner` qo'shildi |
| `migrations/0004_album_owner_artist_owner.py` | — | `owner` maydoni (kim qo'shgan) |
| `migrations/0005_egasiz_yozuvlarni_adminga_berish.py` | 54 | Mavjud yozuvlarni administratorga biriktiradi |

**`models.py` ichidagi muhim qismlar:**

- `make_unique_slug()` — takrorlanmaydigan slug yasaydi (`the-eminem-show-2`)
- `Genre.save()` — slug avtomatik yasaydi
- `Album.embed_url` / `external_url` — Deezer/Spotify pleyeri va sahifasi manzili
- `Album.hero_bg_url` / `hero_figure_url` / `hero_figure_is_cutout` — bosh sahifadagi katta rasm uchun uch xil manba (cutout → portret → muqova)
- `Song.duration_display` — `215000` → `3:35`

### Mantiq qatlami

| Fayl | Qator | Vazifasi |
|---|---|---|
| `views.py` | 819 | **16 ta view** (14 ta klass + 2 ta funksiya) va 1 ta yordamchi. Har bir sahifa qanday ma'lumot olishi va qaysi shablonni ishlatishi |
| `urls.py` | 69 | Manzil → view bog'lanishi. Tartib MUHIM (pastga qarang) |
| `forms.py` | 206 | `ArtistForm`, `AlbumForm`, `SongForm` — maydonlar, yorliqlar va tekshiruvlar |
| `context_processors.py` | 51 | HAR bir sahifaga avtomatik qo'shiladigan ma'lumot: footer janrlari va profil oynasidagi raqamlar |
| `auth_backends.py` | 45 | E-pochta bilan ham kirish imkonini beradi. Django sukut bo'yicha faqat `username` ni qabul qiladi |
| `middleware.py` | 44 | Saytga kirish uchun login talab qiladi. Django nikidan farqi — "qayerga bormoqchi edingiz" ni manzilga (`?next=`) emas, sessiyaga yozadi |

**Sayt yopiq:** `LoginRequiredMiddleware` butun saytga kirish uchun login
talab qiladi. Istisnolar `@login_not_required` bilan belgilangan —
kirish, ro'yxatdan o'tish, Google kirish, chiqish va `/media/`.
| `admin.py` | 82 | Django admin paneli sozlamalari (`SongInline` — albom ichida qo'shiqlar) |
| `apps.py` | 5 | Ilova nomi |

**`views.py` tarkibi:**

| Nomi | Turi | Vazifasi |
|---|---|---|
| `preview_qoshish()` | yordamchi | Har bir albomga birinchi qo'shig'ining namunasini `Subquery` bilan qo'shadi (N+1 muammosining oldini oladi) |
| `AlbumListView` | ro'yxat | Bosh sahifa: hero slayderi, "Top albomlar" qatori, grid, qidiruv, janr filtri, sahifalash |
| `AlbumDetailView` | sahifa | Bitta albom: qo'shiqlar, Deezer pleyeri, boshqa albomlari |
| `ArtistListView` | ro'yxat | Ijrochilar katalogi + qidiruv |
| `ArtistDetailView` | sahifa | Bitta ijrochi va uning albomlari |
| `AlbumCreateView` / `UpdateView` / `DeleteView` | CRUD | Albom qo'shish / tahrirlash / o'chirish |
| `ArtistCreateView` / `UpdateView` / `DeleteView` | CRUD | Ijrochi uchun o'shalar |
| `SongCreateView` / `UpdateView` / `DeleteView` | CRUD | Qo'shiq uchun o'shalar |
| `ImportView` | maxsus | Katalogdan qidirib albom qo'shish (GET — qidiradi, POST — import qiladi) |
| `suggest()` | JSON | Qidiruv maydoni uchun takliflar. Sahifa emas, JSON qaytaradi |
| `SignupView` | CRUD | Ro'yxatdan o'tish. Muvaffaqiyatli bo'lsa darhol tizimga kiritadi |
| `google_login()` | JSON | Brauzerdan kelgan Firebase ID tokenini **serverda tekshirib** tizimga kiritadi |
| `logout_view()` | maxsus | Tizimdan chiqish. **Faqat POST** qabul qiladi |

Kirish uchun alohida view yozilmagan — Django'ning tayyor `LoginView`i
ishlatiladi (`urls.py` da sozlangan), faqat shablon va forma
o'zimizniki.

**`urls.py` dagi tartib qoidasi:**

```
albom/<int:pk>/tahrirlash/     <- YUQORIDA turishi SHART
albom/<slug>/<slug>/           <- pastda
```

Sababi: `slug` raqamni ham qabul qiladi. Tartib teskari bo'lsa
`albom/5/tahrirlash/` albom sahifasi deb qabul qilinib, 404 berardi.

### Tashqi xizmatlar qatlami — `music/services/`

Bu papkaning **bosh qoidasi:** `deezer.py` va `spotify.py` Django
modellarini BILMAYDI. Ular faqat oddiy `dict` qaytaradi. Shuning uchun
API o'zgarsa, faqat shu ikki fayl o'zgaradi.

| Fayl | Qator | Vazifasi |
|---|---|---|
| `deezer.py` | 144 | Deezer API. Kalit kerak emas. `search_albums`, `get_album`, `get_artist`. 30 soniyalik namuna manzilini ham beradi |
| `spotify.py` | 181 | Spotify API. Aynan o'sha metodlar, aynan o'sha `dict` shakli. Hozir ishlamaydi (egasida Premium yo'q → 403) |
| `providers.py` | 58 | Qaysi xizmat ishlashini hal qiladi. `.env` dagi `MUSIC_PROVIDER` ga qaraydi. Bitta qator o'zgarsa butun loyiha boshqa xizmatga o'tadi |
| `artwork.py` | 91 | TheAudioDB — ijrochi rasmlari: `cutout` (foni kesilgan PNG), `fanart` (keng banner), `thumb` (portret) |
| `importers.py` | 279 | **Tarjimon qatlami.** API `dict` ini Django modellariga aylantiradi. Rasm yuklaydi, albom nomini tozalaydi, qo'shiqlarni bitta so'rovda yozadi |

**`importers.py` ichidagi muhim funksiyalar:**

- `clean_album_title()` — `"Nevermind (Remastered)"` → `"Nevermind"`
- `parse_release_date()` — `"2002"`, `"2002-05"`, `"2002-05-26"` ni to'liq sanaga aylantiradi
- `download_image()` — rasmni yuklab Django fayliga aylantiradi
- `get_or_create_artist()` — ijrochini topadi yoki yaratadi, rasmlarini oladi
- `fetch_artist_artwork()` — TheAudioDB dan cutout/banner/portret
- `import_album()` — hammasini birlashtiradi. `@transaction.atomic` — yo hammasi, yo hech narsa

### Terminal buyruqlari — `music/management/commands/`

| Fayl | Qator | Buyruq | Vazifasi |
|---|---|---|---|
| `seed_albums.py` | 247 | `seed_albums` | Bazani 60+ mashhur albom bilan to'ldiradi. Karaoke/tribute/jonli yozuvlarni filtrlaydi |
| `import_album.py` | 67 | `import_album` | Bitta albomni ID yoki nom bo'yicha import qiladi |
| `fetch_artist_art.py` | 78 | `fetch_artist_art` | Mavjud ijrochilarga TheAudioDB dan rasm qo'shadi |

### Shablonlar — `music/templates/music/`

| Fayl | Qator | Vazifasi |
|---|---|---|
| `base.html` | 220 | **Barcha sahifalarning asosi.** Header (menyu, qidiruv, profil oynasi), xabarlar, footer, pastdagi pleyer |
| `album_list.html` | 239 | Bosh sahifa: hero slayderi (10 ta albom), "Top albomlar" qatori, janr chiplari, grid, jadval |
| `album_detail.html` | 217 | Albom sahifasi: muqova, qo'shiqlar ro'yxati, Deezer pleyeri, "Albom haqida" jadvali |
| `artist_list.html` | 73 | Ijrochilar katalogi (dumaloq rasmlar) |
| `artist_detail.html` | 73 | Ijrochi sahifasi va uning albomlari |
| `album_form.html` | 52 | Albom qo'shish **va** tahrirlash (bitta shablon ikkalasiga) |
| `artist_form.html` | 43 | Ijrochi qo'shish va tahrirlash |
| `song_form.html` | 54 | Qo'shiq qo'shish va tahrirlash |
| `confirm_delete.html` | 39 | O'chirishni tasdiqlash. Uchala model uchun ham bitta shablon |
| `import.html` | 110 | Katalogdan qidirib albom qo'shish |
| `partials/_album_card.html` | 47 | **Bitta albom kartasi.** 4 joyda ishlatiladi |
| `partials/_form_fields.html` | 47 | Forma maydonlarini qo'lda chizadi (`{{ form.as_p }}` o'rniga) |
| `auth_base.html` | 114 | Kirish/ro'yxat sahifalarining qobig'i: gradient fon, binolar siluetlari, uchuvchi notalar, dumaloq rasm. **`base.html` dan meros olmaydi** — menyu va footer kerak emas |
| `login.html` | 38 | Kirish formasi |
| `signup.html` | 38 | Ro'yxatdan o'tish formasi |
| `partials/_google_button.html` | 36 | "Google bilan kirish" tugmasi + Firebase SDK ulanishi |

**Nega `partials/`?** Albom kartasi to'rt joyda bir xil ko'rinadi.
Bitta faylda saqlansa, o'zgartirish ham bitta joyda bo'ladi.

---

## `static/` — brauzer fayllari

| Fayl | Qator | Vazifasi |
|---|---|---|
| `css/style.css` | 1953 | **Butun dizayn.** 14 ta raqamlangan bo'lim |
| `js/app.js` | 436 | **Butun jonli qism.** Kutubxona ishlatilmagan, sof JavaScript |
| `js/firebase-auth.js` | 140 | Google orqali kirish. `type="module"` bilan yuklanadi, Firebase SDK Google CDN sidan keladi |

**`style.css` bo'limlari:**

| № | Bo'lim | Nima bor |
|---|---|---|
| 1 | Ranglar | `:root` dagi o'zgaruvchilar. **Gradientni shu yerda o'zgartirsangiz butun sayt o'zgaradi** |
| 2 | Asos | reset, tipografiya, `.wrap`, tugmalar |
| 3 | Header | menyu, qidiruv tabletkasi, avatar, profil oynasi |
| 4 | Hero | slayder, rasm maskalari, sarlavha o'lchamlari |
| 5 | Bo'lim sarlavhalari | "Top **albomlar**" uslubi |
| 6 | Albom kartalari | grid, `.rail`, play tugmasi, janr chiplari |
| 7 | Top albomlar jadvali | raqamlangan ro'yxat |
| 8 | Ijrochi kartalari | dumaloq rasmlar |
| 9 | Albom sahifasi | muqova bloki, qo'shiqlar jadvali |
| 10 | Formalar | maydonlar, chiplar, xatolar |
| 11 | Qidiruv + import | avtoto'ldirish ro'yxati, eslatma |
| 12 | Xabarlar, sahifalash, footer | |
| 13 | Pastdagi pleyer | |
| 14 | Mobil | `@media` qoidalari |
| 15 | Kirish sahifalari | gradient fon, binolar, notalar, oq "tabletka" inputlar, Google tugmasi |

**`app.js` bo'limlari:**

| № | Bo'lim | Vazifasi |
|---|---|---|
| 1 | Mobil menyu | burger tugmasi |
| 2 | Hero slayderi | 10 ta albom, 6 soniyada almashadi, sichqoncha ustida to'xtaydi |
| 2b | Profil oynasi | avatar bosilganda ochiladi |
| 3 | Pleyer | namuna chalish. Qo'shiq ro'yxati va muqova tugmalari bitta pleyerni boshqaradi |
| 4 | Qidiruvda avtoto'ldirish | serverdan taklif so'raydi, klaviatura bilan boshqariladi |
| 5 | Ijrochi maydonida avtoto'ldirish | `<select>` ni qidiruvli ro'yxatga aylantiradi |

**Muhim:** har bir bo'lim o'z IIFE'si ichida. Birida `return` bo'lsa
qolganlari ishlayveradi.

---

## `media/` — yuklab olingan rasmlar

| Papka | Fayl | Nima |
|---|---|---|
| `covers/` | 77 | Albom muqovalari |
| `artists/` | 46 | Ijrochi portretlari (kvadrat) |
| `artists/cutouts/` | 38 | Foni kesilgan shaffof PNG — hero dagi asosiy rasm |
| `artists/banners/` | 40 | Keng suratlar — hero orqa foni |

Bu papka `.gitignore` da. Rasmlar import paytida qaytadan yuklanadi.

**Diqqat:** fayllar soni albomlar sonidan ko'p (77 fayl / 65 albom).
Sababi — Django yozuv o'chirilganda unga bog'langan faylni O'CHIRMAYDI.
Bu xato emas, Django'ning ataylab qilingan xatti-harakati: bir fayl
bir necha yozuvda ishlatilayotgan bo'lishi mumkin. Kerak bo'lsa
egasiz fayllarni alohida tozalash kerak.

---

## Ma'lumot qanday oqadi

Albom import qilinganda:

```
ImportView (views.py)
        ↓
import_album() (services/importers.py)
        ↓
get_client() (services/providers.py)  →  .env dagi MUSIC_PROVIDER ga qaraydi
        ↓
DeezerClient.get_album() (services/deezer.py)  →  oddiy dict qaytaradi
        ↓
importers.py dict ni modellarga aylantiradi:
    • clean_album_title() — nomni tozalaydi
    • get_or_create_artist() — ijrochini topadi/yaratadi
    • fetch_artist_artwork() (services/artwork.py) — cutout/banner oladi
    • download_image() — muqovani yuklaydi
        ↓
models.py  →  baza
```

Sahifa ochilganda:

```
Brauzer  →  core/urls.py  →  music/urls.py  →  views.py
                                                   ↓
                                        models.py dan ma'lumot oladi
                                                   ↓
                                        context_processors.py qo'shimcha qo'shadi
                                                   ↓
                                        templates/ shabloni chizadi
                                                   ↓
                                        static/ dagi CSS va JS bezaydi
```

---

## Nima qayerga qo'shiladi

| Vazifa | Qaysi faylga |
|---|---|
| Yangi maydon (masalan albomga "izoh") | `models.py` + migratsiya + `forms.py` + shablon |
| Yangi sahifa | `views.py` + `urls.py` + `templates/` |
| Yangi musiqa xizmati | `services/` ga yangi fayl + `providers.py` ga bitta qator |
| Rang yoki o'lcham | `static/css/style.css`, 1-bo'lim |
| Yangi jonli xatti-harakat | `static/js/app.js`, yangi IIFE |
| Har sahifada kerak bo'ladigan ma'lumot | `context_processors.py` |
| Terminal buyrug'i | `music/management/commands/` |
