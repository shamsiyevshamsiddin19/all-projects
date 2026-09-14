"""
Spotify Web API bilan ishlaydigan yagona joy.

MUHIM QOIDA (arxitektura):
    Bu fayl Django modellarini BILMAYDI. U faqat oddiy dict qaytaradi.
    Sababi: ertaga Spotify o'zgarsa yoki boshqa xizmat qo'shsangiz,
    faqat shu fayl o'zgaradi, qolgan loyiha tegilmaydi.

Qanday ishlaydi (Client Credentials oqimi):
    1. Client ID + Secret ni Spotify'ga yuboramiz
    2. U bizga 1 soatlik "token" beradi
    3. Har bir so'rovda o'sha tokenni qo'shib yuboramiz
    Foydalanuvchi Spotify'ga kirishi SHART EMAS - bu server-server aloqa.

CHEKLOVLAR (bilib qo'ying):
    - To'liq qo'shiqni eshittirib bo'lmaydi. Spotify audio fayl bermaydi.
      Yechim: <iframe src="https://open.spotify.com/embed/album/<id>">
    - 30 soniyalik preview_url yangi ilovalar uchun yopilgan (null keladi).
    - Recommendations, Audio Features, Related Artists ham yopilgan.
    - So'rovlar soni cheklangan, shuning uchun token keshlanadi.
"""

import base64
import logging

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

TOKEN_URL = 'https://accounts.spotify.com/api/token'
API_BASE = 'https://api.spotify.com/v1'
CACHE_KEY = 'spotify_access_token'
TIMEOUT = 10  # soniya: javob kelmasa kutib qolmaymiz


class SpotifyError(Exception):
    """Spotify bilan bog'liq har qanday xato uchun bitta umumiy tur."""


class SpotifyClient:


    source = 'spotify'   # importers.py shu nom bilan bazaga yozadi

    def __init__(self, client_id=None, client_secret=None):
        # Argument berilmasa settings.py dan (u esa .env dan) oladi
        self.client_id = client_id or settings.SPOTIFY_CLIENT_ID
        self.client_secret = client_secret or settings.SPOTIFY_CLIENT_SECRET
        if not self.client_id or not self.client_secret:
            raise SpotifyError(
                '.env faylida SPOTIFY_CLIENT_ID va SPOTIFY_CLIENT_SECRET yo\'q. '
                'Ularni https://developer.spotify.com/dashboard dan oling.'
            )

    # ---------- ichki yordamchilar ----------

    def _get_token(self):
        """Tokenni keshdan oladi, bo'lmasa Spotify'dan yangisini so'raydi."""
        token = cache.get(CACHE_KEY)
        if token:
            return token

        # Spotify ID va Secret ni base64 shaklida sarlavhada kutadi
        raw = f'{self.client_id}:{self.client_secret}'.encode()
        auth_header = base64.b64encode(raw).decode()

        response = requests.post(
            TOKEN_URL,
            data={'grant_type': 'client_credentials'},
            headers={'Authorization': f'Basic {auth_header}'},
            timeout=TIMEOUT,
        )
        if response.status_code != 200:
            raise SpotifyError(f'Token olinmadi ({response.status_code}): {response.text}')

        data = response.json()
        token = data['access_token']
        # Token 3600 soniya yashaydi. 60 soniya oldinroq eskirgan deb hisoblaymiz,
        # aks holda so'rov ketayotganda token o'lib qolishi mumkin.
        cache.set(CACHE_KEY, token, data.get('expires_in', 3600) - 60)
        return token

    def _get(self, path, params=None):
        """API ga GET so'rov yuboradi va JSON qaytaradi."""
        response = requests.get(
            f'{API_BASE}{path}',
            params=params or {},
            headers={'Authorization': f'Bearer {self._get_token()}'},
            timeout=TIMEOUT,
        )

        # 401 = token eskirgan. Keshni tozalab, bir marta qayta urinamiz.
        if response.status_code == 401:
            cache.delete(CACHE_KEY)
            response = requests.get(
                f'{API_BASE}{path}',
                params=params or {},
                headers={'Authorization': f'Bearer {self._get_token()}'},
                timeout=TIMEOUT,
            )

        # 429 = juda ko'p so'rov yubordik
        # 403 = kalitlar to'g'ri, lekin akkauntda ruxsat yo'q.
        # Spotify 2025-yildan beri ilova egasidan Premium talab qiladi.
        if response.status_code == 403:
            raise SpotifyError(
                'Spotify ruxsat bermadi (403). Sabab: ilova egasining '
                'akkaunti Premium emas. .env da MUSIC_PROVIDER=deezer '
                'qilib qo\'ying — u kalitsiz va bepul ishlaydi.'
            )

        if response.status_code == 429:
            retry_after = response.headers.get('Retry-After', '?')
            raise SpotifyError(f'So\'rov chegarasi. {retry_after} soniyadan keyin urining.')

        if response.status_code != 200:
            raise SpotifyError(f'Spotify xatosi ({response.status_code}): {response.text[:200]}')

        return response.json()

    # ---------- tashqi (ishlatiladigan) metodlar ----------

    def search_albums(self, query, limit=10):
        """Albom qidiradi. Sodda dict ro'yxatini qaytaradi."""
        data = self._get('/search', {'q': query, 'type': 'album', 'limit': limit})
        return [self._simplify_album(item) for item in data['albums']['items']]

    def get_album(self, spotify_id):
        """Bitta albomni to'liq ma'lumoti va qo'shiqlari bilan oladi."""
        data = self._get(f'/albums/{spotify_id}')
        album = self._simplify_album(data)
        album['genres'] = data.get('genres', [])
        album['tracks'] = [
            {
                'external_id': t['id'],
                'title': t['name'],
                'track_number': t['track_number'],
                'duration_ms': t['duration_ms'],
                # Spotify yangi ilovalarga preview bermaydi — doim None keladi.
                'preview_url': t.get('preview_url'),
            }
            # Albomda 50 dan ortiq trek bo'lsa, qolgani keyingi sahifada
            # qoladi. Bu loyihada bunday holat deyarli uchramaydi.
            for t in data['tracks']['items']
        ]
        return album

    def get_artist(self, spotify_id):
        data = self._get(f'/artists/{spotify_id}')
        images = data.get('images') or []
        return {
            'source': 'spotify',
            'external_id': data['id'],
            'name': data['name'],
            'genres': data.get('genres', []),
            'image_url': images[0]['url'] if images else None,
        }

    # ---------- format o'zgartirish ----------

    @staticmethod
    def _simplify_album(item):
        """Spotify'ning katta javobidan bizga kerakli qismini ajratadi."""
        images = item.get('images') or []
        artists = item.get('artists') or []
        return {
            'source': 'spotify',
            'external_id': item['id'],
            'title': item['name'],
            # release_date "2002" yoki "2002-05" yoki "2002-05-26" bo'lishi mumkin
            'release_date': item.get('release_date'),
            'release_date_precision': item.get('release_date_precision'),
            'cover_url': images[0]['url'] if images else None,
            'artist_name': artists[0]['name'] if artists else '',
            'artist_external_id': artists[0]['id'] if artists else None,
            'total_tracks': item.get('total_tracks'),
            # Saytda qo'yish uchun tayyor embed manzili (audio shu orqali chalinadi)
            'embed_url': f"https://open.spotify.com/embed/album/{item['id']}",
        }
