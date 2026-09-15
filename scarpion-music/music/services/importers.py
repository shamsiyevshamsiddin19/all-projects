"""
Tashqi xizmatdan (Deezer/Spotify) kelgan dict ni bizning modellarimizga
aylantiruvchi qatlam.

Nega alohida fayl?
    deezer.py / spotify.py - faqat API bilan gaplashadi (modellarni bilmaydi)
    importers.py           - o'rtadagi "tarjimon" (ikkalasini biladi)
    views.py               - faqat shu yerni chaqiradi

Shunday bo'lgani uchun API o'zgarsa, views.py ga umuman tegilmaydi.
Va Deezer'dan Spotify'ga o'tganda ham bu fayl o'zgarmaydi — chunki
ikkala klient ham bir xil shakldagi dict qaytaradi.
"""

import re
from datetime import date

import requests
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils.text import slugify

from ..models import Album, Artist, Genre, Song, Source
from .artwork import get_artist_images
from .providers import get_client


# Albom nomi oxiridagi "nashr" qismlari. Katalogda ular ko'p:
#   "Morning Glory? (30th Anniversary)", "Nevermind (Remastered)"
# Sayt uchun bular ortiqcha — sarlavhani cho'zib, dizaynni buzadi.
NASHR_SOZLARI = (
    'remaster', 'deluxe', 'anniversary', 'expanded', 'edition',
    'version', 'explicit', 'bonus', 'reissue', 'super deluxe',
    "taylor's version",
)

# Oxiridagi ( ... ) yoki [ ... ] bo'lagini ushlaydi
NASHR_NAQSHI = re.compile(r'\s*[\(\[][^\(\)\[\]]*[\)\]]\s*$')


def clean_album_title(title):
    """
    Albom nomidan nashr haqidagi qo'shimchani olib tashlaydi.

        "Nevermind (Remastered)"                    -> "Nevermind"
        "Morning Glory? (30th Anniversary)"         -> "Morning Glory?"
        "folklore (deluxe version)"                 -> "folklore"

    DIQQAT: faqat OXIRIDAGI qavs va faqat ichida nashr so'zi bo'lsa
    olib tashlanadi. Shu sababli quyidagilar TEGILMAYDI:
        "(What's the Story) Morning Glory?"   — qavs boshida
        "good kid, m.A.A.d city"              — qavs yo'q
        "Sgt. Pepper's (Lonely Hearts)"       — nashr so'zi yo'q

    Nomning o'zi butunlay qavs ichida bo'lsa ham tegilmaydi —
    aks holda bo'sh nom qolib ketardi.
    """
    if not title:
        return title

    natija = title.strip()
    # Ketma-ket ikkita qavs bo'lishi mumkin: "... (Deluxe) (Remastered)"
    for _ in range(2):
        m = NASHR_NAQSHI.search(natija)
        if not m:
            break
        ich = m.group(0).lower()
        if not any(soz in ich for soz in NASHR_SOZLARI):
            break
        qisqargan = natija[:m.start()].strip()
        if not qisqargan:          # hammasi qavs ichida edi — tegmaymiz
            break
        natija = qisqargan

    return natija


def parse_release_date(value, precision):
    """
    Xizmatlar sanani uch xil aniqlikda berishi mumkin:
        "2002"       (precision='year')
        "2002-05"    (precision='month')
        "2002-05-26" (precision='day')
    Bizning DateField esa to'liq sana kutadi - yetmagan qismni 1 bilan to'ldiramiz.
    """
    if not value:
        return None
    parts = value.split('-')
    try:
        year = int(parts[0])
        month = int(parts[1]) if len(parts) > 1 else 1
        day = int(parts[2]) if len(parts) > 2 else 1
        return date(year, month, day)
    except (ValueError, IndexError):
        return None


def download_image(url, filename):
    """Rasmni yuklab, Django faylga aylantiradi. Xato bo'lsa None qaytaradi."""
    if not url:
        return None
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        return ContentFile(response.content, name=filename)
    except requests.RequestException:
        return None


def fetch_artist_artwork(artist, force=False):
    """
    Ijrochiga TheAudioDB dan chiroyliroq rasmlar qo'shadi.

    force=False (sukut) — faqat BO'SH maydonlar to'ldiriladi.
    force=True          — mavjud rasm ustiga yozadi (portret ham).

    Qaytaradi: nima yangilangani ro'yxati, masalan ['cutout', 'banner'].
    Hech narsa topilmasa — bo'sh ro'yxat. Bu xato emas: kam tanilgan
    ijrochi bazada yo'q, eski rasm joyida qolaveradi.
    """
    rasmlar = get_artist_images(artist.name)
    if not any(rasmlar.values()):
        return []

    asos = slugify(artist.name) or 'artist'
    yangilandi = []

    # cutout — shaffof PNG, shuning uchun .png bo'lishi SHART.
    # .jpg qilsak shaffoflik yo'qoladi va orqasi qora bo'lib qoladi.
    if rasmlar['cutout'] and (force or not artist.cutout):
        fayl = download_image(rasmlar['cutout'], f'{asos}-cutout.png')
        if fayl:
            artist.cutout = fayl
            yangilandi.append('cutout')

    if rasmlar['fanart'] and (force or not artist.banner):
        fayl = download_image(rasmlar['fanart'], f'{asos}-banner.jpg')
        if fayl:
            artist.banner = fayl
            yangilandi.append('banner')

    # Portretni faqat so'ralganda yoki umuman bo'lmaganda almashtiramiz.
    if rasmlar['thumb'] and (force or not artist.photo):
        fayl = download_image(rasmlar['thumb'], f'{asos}.jpg')
        if fayl:
            artist.photo = fayl
            yangilandi.append('photo')

    if yangilandi:
        artist.save(update_fields=yangilandi)
    return yangilandi


