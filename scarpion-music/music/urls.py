from django.urls import path

from . import views

# app_name = shu app uchun "familiya".
# Shundan keyin URL lar 'music:album_list' deb chaqiriladi.
# Bu boshqa applar bilan nom to'qnashuvining oldini oladi.
app_name = 'music'

# DIQQAT - TARTIB MUHIM!
# Django ro'yxatni yuqoridan pastga tekshiradi va BIRINCHI mos kelganida
# to'xtaydi. Shuning uchun aniq so'zlar (qoshish) o'zgaruvchilardan
# (<slug:...>) OLDIN turishi kerak. Aks holda "qoshish" so'zi
# ijrochi slugi deb qabul qilinib, 404 beradi.
urlpatterns = [
    # Bosh sahifa: albomlar ro'yxati + qidiruv (?q=...)
    path('', views.AlbumListView.as_view(), name='album_list'),

    # --- Import (Deezer/Spotify dan olib kelish) ---
    path('import/', views.ImportView.as_view(), name='import'),

    # --- Akkaunt ---
    # LoginView Django'ning tayyor view'i — faqat shablon va formani
    # o'zimiznikiga almashtiramiz, qolgan mantiq o'zida.
    # KirishView ning o'zida @login_not_required bor — busiz kirish
    # sahifasi ham login so'rab, cheksiz aylanma hosil bo'lardi.
    path('kirish/', views.KirishView.as_view(), name='login'),
    path('royxatdan-otish/', views.SignupView.as_view(), name='signup'),
    # Brauzerdan Firebase ID tokeni keladi, javob JSON bo'ladi
    path('google-kirish/', views.google_login, name='google_login'),
    path('chiqish/', views.logout_view, name='logout'),

    # --- Avtoto'ldirish (JSON, sahifa emas) ---
    path('takliflar/', views.suggest, name='suggest'),

    # --- Albom ---
    path('albom/qoshish/', views.AlbumCreateView.as_view(), name='album_create'),

    # DIQQAT: bu ikkovi album_detail dan YUQORIDA turishi SHART.
    # album_detail manzili <slug>/<slug> ko'rinishida, slug esa raqamni
    # ham qabul qiladi — "albom/5/tahrirlash/" xato yo'lga tushib
    # ketmasligi uchun aniqroq qoidalar oldinda turadi.
    path('albom/<int:pk>/tahrirlash/', views.AlbumUpdateView.as_view(), name='album_update'),
    path('albom/<int:pk>/ochirish/', views.AlbumDeleteView.as_view(), name='album_delete'),
    # <int:album_pk> = manzildagi son album_pk nomi bilan view ga uzatiladi
    path(
        'albom/<int:album_pk>/qoshiq-qoshish/',
        views.SongCreateView.as_view(),
        name='song_create',
    ),
    # Ikki qismli manzil: /albom/eminem/the-eminem-show/
    # Bu qator song_create dan PASTDA turishi shart.
    path(
        'albom/<slug:artist_slug>/<slug:slug>/',
        views.AlbumDetailView.as_view(),
        name='album_detail',
    ),

    # --- Ijrochi ---
    path('ijrochi/', views.ArtistListView.as_view(), name='artist_list'),
    path('ijrochi/qoshish/', views.ArtistCreateView.as_view(), name='artist_create'),
    path('ijrochi/<slug:slug>/tahrirlash/', views.ArtistUpdateView.as_view(), name='artist_update'),
    path('ijrochi/<slug:slug>/ochirish/', views.ArtistDeleteView.as_view(), name='artist_delete'),
    path('ijrochi/<slug:slug>/', views.ArtistDetailView.as_view(), name='artist_detail'),

    # --- Qo'shiq ---
    path('qoshiq/<int:pk>/tahrirlash/', views.SongUpdateView.as_view(), name='song_update'),
    path('qoshiq/<int:pk>/ochirish/', views.SongDeleteView.as_view(), name='song_delete'),
]
