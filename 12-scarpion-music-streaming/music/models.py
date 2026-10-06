# Django'ning baza bilan ishlaydigan asboblar to'plamini chaqiramiz.
# Shundan keyin "models.CharField", "models.ForeignKey" deb yoza olamiz.
from django.conf import settings
from django.db import models
# reverse() = URL nomidan haqiqiy manzil yasaydi ("music:album_detail" -> "/albom/eminem/...")
from django.urls import reverse
# slugify() = "The Eminem Show" -> "the-eminem-show"
from django.utils.text import slugify


# ----------------------------------------------------------
# Yordamchi funksiya: takrorlanmaydigan slug yasaydi.
# Agar "the-eminem-show" band bo'lsa, "the-eminem-show-2" qaytaradi.
#   value    - qaysi matndan yasaymiz (albom nomi yoki ijrochi ismi)
#   queryset - qayerda tekshiramiz (band-emasligini shu yerda qidiradi)
#   fallback - matn butunlay yaroqsiz bo'lsa (masalan "!!!") shu ishlatiladi
# ----------------------------------------------------------
def make_unique_slug(value, queryset, fallback='element'):
    base = slugify(value) or fallback
    slug = base
    counter = 2
    while queryset.filter(slug=slug).exists():
        slug = f'{base}-{counter}'
        counter += 1
    return slug


# ==========================================================
#  MANBA — yozuv qayerdan kelgani.
#  models.TextChoices = "faqat shu qiymatlardan biri bo'lsin" ro'yxati.
#  Chapdagi ('deezer') bazaga yoziladi, o'ngdagi ('Deezer') formada ko'rinadi.
# ==========================================================
class Source(models.TextChoices):
    MANUAL = 'manual', "Qo'lda"
    SPOTIFY = 'spotify', 'Spotify'
    DEEZER = 'deezer', 'Deezer'


# ==========================================================
#  1) JANR — eng sodda model. Qolgan 3 tasi shu shakl asosida.
# ==========================================================
# "class" = yangi model e'lon qilyapmiz.
# "Genre" = model nomi (bosh harf bilan, birlikda).
# "(models.Model)" = Django modelidan meros olyapmiz —
#     AYNAN shu qism Django'ga "bazada jadval yarat" deb aytadi.
# Oxiridagi ":" = "pastda shu klassning ichi boshlanadi".
class Genre(models.Model):

    # name = janr nomi. Masalan: "Rok"
    #   models.CharField  -> qisqa matn uchun ustun (bazada VARCHAR)
    #   max_length=100    -> ko'pi bilan 100 ta belgi (CharField'da MAJBURIY)
    #   unique=True       -> bazada ikkita bir xil janr bo'lmasin
    name = models.CharField(max_length=100, unique=True)

    # slug = URL uchun xavfsiz nom. "Hip Hop" -> "hip-hop"
    #   Natijada manzil chiroyli bo'ladi: /janr/hip-hop/
    #   SlugField faqat harf, raqam, "-" va "_" ga ruxsat beradi.
    slug = models.SlugField(max_length=100, unique=True)

    # "class Meta" MAYDON EMAS. Bu — modelning o'zi haqidagi sozlama.
    # Diqqat: u Genre klassining ICHIDA turadi (4 probel surilgan).
    class Meta:
        # Genre.objects.all() chaqirilganda alifbo tartibida kelsin.
        # Oldiga "-" qo'ysak ('-name') teskari tartib bo'lardi.
        ordering = ['name']
        # Admin panelda "Genre" emas, o'zbekcha ko'rinsin:
        verbose_name = 'Janr'            # birlikda
        verbose_name_plural = 'Janrlar'  # ko'plikda

    # Artist va Album dagi kabi — slug bo'sh bo'lsa nomdan yasaladi.
    # Busiz ikkinchi janr qo'shilganda ikkovining ham slug'i bo'sh bo'lib
    # qoladi va unique=True sababli IntegrityError chiqadi.
    # (Admin panelda prepopulated_fields ishlaydi, lekin u faqat brauzerdagi
    #  formaga tegishli — API orqali kelgan janrga yordam bermaydi.)
    def save(self, *args, **kwargs):
        if not self.slug:
            qs = Genre.objects.all()
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            self.slug = make_unique_slug(self.name, qs, 'janr')
        super().save(*args, **kwargs)

    # __str__ = "bu yozuvni matn sifatida qanday ko'rsatay?" degan savolga javob.
    # Busiz admin panelda "Genre object (1)" deb chiqadi — foydasiz.
    # "self" = shu aniq yozuvning o'zi. self.name = shu yozuvning name maydoni.
    def __str__(self):
        return self.name


