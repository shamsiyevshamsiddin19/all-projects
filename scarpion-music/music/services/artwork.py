"""
Ijrochi rasmlarini oladigan qatlam — TheAudioDB.

NEGA YANA BITTA XIZMAT?
    Deezer ijrochi surati sifatida ko'pincha uning ALBOM MUQOVASINI
    beradi (ayniqsa kam tanilgan ijrochilarda). Bosh sahifadagi katta
    blokka esa odamning o'zi kerak.

    TheAudioDB aynan shuni beradi va uch xil ko'rinishda:
        cutout — foni KESILGAN shaffof PNG (odam qora fonda "suzadi")
        fanart — keng surat, 1920x1080 (fon uchun juda mos)
        thumb  — kvadrat portret, 700x700 (kartalar uchun)

    Kalit kerak emas: hujjatlarda ochiq turgan '2' test kaliti bilan
    ishlaydi. Kalit olsangiz .env ga AUDIODB_KEY=... deb yozasiz.

CHEKLOVLAR:
    - Faqat TANILGAN ijrochilar bor. Mahalliy yoki kam mashhur
      ijrochilar topilmaydi — bu xato emas, oddiy hol. Shunda
      eski rasm (Deezer'niki) joyida qolaveradi.
    - So'rovlar soni cheklangan, shuning uchun ketma-ket ishlatganda
      orasiga biroz tanaffus qo'yish kerak (buyruqda shunday qilingan).
"""

import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

API = 'https://www.theaudiodb.com/api/v1/json'
TIMEOUT = 12


class ArtworkError(Exception):
    """Rasm xizmati bilan bog'liq xato."""


def _key():
    return getattr(settings, 'AUDIODB_KEY', '') or '2'


def get_artist_images(name):
    """
    Ijrochi nomi bo'yicha rasm manzillarini qaytaradi.

    Qaytadigan dict:
        {'cutout': url|None, 'fanart': url|None, 'thumb': url|None}

    Ijrochi topilmasa — barcha qiymatlar None. Bu XATO EMAS,
    shuning uchun istisno (exception) ko'tarilmaydi: chaqiruvchi kod
    oddiygina "rasm yo'q" deb davom etaveradi.
    """
    bosh = {'cutout': None, 'fanart': None, 'thumb': None}

    if not name or not name.strip():
        return bosh

    try:
        response = requests.get(
            f'{API}/{_key()}/search.php',
            params={'s': name.strip()},
            timeout=TIMEOUT,
        )
    except requests.RequestException as exc:
        logger.warning('TheAudioDB ga ulanib bo\'lmadi: %s', exc)
        return bosh

    if response.status_code != 200:
        logger.warning('TheAudioDB xatosi: %s', response.status_code)
        return bosh

    try:
        data = response.json() or {}
    except ValueError:
        # Chegaraga yetganda HTML qaytarishi mumkin — JSON emas.
        logger.warning('TheAudioDB JSON qaytarmadi (chegara bo\'lishi mumkin)')
        return bosh

    artists = data.get('artists')
    if not artists:
        return bosh

    a = artists[0]
    return {
        'cutout': a.get('strArtistCutout') or None,
        # Fanart yo'q bo'lsa WideThumb ham keng rasm — u ham bo'ladi
        'fanart': a.get('strArtistFanart') or a.get('strArtistWideThumb') or None,
        'thumb': a.get('strArtistThumb') or None,
    }
