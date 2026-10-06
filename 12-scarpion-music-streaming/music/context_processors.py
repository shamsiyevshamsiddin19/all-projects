"""
Kontekst protsessori = HAR BIR shablonga avtomatik qo'shiladigan ma'lumot.

Nega kerak?
    Footer'dagi janrlar ro'yxati hamma sahifada ko'rinishi kerak.
    Buni har bir view ichida yozib chiqish — takror ish.
    Shu funksiya settings.py ga ulangach, {{ footer_genres }}
    o'z-o'zidan hamma joyda ishlaydi.

DIQQAT: bu funksiya HAR bir sahifada ishlaydi, shuning uchun
    ichida og'ir so'rov yozmaslik kerak. Bu yerda — 6 ta qator, yengil.
"""

import json

from django.conf import settings
from django.db.models import Count

from .models import Album, Artist, Genre, Song


def footer(request):
    return {
        'footer_genres': (
            Genre.objects
            .annotate(albums_total=Count('albums'))
            .filter(albums_total__gt=0)
            .order_by('-albums_total', 'name')[:6]
        ),
        # Profil oynasidagi raqamlar. Uchta COUNT so'rovi — yengil,
        # lekin HAR sahifada ishlaydi. Baza kattalashsa bularni
        # keshga olish kerak bo'ladi.
        'stat_albums': Album.objects.count(),
        'stat_artists': Artist.objects.count(),
        'stat_songs': Song.objects.count(),
    }


def firebase(request):
    """
    Firebase sozlamalarini shablonga uzatadi.

    json.dumps() bilan beramiz — shablonda uni to'g'ridan-to'g'ri
    JavaScript obyekti sifatida ishlatish mumkin bo'ladi.
    Qiymatlar maxfiy emas (yuqoridagi settings.py izohiga qarang).
    """
    return {
        'firebase_config': json.dumps(settings.FIREBASE),
        # Sozlanmagan bo'lsa tugmani umuman ko'rsatmaymiz
        'firebase_yoqilgan': bool(settings.FIREBASE.get('apiKey')),
    }