# ==========================================================
#  2) IJROCHI
# ==========================================================
class Artist(models.Model):

    # Ijrochi ismi. Bu yerda unique=True YO'Q —
    # chunki dunyoda bir xil ismli ijrochilar uchraydi.
    name = models.CharField(max_length=200)

    # URL uchun: /ijrochi/eminem/
    slug = models.SlugField(max_length=200, unique=True)

    # Biografiya — uzun matn (bir necha abzas) uchun TextField.
    #   blank=True -> formada bu katakni bo'sh qoldirsa ham bo'ladi.
    #   Matn maydonlarida null=True YOZILMAYDI (bo'shlik ikki xil
    #   ma'noga ega bo'lib qolmasligi uchun: '' va NULL).
    bio = models.TextField(blank=True)

    # Ijrochi rasmi.
    #   DIQQAT: bazaga rasmning O'ZI emas, faqat YO'LI (matn) yoziladi.
    #   Rasmning o'zi diskda, media/ papkasida yotadi.
    #   upload_to='artists/' -> fayl media/artists/ ichiga tushadi.
    #   blank=True  -> forma bo'sh qoldirishga ruxsat beradi
    #   null=True   -> bazada bo'sh (NULL) bo'lishiga ruxsat beradi
    photo = models.ImageField(upload_to='artists/', blank=True, null=True)

    # --- Bosh sahifadagi katta blok (hero) uchun rasmlar ---
    # Ikkalasi ham TheAudioDB dan keladi (services/artwork.py).
    #   cutout — foni KESILGAN shaffof PNG. Odam qora fonda "suzadi",
    #            aynan shu ko'rinish kerak edi.
    #   banner — keng surat (1920x1080). Orqa fon uchun: kvadrat
    #            rasmni cho'zgandan ko'ra ancha toza chiqadi.
    # Ikkovi ham bo'sh bo'lishi mumkin: kam tanilgan ijrochi
    # TheAudioDB da topilmaydi. Unda photo/muqova ishlatiladi.
    cutout = models.ImageField(upload_to='artists/cutouts/', blank=True, null=True)
    banner = models.ImageField(upload_to='artists/banners/', blank=True, null=True)

    # --- Egasi ---
    # Kim qo'shgan bo'lsa — o'sha. Faqat egasi (va admin) o'zgartira
    # yoki o'chira oladi; ko'rishni hamma ko'raveradi.
    #
    # on_delete=SET_NULL: foydalanuvchi o'chirilsa albom o'chmasin,
    # shunchaki egasiz qolsin. CASCADE bo'lsa bitta odamni o'chirish
    # butun katalogni olib ketardi.
    # null=True: eski yozuvlar va egasiz qolganlar uchun.
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='owned_artists',
        verbose_name='Egasi',
    )

    # --- Tashqi xizmat ma'lumotlari (Spotify / Deezer) ---
    # source      = qaysi xizmatdan kelgan ('manual' = qo'lda kiritilgan)
    # external_id = o'sha xizmatdagi ID si
    # Ikkovi BIRGALIKDA unikal (pastdagi constraints ga qarang), chunki
    # Spotify'dagi "123" bilan Deezer'dagi "123" butunlay boshqa narsa.
    # external_id NULL bo'lsa cheklov ishlamaydi — shuning uchun qo'lda
    # kiritilgan yozuvlarni istagancha qo'shaverish mumkin.
    source = models.CharField(
        max_length=20, choices=Source.choices, default=Source.MANUAL
    )
    external_id = models.CharField(max_length=50, blank=True, null=True)

    # Yozuv birinchi marta yaratilgan vaqt.
    #   auto_now_add=True -> Django o'zi to'ldiradi va boshqa hech qachon
    #   o'zgartirmaydi. Avtomatik bo'lgani uchun blank=True kerak emas.
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['source', 'external_id'],
                name='uniq_artist_external',
            ),
        ]
        verbose_name = 'Ijrochi'
        verbose_name_plural = 'Ijrochilar'

    def save(self, *args, **kwargs):
        if not self.slug:
            qs = Artist.objects.all()
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            self.slug = make_unique_slug(self.name, qs, 'ijrochi')
        super().save(*args, **kwargs)

    # get_absolute_url = "shu yozuvning sahifasi qayerda?"
    # Django buni o'zi ishlatadi: forma saqlangach shu manzilga yo'naltiradi.
    # 'music:artist_detail' -> music/urls.py dagi app_name + URL nomi.
    def get_absolute_url(self):
        return reverse('music:artist_detail', args=[self.slug])

    def __str__(self):
        return self.name


