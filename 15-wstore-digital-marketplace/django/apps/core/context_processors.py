from django.conf import settings


def global_settings(request):
    """
    Barcha shablonlarga kerak bo'ladigan global sozlamalar.

    Ilgari bu yerda `CATEGORIES_GLOBAL` (Category so'rovi) va
    `USER_WISHLIST_IDS` (Wishlist so'rovi) ham bor edi — ya'ni HAR BIR
    so'rovda, hatto admin panelida va JSON endpointlarda ham ikkita
    ortiqcha SQL so'rov bajarilardi. Tekshiruv shuni ko'rsatdiki, ikkalasi
    ham hech bir shablonda ishlatilmagan: katalog va sevimlilar sahifalari
    wishlist ro'yxatini o'z view'idan (`wishlist_ids`) oladi.
    """
    # DEBUG'da statik fayl versiyasini har safar qayta hisoblaymiz: dev server
    # .css/.js o'zgarganda qayta yuklanmaydi, shuning uchun ishga tushganda
    # hisoblangan qiymat eskirib qolardi va brauzer eski faylni ko'rsatardi.
    if settings.DEBUG:
        static_version = settings.STATIC_VERSION_FN()
    else:
        static_version = getattr(settings, "STATIC_VERSION", "1")

    return {
        "DEMO_MODE": getattr(settings, "DEMO_MODE", False),
        # Kalitlar sozlanmagan bo'lsa "Google bilan kirish" tugmasi
        # ko'rsatilmaydi — bosilganda baribir xato chiqardi.
        "GOOGLE_AUTH_ENABLED": getattr(settings, "GOOGLE_AUTH_ENABLED", False),
        "STATIC_VERSION": static_version,
        "UZS_RATE": getattr(settings, "PRODUCT_UZS_RATE", 12600),
        "MIN_WITHDRAWAL_SOM": getattr(settings, "MIN_WITHDRAWAL_SOM", 50000),
        "REFERRAL_BONUS_SOM": getattr(settings, "REFERRAL_BONUS_SOM", 10000),
        "LISTING_FEE_SOM": getattr(settings, "LISTING_FEE_SOM", 5000),
    }
