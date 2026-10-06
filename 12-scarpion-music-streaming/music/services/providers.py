"""
Qaysi musiqa xizmatidan foydalanishni HAL QILADIGAN yagona joy.

Nega alohida fayl kerak?
    views.py da "if provider == 'deezer': ... else: ..." deb yozsak,
    ertaga uchinchi xizmat qo'shilganda o'sha if ni HAMMA joyda
    qidirib chiqishga to'g'ri keladi. Bu yerda esa — bitta lug'at.

Almashtirish juda oddiy — .env faylida bitta qatorni o'zgartirasiz:
    MUSIC_PROVIDER=deezer     <- kalitsiz, bepul (hozirgi holat)
    MUSIC_PROVIDER=spotify    <- Premium olganingizdan keyin

Kodga umuman tegilmaydi, chunki ikkala klientda ham AYNI metodlar bor:
    search_albums(query)  |  get_album(id)  |  get_artist(id)
"""

from django.conf import settings

from .deezer import DeezerClient, DeezerError
from .spotify import SpotifyClient, SpotifyError

# Nom -> klass. Yangi xizmat qo'shsangiz shu yerga bitta qator qo'shasiz.
PROVIDERS = {
    'deezer': DeezerClient,
    'spotify': SpotifyClient,
}

# views.py shu tuple ni "except" da ishlatadi:
#     except PROVIDER_ERRORS as exc:
# Shunda qaysi xizmat xato bergani muhim emas — ikkalasi ham ushlanadi.
PROVIDER_ERRORS = (DeezerError, SpotifyError)


class UnknownProvider(Exception):
    """.env da noto'g'ri nom yozilganda chiqadi."""


def get_client(name=None):
    """
    Tayyor klient qaytaradi.
        get_client()           -> .env dagi MUSIC_PROVIDER ni ishlatadi
        get_client('spotify')  -> majburan Spotify (sinash uchun qulay)
    """
    name = (name or getattr(settings, 'MUSIC_PROVIDER', 'deezer') or 'deezer').lower()

    if name not in PROVIDERS:
        mavjud = ', '.join(PROVIDERS)
        raise UnknownProvider(
            f"'{name}' degan xizmat yo'q. Mumkin bo'lganlari: {mavjud}. "
            f'.env dagi MUSIC_PROVIDER ni tekshiring.'
        )

    return PROVIDERS[name]()


def provider_name():
    """Hozir qaysi xizmat ishlayotganini shablonlarda ko'rsatish uchun."""
    return (getattr(settings, 'MUSIC_PROVIDER', 'deezer') or 'deezer').lower()