# ==========================================================
#  3) ALBOM — eng murakkabi. Bog'lanishlar shu yerda.
# ==========================================================
class Album(models.Model):

    title = models.CharField(max_length=200)

    # DIQQAT: bu yerda unique=True YO'Q (Genre/Artist'dan farqi shu).
    # Sababi pastdagi Meta.constraints da tushuntirilgan.
    slug = models.SlugField(max_length=200)

    # ForeignKey = "bitta-ga-ko'p" bog'lanish.
    # Bitta ijrochining KO'P albomi bor, lekin bitta albom BITTA ijrochiniki.
    # Shuning uchun FK har doim "ko'p" tomonda — ya'ni Album ichida turadi.
    artist = models.ForeignKey(
        # Qaysi modelga bog'lanyapmiz. Qo'shtirnoqsiz, chunki Artist yuqorida yozilgan.
        Artist,
        # Ijrochi o'chirilmoqchi bo'lsa nima bo'lsin?
        #   PROTECT = albomi bor ekan, o'chirtirmaydi (xato beradi)
        #   CASCADE = ijrochi bilan birga albomlari ham o'chib ketardi
        # Bizga PROTECT — tasodifan ma'lumot yo'qotmaslik uchun.
        on_delete=models.PROTECT,
        # TESKARI yo'nalishga nom beradi:
        #   album.artist        -> albomdan ijrochiga (tabiiy yo'nalish)
        #   artist.albums.all() -> ijrochidan uning albomlariga  <-- shu nom
        # Yozmasak, xunuk "artist.album_set.all()" deb chaqirishga majbur bo'lardik.
        related_name='albums',
    )

    # Chiqqan sanasi. Faqat sana (vaqtsiz) -> DateField.
    release_date = models.DateField(blank=True, null=True)

    # Albom muqovasi. media/covers/ ichiga tushadi.
    cover = models.ImageField(upload_to='covers/', blank=True, null=True)

    # ManyToManyField = "ko'p-ga-ko'p".
    # Bitta albom bir necha janrda, bitta janrda bir necha albom bo'ladi.
    # Django buning uchun yashirin UCHINCHI jadval yaratadi.
    # DIQQAT: M2M da on_delete YO'Q (qaysi tomon o'chadi — noaniq),
    #         lekin blank=True bor.
    genres = models.ManyToManyField(Genre, blank=True, related_name='albums')

    # --- Egasi ---
    # Kim qo'shgan bo'lsa — o'sha. Faqat egasi (va admin) o'zgartira
    # yoki o'chira oladi; ko'rishni hamma ko'raveradi.
    #
    # on_delete=SET_NULL: foydalanuvchi o'chirilsa albom o'chmasin,
    # shunchaki egasiz qolsin. CASCADE bo'lsa bitta odamni o'chirish
    # butun katalogni olib ketardi.
    # null=True: eski yozuvlar va egasiz qolganlar uchun.
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='owned_albums',
        verbose_name='Egasi',
    )

    # --- Tashqi xizmat ma'lumotlari (Spotify / Deezer) ---
    # source      = qaysi xizmatdan kelgan ('manual' = qo'lda kiritilgan)
    # external_id = o'sha xizmatdagi ID si
    # Ikkovi BIRGALIKDA unikal (pastdagi constraints ga qarang), chunki
    # Spotify'dagi "123" bilan Deezer'dagi "123" butunlay boshqa narsa.
    # external_id NULL bo'lsa cheklov ishlamaydi — shuning uchun qo'lda
    # kiritilgan yozuvlarni istagancha qo'shaverish mumkin.
    source = models.CharField(
        max_length=20, choices=Source.choices, default=Source.MANUAL
    )
    external_id = models.CharField(max_length=50, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Eng yangi albom birinchi chiqsin. "-" = teskari tartib.
        ordering = ['-release_date']

        # constraints = bazaning o'zi tekshiradigan qoidalar ro'yxati.
        # Bu yerda: bitta ijrochi ichida bir xil slug ikki marta bo'lmasin.
        # Nega yuqorida slug'ga unique=True qo'ymadik?
        #   Chunki turli ijrochilarda bir xil nomli albom bo'lishi mumkin
        #   ("Greatest Hits"). Bizga kerak bo'lgani — faqat bitta ijrochi
        #   ICHIDA takrorlanmasligi. Shuning uchun ikki ustun BIRGALIKDA unikal.
        constraints = [
            models.UniqueConstraint(
                fields=['artist', 'slug'],           # qaysi ustunlar birgalikda
                name='uniq_album_slug_per_artist',   # qoidaning bazadagi nomi
            ),
            models.UniqueConstraint(
                fields=['source', 'external_id'],
                name='uniq_album_external',
            ),
        ]
        verbose_name = 'Albom'
        verbose_name_plural = 'Albomlar'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Slug "ijrochi + slug" birgalikda unikal (Meta.constraints).
        # Tahrirlashda ijrochi boshqasiga almashtirilsa, eski slug
        # YANGI ijrochida band bo'lib qolishi mumkin — shuni bilish
        # uchun asl ijrochini eslab qolamiz.
        self._original_artist_id = self.artist_id

    def save(self, *args, **kwargs):
        ijrochi_almashdimi = self.pk and self.artist_id != self._original_artist_id
        if not self.slug or ijrochi_almashdimi:
            # DIQQAT: bu yerda faqat SHU IJROCHINING albomlari orasida
            # tekshiramiz, chunki qoidamiz "ijrochi + slug" birgalikda unikal.
            qs = Album.objects.filter(artist=self.artist)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            self.slug = make_unique_slug(self.title, qs, 'albom')
        super().save(*args, **kwargs)
        self._original_artist_id = self.artist_id

    # Manzil ikki qismdan iborat: /albom/<ijrochi-slug>/<albom-slug>/
    def get_absolute_url(self):
        return reverse('music:album_detail', args=[self.artist.slug, self.slug])

    # @property = "metod, lekin oddiy maydondek chaqiriladi".
    # Shablonda {{ album.embed_url }} deb yoziladi — qavssiz.
    # Bazada ustun yaratmaydi, har safar hisoblanadi.
    @property
    def embed_url(self):
        """Xizmatning o'z pleyeri (iframe ichiga qo'yiladi)."""
        if not self.external_id:
            return None
        if self.source == Source.DEEZER:
            return f'https://widget.deezer.com/widget/dark/album/{self.external_id}'
        if self.source == Source.SPOTIFY:
            return f'https://open.spotify.com/embed/album/{self.external_id}'
        return None

    @property
    def hero_image_url(self):
        """
        Zaxira rasm: ijrochining oddiy portreti, u ham bo'lmasa muqova.
        Quyidagi ikkala xossa ham oxirida shunga murojaat qiladi.
        """
        if self.artist.photo:
            return self.artist.photo.url
        if self.cover:
            return self.cover.url
        return None

    @property
    def hero_bg_url(self):
        """Hero ORQA FONI uchun rasm — keng banner afzal."""
        if self.artist.banner:
            return self.artist.banner.url
        return self.hero_image_url

    @property
    def hero_figure_url(self):
        """
        Hero dagi ASOSIY rasm — foni kesilgan (cutout) surat afzal:
        odam qora fonda "suzib" turadi, ramkasi ko'rinmaydi.
        """
        if self.artist.cutout:
            return self.artist.cutout.url
        return self.hero_image_url

    @property
    def hero_figure_is_cutout(self):
        """
        Shablon shu bilan bilib oladi: rasm shaffofmi yoki oddiy
        to'rtburchakmi. Ikkisiga CSS turlicha qo'llanadi — shaffof
        rasmga maska kerak emas, to'rtburchakka esa SHART.
        """
        return bool(self.artist.cutout)

    @property
    def external_url(self):
        """Albomning xizmatdagi sahifasi ("Deezer'da ochish" havolasi)."""
        if not self.external_id:
            return None
        if self.source == Source.DEEZER:
            return f'https://www.deezer.com/album/{self.external_id}'
        if self.source == Source.SPOTIFY:
            return f'https://open.spotify.com/album/{self.external_id}'
        return None

    # f'...' = "f-string". Ichidagi {...} qismlar qiymat bilan almashadi.
    # Natija: "Eminem — The Eminem Show"
    # self.artist.name — ikki nuqta: albomdan ijrochiga, undan uning ismiga.
    def __str__(self):
        return f'{self.artist.name} — {self.title}'


# ==========================================================
#  4) QO'SHIQ
# ==========================================================
class Song(models.Model):

    title = models.CharField(max_length=200)

    # Yana ForeignKey — qo'shiq albomga biriktiriladi.
    album = models.ForeignKey(
        Album,
        # Bu yerda CASCADE (Album'dagi PROTECT'dan farqli).
        # Sababi: albomsiz qo'shiqning ma'nosi yo'q — albom o'chsa,
        # qo'shiqlari ham o'chib ketaversin, "yetim" yozuv qolmasin.
        on_delete=models.CASCADE,
        # album.songs.all() deb chaqirish uchun
        related_name='songs',
    )

    # Albomdagi tartib raqami: 1, 2, 3...
    # PositiveSmallIntegerField = 0 dan 32767 gacha musbat son.
    # Argumentsiz -> bu maydon MAJBURIY, bo'sh qoldirib bo'lmaydi.
    track_number = models.PositiveSmallIntegerField()

    # Davomiyligi millisekundda (Spotify aynan shu formatda beradi).
    # Ko'rsatishda keyin 3:45 ko'rinishiga aylantiramiz.
    duration_ms = models.PositiveIntegerField(blank=True, null=True)

    # --- Tashqi xizmat ma'lumotlari (Spotify / Deezer) ---
    # source      = qaysi xizmatdan kelgan ('manual' = qo'lda kiritilgan)
    # external_id = o'sha xizmatdagi ID si
    # Ikkovi BIRGALIKDA unikal (pastdagi constraints ga qarang), chunki
    # Spotify'dagi "123" bilan Deezer'dagi "123" butunlay boshqa narsa.
    # external_id NULL bo'lsa cheklov ishlamaydi — shuning uchun qo'lda
    # kiritilgan yozuvlarni istagancha qo'shaverish mumkin.
    source = models.CharField(
        max_length=20, choices=Source.choices, default=Source.MANUAL
    )
    external_id = models.CharField(max_length=50, blank=True, null=True)

    # 30 soniyalik namuna (mp3) manzili. Deezer beradi, Spotify endi bermaydi.
    # Shu maydon to'liq bo'lsa — saytdagi play tugmasi ishlaydi.
    preview_url = models.URLField(max_length=500, blank=True, null=True)

    class Meta:
        # Qo'shiqlar har doim trek raqami bo'yicha kelsin.
        ordering = ['track_number']

        # Bitta albomda 3-trek ikkita bo'lib qolmasin.
        constraints = [
            models.UniqueConstraint(
                fields=['album', 'track_number'],
                name='uniq_track_no',
            ),
            models.UniqueConstraint(
                fields=['source', 'external_id'],
                name='uniq_song_external',
            ),
        ]
        # Izoh: "Qo'shiq" ichida apostrof (') bor, shuning uchun
        # matnni ikkitalik qo'shtirnoq (") bilan o'radik.
        verbose_name = "Qo'shiq"
        verbose_name_plural = "Qo'shiqlar"

    # @property = "bu metodni oddiy maydondek chaqir".
    # Ya'ni song.duration_display() emas, song.duration_display deb yoziladi.
    # Bazada ustun yaratmaydi - qiymatni har safar hisoblab beradi.
    @property
    def duration_display(self):
        """215000 (millisekund) -> '3:35'"""
        if not self.duration_ms:
            return ''
        total_seconds = self.duration_ms // 1000   # // = butun bo'lish
        minutes = total_seconds // 60
        seconds = total_seconds % 60               # % = bo'linmadan qolgan qoldiq
        return f'{minutes}:{seconds:02d}'          # :02d = "07" kabi ikki xonali

    def __str__(self):
        return self.title
