"""
Deezer API bilan ishlaydigan yagona joy.

NEGA DEEZER?
    Spotify 2025-yildan beri Web API uchun ilova egasidan Premium talab qiladi.
    Premium bo'lmasa har bir so'rovga 403 qaytadi. Deezer esa:
        - kalit (API key) umuman kerak emas
        - ro'yxatdan o'tish kerak emas
        - 30 soniyalik preview mp3 BERADI (Spotify buni endi bermaydi)

MUHIM QOIDA (spotify.py dagi bilan bir xil):
    Bu fayl Django modellarini BILMAYDI. Faqat oddiy dict qaytaradi.
    Va eng muhimi — SpotifyClient bilan AYNI metodlar, AYNI dict shakli.
    Shuning uchun importers.py ga qaysi klient kelgani umuman farqi yo'q.
    Buni "bir xil shakl" (interface) deyiladi.

CHEKLOVLAR:
    - 5 soniyada ~50 ta so'rov. Ko'p so'rasangiz 4-kod bilan xato beradi.
    - Deezer xatoni HTTP 200 bilan, javob ichida {"error": ...} qilib yuboradi.
      Shuning uchun status_code ni tekshirish YETARLI EMAS.
"""

import logging

import requests

logger = logging.getLogger(__name__)

API_BASE = 'https://api.deezer.com'
TIMEOUT = 10  # soniya: javob kelmasa kutib qolmaymiz


class DeezerError(Exception):
    """Deezer bilan bog'liq har qanday xato uchun bitta umumiy tur."""


class DeezerClient:
    """
    Kalit kerak emas, shuning uchun __init__ ham bo'sh.
    (SpotifyClient bilan bir xil bo'lishi uchun argumentlarni qabul qiladi,
     lekin ularni ishlatmaydi.)
    """

    source = 'deezer'   # importers.py shu nom bilan bazaga yozadi

    def __init__(self, client_id=None, client_secret=None):
        pass

    # ------------------------------------------------------------------
    #  Ichki yordamchi
    # ------------------------------------------------------------------
    def _get(self, path, params=None):
        """API ga GET so'rov yuboradi va JSON qaytaradi."""
        try:
            response = requests.get(
                f'{API_BASE}{path}',
                params=params or {},
                timeout=TIMEOUT,
            )
        except requests.RequestException as exc:
            raise DeezerError(f'Deezer ga ulanib bo\'lmadi: {exc}')

        if response.status_code != 200:
            raise DeezerError(f'Deezer xatosi ({response.status_code})')

        data = response.json()

        # Deezer xatoni 200 kod bilan, javob ICHIDA yuboradi — shuni ushlaymiz.
        if isinstance(data, dict) and 'error' in data:
            error = data['error']
            message = error.get('message', 'noma\'lum xato')
            if error.get('code') == 4:
                raise DeezerError('So\'rov chegarasi. Bir oz kutib qayta urining.')
            raise DeezerError(f'Deezer xatosi: {message}')

        return data

    # ------------------------------------------------------------------
    #  Ochiq metodlar — SpotifyClient dagi bilan bir xil nomlar
    # ------------------------------------------------------------------
    def search_albums(self, query, limit=10):
        """Albom qidiradi. Sodda dict ro'yxatini qaytaradi."""
        data = self._get('/search/album', {'q': query, 'limit': limit})
        return [self._simplify_album(item) for item in data.get('data', [])]

    def get_album(self, external_id):
        """Bitta albomni to'liq ma'lumoti va qo'shiqlari bilan oladi."""
        data = self._get(f'/album/{external_id}')
        album = self._simplify_album(data)

        # Deezer janrni {"data": [{"name": "Rap/Hip Hop"}, ...]} shaklida beradi
        genres = (data.get('genres') or {}).get('data') or []
        album['genres'] = [g['name'] for g in genres if g.get('name')]

        # DIQQAT: albom javobidagi treklarda track_position YO'Q.
        # Uni alohida so'rasa bo'ladi, lekin har trek uchun bitta so'rov —
        # 20 ta qo'shiqqa 20 ta so'rov, chegaraga tez yetamiz.
        # Treklar allaqachon to'g'ri tartibda kelgani uchun
        # enumerate(..., start=1) bilan raqamlaymiz. Shu yetarli.
        tracks = (data.get('tracks') or {}).get('data') or []
        album['tracks'] = [
            {
                'external_id': str(track['id']),
                'title': track.get('title') or 'Nomsiz',
                'track_number': index,
                # Deezer davomiylikni SONIYADA beradi, bizga MILLISEKUND kerak
                'duration_ms': int(track.get('duration') or 0) * 1000 or None,
                'preview_url': track.get('preview') or None,
            }
            for index, track in enumerate(tracks, start=1)
        ]
        return album

    def get_artist(self, external_id):
        """Ijrochi haqida ma'lumot (asosan rasm kerak)."""
        data = self._get(f'/artist/{external_id}')
        return {
            'source': self.source,
            'external_id': str(data['id']),
            'name': data['name'],
            'genres': [],   # Deezer ijrochi uchun janr bermaydi
            'image_url': data.get('picture_xl') or data.get('picture_big'),
        }

    # ------------------------------------------------------------------
    #  Deezer javobidan bizga kerakli qismini ajratamiz
    # ------------------------------------------------------------------
    @staticmethod
    def _simplify_album(item):
        # DIQQAT: oddiy item['id'] deb yozilsa, Deezer kutilmagan
        # (masalan, hududiy cheklov tufayli qisman) javob qaytarganda
        # xom KeyError chiqib, modul o'z va'dasiga (barcha xatolar
        # DeezerError bo'lishi kerak) zid ravishda views.py dagi
        # "except PROVIDER_ERRORS" ni chetlab o'tib, foydalanuvchiga
        # tushunarsiz 500-xato ko'rsatardi.
        if not item.get('id'):
            raise DeezerError("Deezer noto'g'ri albom ma'lumotini qaytardi.")
        artist = item.get('artist') or {}
        return {
            'source': 'deezer',
            'external_id': str(item['id']),
            'title': item.get('title') or 'Nomsiz',
            # Deezer sanani doim to'liq "2002-05-26" shaklida beradi,
            # shuning uchun aniqlik (precision) har doim 'day'.
            'release_date': item.get('release_date'),
            'release_date_precision': 'day',
            'cover_url': item.get('cover_xl') or item.get('cover_big'),
            'artist_name': artist.get('name', ''),
            'artist_external_id': str(artist['id']) if artist.get('id') else None,
            'total_tracks': item.get('nb_tracks'),
            'embed_url': f"https://widget.deezer.com/widget/dark/album/{item['id']}",
        }