def get_or_create_artist(name, external_id=None, source=Source.MANUAL,
                         client=None, owner=None):
    """
    Ijrochini topadi, bo'lmasa yaratadi.

    Uch bosqichda qidiradi (yuqoridan pastga):
      1. Aynan shu xizmatdagi ID bo'yicha  - eng ishonchli
      2. Ismi bo'yicha (katta-kichik harf farqi yo'q) - takror yaratmaslik uchun
      3. Topilmasa - yangisini yaratadi
    """
    artist = None

    if external_id:
        artist = Artist.objects.filter(source=source, external_id=external_id).first()

    if artist is None:
        artist = Artist.objects.filter(name__iexact=name).first()

    if artist is None:
        artist = Artist(name=name, source=source, external_id=external_id,
                        owner=owner)
        if external_id and client:
            try:
                info = client.get_artist(external_id)
                image = download_image(
                    info['image_url'], f'{slugify(name) or "artist"}.jpg'
                )
                if image:
                    artist.photo = image
            except Exception:
                pass  # rasm bo'lmasa ham ijrochi yaratilaveradi
        artist.save()

        # Endi chiroyliroq rasmlarni qidiramiz (cutout / banner).
        # Xato bo'lsa e'tibor bermaymiz — ijrochi allaqachon saqlangan,
        # rasm esa "bo'lsa yaxshi" darajasidagi qo'shimcha.
        try:
            fetch_artist_artwork(artist)
        except Exception:
            pass

    elif external_id and not artist.external_id:
        # Ilgari qo'lda kiritilgan ijrochi edi - endi unga ID biriktiramiz.
        artist.source = source
        artist.external_id = external_id
        artist.save(update_fields=['source', 'external_id'])

    return artist


@transaction.atomic
def import_album(external_id, client=None, owner=None):
    """
    Tashqi ID bo'yicha albomni (ijrochisi va qo'shiqlari bilan) bazaga yozadi.

    @transaction.atomic = "yo hammasi, yo hech narsa".
        O'rtada xato chiqsa, yarim yozilgan albom qolib ketmaydi -
        baza xato chiqishidan oldingi holatiga qaytadi.

    owner - kim import qilayotgan bo'lsa o'sha. Albom va (agar yangi
    yaratilsa) ijrochi shu odamga tegishli bo'ladi. Terminaldan
    ishlatilganda None bo'ladi — bunda yozuv egasiz qoladi va uni
    faqat administrator o'zgartira oladi.

    Qaytaradi: (album, created) - created=True bo'lsa yangi qo'shildi.
    """
    client = client or get_client()
    source = client.source
    data = client.get_album(external_id)

    # Allaqachon import qilinganmi? Unda ikkinchi nusxa yaratmaymiz.
    existing = Album.objects.filter(
        source=source, external_id=data['external_id']
    ).first()
    if existing:
        return existing, False

    artist = get_or_create_artist(
        data['artist_name'],
        data['artist_external_id'],
        source=source,
        client=client,
        owner=owner,
    )

    album = Album(
        title=clean_album_title(data['title']),
        artist=artist,
        release_date=parse_release_date(
            data['release_date'], data['release_date_precision']
        ),
        source=source,
        external_id=data['external_id'],
        owner=owner,
    )

    cover = download_image(
        data['cover_url'], f'{slugify(data["title"]) or "album"}.jpg'
    )
    if cover:
        album.cover = cover

    album.save()   # slug shu yerda avtomatik yasaladi (models.py dagi save())

    for genre_name in data.get('genres', []):
        genre, _ = Genre.objects.get_or_create(
            name__iexact=genre_name,
            defaults={'name': genre_name},
        )
        album.genres.add(genre)

    # bulk_create = 20 ta qo'shiqni 20 ta emas, BITTA so'rov bilan yozadi.
    Song.objects.bulk_create([
        Song(
            album=album,
            title=track['title'],
            track_number=track['track_number'],
            duration_ms=track['duration_ms'],
            preview_url=track.get('preview_url'),
            source=source,
            external_id=track['external_id'],
        )
        for track in data['tracks']
    ])

    return album, True
