import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_not_required
from django.contrib.auth.views import LoginView
from django.utils.decorators import method_decorator
from django.db.models import Count, F, OuterRef, ProtectedError, Q, Subquery
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.shortcuts import resolve_url
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.text import slugify
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView,
)
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

logger = logging.getLogger(__name__)

from .forms import ArtistForm, AlbumForm, KirishForm, RoyxatForm, SongForm
from .middleware import KEYINGI_MANZIL
from .models import Album, Artist, Genre, Song
from .services.importers import import_album
from .services.providers import PROVIDER_ERRORS, get_client, provider_name


# ==========================================================
#  ALBOMLAR RO'YXATI  +  QIDIRUV        ->  /
# ==========================================================
# ListView = "ro'yxat ko'rsatadigan" tayyor view.
# U o'zi so'rov yuboradi, sahifalarga bo'ladi va templatega uzatadi.
def preview_qoshish(qs):
    """
    Har bir albomga uning BIRINCHI qo'shig'i haqidagi ma'lumotni qo'shadi:
    namuna manzili va qo'shiq nomi. Kartadagi "play" tugmasi shularni
    ishlatadi.

    Nega Subquery? Eng sodda yo'l — shablonda "album.songs.first" yozish.
    Lekin u HAR BIR karta uchun alohida so'rov yuboradi: 24 ta karta =
    24 ta ortiqcha so'rov (buni "N+1 muammosi" deyishadi).
    Subquery esa hammasini BITTA so'rovga qo'shib yuboradi.

    prefetch_related ham bo'lardi, lekin u albomning BARCHA qo'shiqlarini
    tortib olardi — bizga esa faqat bittasi kerak.
    """
    birinchi = Song.objects.filter(album=OuterRef('pk')).order_by('track_number')
    return qs.annotate(
        birinchi_preview=Subquery(birinchi.values('preview_url')[:1]),
        birinchi_nom=Subquery(birinchi.values('title')[:1]),
    )


class AlbumListView(ListView):
    model = Album
    template_name = 'music/album_list.html'
    context_object_name = 'albums'   # templatede {{ albums }} deb chaqiriladi
    paginate_by = 12                 # har sahifada 12 ta albom

    # get_queryset = "bazadan nimani olay?" degan savolga javob.
    def get_queryset(self):
        # preview_qoshish() har bir albomga birinchi qo'shig'ining
        # namuna manzilini qo'shadi — kartadagi "play" tugmasi uchun.
        qs = preview_qoshish(
            Album.objects
            # select_related = FK uchun. Busiz 12 ta albom uchun baza
            # 13 marta so'roq qilinadi (N+1 muammosi).
            .select_related('artist')
            # prefetch_related = M2M uchun (select_related M2M da ishlamaydi)
            .prefetch_related('genres')
            # Har bir albomning qo'shiqlari sonini bitta so'rovda hisoblaydi
            .annotate(songs_total=Count('songs'))
            # DIQQAT: annotate() ishlatilganda Django modeldagi
            # Meta.ordering ni "yo'qotadi" va sahifalashda ogohlantirish
            # beradi. Shuning uchun tartibni shu yerda aniq ko'rsatamiz.
            # nulls_last=True -> sanasi noma'lum albomlar eng oxirida tursin.
            .order_by(F('release_date').desc(nulls_last=True), 'title')
        )

        # Manzildagi ?q=... qismini olamiz. Bo'lmasa - bo'sh satr.
        query = self.request.GET.get('q', '').strip()
        if query:
            # Q(...) | Q(...) = "yoki". Oddiy filter(a=1, b=2) esa "va".
            # icontains = ichida bor va katta-kichik harfga qaramaydi.
            qs = qs.filter(
                Q(title__icontains=query) | Q(artist__name__icontains=query)
            )

        # Janr bo'yicha filtr: ?genre=rok
        genre = self.request.GET.get('genre', '').strip()
        if genre:
            qs = qs.filter(genres__slug=genre)

        return qs

    # get_context_data = templatega qo'shimcha ma'lumot uzatish.
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Qidiruv so'zini qaytarib yuboramiz - inputda saqlanib tursin
        context['q'] = self.request.GET.get('q', '')
        context['selected_genre'] = self.request.GET.get('genre', '')

        # Janr chiplari: faqat albomi bor janrlar ko'rinsin.
        context['genres'] = (
            Genre.objects.annotate(albums_total=Count('albums'))
            .filter(albums_total__gt=0).order_by('name')
        )

        # Sahifaning tepasidagi katta rasm (hero) va "Top albomlar" jadvali
        # faqat BIRINCHI sahifada, qidiruv ishlatilmaganda ko'rsatiladi.
        # Aks holda qidiruv natijasi ustidan begona albom chiqib qoladi.
        birinchi_sahifa = context['page_obj'].number == 1
        toza = not context['q'] and not context['selected_genre']

        if birinchi_sahifa and toza:
            # Tepadagi katta blok uchun eng yangi albom.
            # Rasm sifatida IJROCHINING surati ishlatiladi, shuning uchun
            # avval surati bor ijrochilardan qidiramiz. Topilmasa —
            # istalgan muqovali albomni olamiz (u holda muqova ko'rsatiladi).
            yangi_albomlar = (
                Album.objects.select_related('artist')
                .exclude(cover='')
                .order_by(F('release_date').desc(nulls_last=True))
            )
            # Tepadagi slayder uchun bir nechta albom tanlaymiz.
            # Tartib (yaxshidan yomonga):
            #   1. Ijrochisida CUTOUT bor — eng chiroyli ko'rinish
            #   2. Ijrochisida oddiy portret bor
            #   3. Qolganlari
            # dict.fromkeys(...) = takrorlarni olib tashlaydi va
            # qo'shilish TARTIBINI saqlaydi (set bunday qilmaydi).
            cutoutlilar = list(
                yangi_albomlar.exclude(artist__cutout='')
                              .exclude(artist__cutout=None)[:12]
            )
            portretlilar = list(
                yangi_albomlar.exclude(artist__photo='')
                              .exclude(artist__photo=None)[:12]
            )
            qolganlari = list(yangi_albomlar[:12])
            context['featured_albums'] = list(
                dict.fromkeys(cutoutlilar + portretlilar + qolganlari)
            )[:10]

            # "Top albomlar" gorizontal qatori — qo'shig'i ko'p albomlar.
            context['rail_albums'] = preview_qoshish(
                Album.objects.select_related('artist')
                .exclude(cover='')
                .annotate(songs_total=Count('songs'))
                .order_by('-songs_total', 'title')
            )[:12]

            # Pastdagi jadval — o'sha ro'yxatning qisqa, ma'lumotli ko'rinishi
            context['top_albums'] = (
                Album.objects.select_related('artist')
                .prefetch_related('genres')
                .annotate(songs_total=Count('songs'))
                .order_by('-songs_total', 'title')[:5]
            )
        return context


# ==========================================================
#  ALBOM DETAIL     ->  /albom/<ijrochi>/<albom>/
# ==========================================================
class AlbumDetailView(DetailView):
    template_name = 'music/album_detail.html'
    context_object_name = 'album'

    # Bu yerda get_object ni o'zimiz yozyapmiz, chunki albom IKKI
    # qism bo'yicha topiladi: ijrochi slugi + albom slugi.
    def get_object(self, queryset=None):
        return get_object_or_404(
            Album.objects
            .select_related('artist')
            .prefetch_related('genres', 'songs'),
            artist__slug=self.kwargs['artist_slug'],
            slug=self.kwargs['slug'],
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        album = self.object
        # related_name='songs' shu yerda ishlayapti.
        # Meta.ordering tufayli trek raqami bo'yicha tartiblangan holda keladi.
        context['songs'] = album.songs.all()
        # Shu ijrochining boshqa albomlari
        context['other_albums'] = preview_qoshish(
            album.artist.albums.exclude(pk=album.pk).select_related('artist')
        )
        # Albomning umumiy davomiyligi (millisekundlarni qo'shamiz)
        jami_ms = sum(s.duration_ms or 0 for s in context['songs'])
        context['total_minutes'] = jami_ms // 60000

        # Shablon shu bayroqqa qarab tahrirlash tugmalarini
        # ko'rsatadi yoki yashiradi
        context['ozgartira_oladi'] = ozgartira_oladimi(self.request.user, album)
        return context


# ==========================================================
#  IJROCHILAR RO'YXATI   ->  /ijrochi/
# ==========================================================
class ArtistListView(ListView):
    model = Artist
    template_name = 'music/artist_list.html'
    context_object_name = 'artists'
    paginate_by = 24

    def get_queryset(self):
        qs = (
            Artist.objects
            .annotate(albums_total=Count('albums'))
            .order_by('name')   # annotate() sababli aniq yozamiz
        )
        query = self.request.GET.get('q', '').strip()
        if query:
            qs = qs.filter(name__icontains=query)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q', '')
        return context


# ==========================================================
#  IJROCHI DETAIL   ->  /ijrochi/<slug>/
# ==========================================================
class ArtistDetailView(DetailView):
    model = Artist
    template_name = 'music/artist_detail.html'
    context_object_name = 'artist'
    # slug_field = modeldagi ustun nomi
    # slug_url_kwarg = URL dagi <slug:...> ning nomi
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['albums'] = preview_qoshish(
            self.object.albums
            .select_related('artist')
            .prefetch_related('genres')
            .annotate(songs_total=Count('songs'))
            .order_by(F('release_date').desc(nulls_last=True), 'title')
        )
        context['ozgartira_oladi'] = ozgartira_oladimi(
            self.request.user, self.object
        )
        return context


# ==========================================================
#  QO'SHISH FORMALARI
# ==========================================================
# CreateView = forma ko'rsatadi, tekshiradi, saqlaydi va yo'naltiradi.
class ArtistCreateView(CreateView):
    model = Artist
    form_class = ArtistForm
    template_name = 'music/artist_form.html'
    # success_url yozilmagan - Django modeldagi get_absolute_url() ni ishlatadi

    # form_valid = forma tekshiruvdan o'tgach ishlaydi
    def form_valid(self, form):
        # Kim qo'shsa — o'sha ega bo'ladi
        form.instance.owner = self.request.user
        messages.success(self.request, 'Ijrochi qo\'shildi.')
        return super().form_valid(form)


class AlbumCreateView(CreateView):
    model = Album
    form_class = AlbumForm
    template_name = 'music/album_form.html'

    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(self.request, 'Albom qo\'shildi.')
        return super().form_valid(form)


# Qo'shiqni ALBOMGA biriktirish.
# Albom URL dan olinadi: /albom/<pk>/qoshiq-qoshish/
class SongCreateView(CreateView):
    model = Song
    form_class = SongForm
    template_name = 'music/song_form.html'

    # dispatch = har qanday so'rovdan (GET ham, POST ham) OLDIN ishlaydi.
    # Albomni shu yerda bir marta topib olamiz.
    def dispatch(self, request, *args, **kwargs):
        self.album = get_object_or_404(Album, pk=kwargs['album_pk'])

        # Begona albomga qo'shiq qo'shib bo'lmaydi
        if not ozgartira_oladimi(request.user, self.album):
            ega = self.album.owner
            messages.error(
                request,
                f"Bu albom sizniki emas — unga qo'shiq qo'sha olmaysiz. "
                f"Egasi: {ega.username if ega else 'administrator'}."
            )
            return redirect(self.album.get_absolute_url())

        return super().dispatch(request, *args, **kwargs)

    # Formaga albomni uzatamiz (forms.py dagi __init__ uni kutyapti)
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['album'] = self.album
        return kwargs

    # Trek raqamini oldindan to'ldirib qo'yamiz: oxirgisidan keyingi son
    def get_initial(self):
        last = self.album.songs.order_by('track_number').last()
        return {'track_number': (last.track_number + 1) if last else 1}

    def form_valid(self, form):
        # Formada album maydoni yo'q edi - shuni shu yerda o'rnatamiz
        form.instance.album = self.album
        messages.success(self.request, 'Qo\'shiq albomga biriktirildi.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['album'] = self.album
        return context

    # Saqlangach albom sahifasiga qaytamiz
    def get_success_url(self):
        return self.album.get_absolute_url()


# ==========================================================
#  IMPORT — tashqi xizmatdan albom olib kelish (brauzerda)
# ==========================================================
# Nega CreateView emas, oddiy View?
#   Bu yerda forma modelga bevosita bog'lanmagan: avval QIDIRAMIZ
#   (hech narsa saqlanmaydi), keyin tanlanganini import qilamiz.
#   Shuning uchun GET va POST ni o'zimiz yozganimiz tushunarliroq.
class ImportView(View):
    template_name = 'music/import.html'

    def get(self, request):
        """?q=... bo'lsa qidiradi, bo'lmasa bo'sh sahifa ko'rsatadi."""
        query = request.GET.get('q', '').strip()
        context = {'q': query, 'provider': provider_name()}

        if query:
            try:
                context['results'] = get_client().search_albums(query, limit=12)
            except PROVIDER_ERRORS as exc:
                # Xatoni foydalanuvchiga ko'rsatamiz, sahifa "buzilmaydi".
                messages.error(request, str(exc))

        return render(request, self.template_name, context)

    def post(self, request):
        """Tanlangan albomni bazaga yozadi va uning sahifasiga o'tadi."""
        external_id = request.POST.get('external_id', '').strip()
        if not external_id:
            messages.error(request, 'Albom tanlanmadi.')
            return redirect('music:import')

        try:
            # Kim import qilsa — o'sha ega bo'ladi
            album, created = import_album(external_id, owner=request.user)
        except PROVIDER_ERRORS as exc:
            messages.error(request, str(exc))
            return redirect('music:import')

        if created:
            messages.success(
                request,
                f'"{album.title}" qo\'shildi — {album.songs.count()} ta qo\'shiq.'
            )
        else:
            messages.info(request, f'"{album.title}" allaqachon bazada bor edi.')

        return redirect(album.get_absolute_url())

# ==========================================================
#  EGALIK — kim nimani o'zgartira oladi
# ==========================================================

def egasi_kim(obyekt):
    """
    Obyektning egasini qaytaradi.

    Albom va Ijrochida "owner" maydoni bor. Qo'shiqda yo'q —
    uning egasi o'zi turgan albomning egasi hisoblanadi.
    """
    ega = getattr(obyekt, 'owner', None)
    if ega is None and hasattr(obyekt, 'album_id'):
        return obyekt.album.owner
    return ega


def ozgartira_oladimi(user, obyekt):
    """
    Shu foydalanuvchi obyektni tahrirlashi/o'chirishi mumkinmi?

    Qoidalar:
      - Administrator (superuser) — hamma narsani
      - Egasi — o'zinikini
      - Qolganlar — yo'q
      - Egasiz yozuvni faqat administrator o'zgartira oladi
    """
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    ega = egasi_kim(obyekt)
    return ega is not None and ega == user


class EgalikTalabi:
    """
    Tahrirlash/o'chirish view lariga qo'shiladigan tekshiruv.

    dispatch() ichida ishlaydi — ya'ni sahifa umuman chizilmasdan
    OLDIN. Busiz begona odam forma sahifasini ko'rib, keyingina
    to'xtatilardi.

    403 sahifa o'rniga xabar bilan qaytaramiz: foydalanuvchi uchun
    tushunarliroq va sayt ichida qoladi.
    """

    def dispatch(self, request, *args, **kwargs):
        # setup() dispatch dan oldin ishlagani uchun self.kwargs tayyor
        obyekt = self.get_object()

        if not ozgartira_oladimi(request.user, obyekt):
            ega = egasi_kim(obyekt)
            messages.error(
                request,
                f"Bu yozuv sizniki emas — uni faqat "
                f"{ega.username if ega else 'administrator'} o'zgartira oladi."
            )
            return redirect(self.rad_etilganda(obyekt))

        return super().dispatch(request, *args, **kwargs)

    def rad_etilganda(self, obyekt):
        """Ruxsat bo'lmaganda qaysi sahifaga qaytaramiz."""
        if hasattr(obyekt, 'get_absolute_url'):
            return obyekt.get_absolute_url()
        return obyekt.album.get_absolute_url()   # Qo'shiq uchun


# ==========================================================
#  TAHRIRLASH VA O'CHIRISH (CRUD ning U va D qismlari)
# ==========================================================
# UpdateView CreateView bilan deyarli bir xil ishlaydi: o'sha forma,
# o'sha shablon. Farqi — u mavjud yozuvni topib, formani to'ldirib
# beradi. Shuning uchun shablonlar QAYTA ishlatiladi.
#
# DeleteView esa GET so'rovda tasdiqlash sahifasini ko'rsatadi,
# POST kelganda o'chiradi. Bu MAJBURIY himoya: aks holda qidiruv
# roboti havolani ochib, yozuvni o'chirib yuborishi mumkin edi.


class AlbumUpdateView(EgalikTalabi, UpdateView):
    model = Album
    form_class = AlbumForm
    template_name = 'music/album_form.html'

    def form_valid(self, form):
        messages.success(self.request, 'Albom yangilandi.')
        return super().form_valid(form)


class AlbumDeleteView(EgalikTalabi, DeleteView):
    model = Album
    template_name = 'music/confirm_delete.html'
    # O'chirilgandan keyin qaytadigan manzil.
    # reverse_lazy — chunki URL lar hali yuklanmagan paytda hisoblanadi.
    success_url = reverse_lazy('music:album_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['nima'] = 'Albom'
        context['nomi'] = self.object.title
        context['izoh'] = (
            f"Albom bilan birga uning {self.object.songs.count()} ta qo'shig'i "
            f"ham o'chadi. Bu amalni orqaga qaytarib bo'lmaydi."
        )
        context['bekor_url'] = self.object.get_absolute_url()
        return context

    def form_valid(self, form):
        messages.success(self.request, f"\"{self.object.title}\" o'chirildi.")
        return super().form_valid(form)


class ArtistUpdateView(EgalikTalabi, UpdateView):
    model = Artist
    form_class = ArtistForm
    template_name = 'music/artist_form.html'

    def form_valid(self, form):
        messages.success(self.request, 'Ijrochi yangilandi.')
        return super().form_valid(form)


class ArtistDeleteView(EgalikTalabi, DeleteView):
    model = Artist
    template_name = 'music/confirm_delete.html'
    success_url = reverse_lazy('music:artist_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        albomlar = self.object.albums.count()
        context['nima'] = 'Ijrochi'
        context['nomi'] = self.object.name
        context['izoh'] = (
            f"Bu ijrochining {albomlar} ta albomi va ulardagi barcha "
            f"qo'shiqlar ham o'chadi. Bu amalni orqaga qaytarib bo'lmaydi."
            if albomlar else
            "Bu amalni orqaga qaytarib bo'lmaydi."
        )
        context['bekor_url'] = self.object.get_absolute_url()
        return context

    def form_valid(self, form):
        # Artist.albums FK on_delete=PROTECT: albomi bor ijrochini
        # o'chirishga Django ruxsat bermaydi (ProtectedError chiqaradi).
        # Yuqoridagi tasdiqlash matni "albomlari ham o'chadi" deb
        # aldamchi va'da berganidan keyin, buni ushlamasak, foydalanuvchi
        # tugmani bossa xom 500-xato ko'rardi.
        try:
            self.object.delete()
        except ProtectedError:
            messages.error(
                self.request,
                f"\"{self.object.name}\" ni o'chirib bo'lmadi — unda hali "
                f"albomlar bor. Avval albomlarini o'chiring yoki boshqa "
                f"ijrochiga o'tkazing."
            )
            return redirect(self.object.get_absolute_url())
        messages.success(self.request, f"\"{self.object.name}\" o'chirildi.")
        return redirect(self.get_success_url())


class SongUpdateView(EgalikTalabi, UpdateView):
    model = Song
    form_class = SongForm
    template_name = 'music/song_form.html'

    def get_form_kwargs(self):
        # SongForm takror trek raqamini tekshirish uchun albomni biladi
        kwargs = super().get_form_kwargs()
        kwargs['album'] = self.object.album
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['album'] = self.object.album
        return context

    def get_success_url(self):
        return self.object.album.get_absolute_url()

    def form_valid(self, form):
        messages.success(self.request, "Qo'shiq yangilandi.")
        return super().form_valid(form)


class SongDeleteView(EgalikTalabi, DeleteView):
    model = Song
    template_name = 'music/confirm_delete.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['nima'] = "Qo'shiq"
        context['nomi'] = self.object.title
        context['izoh'] = (
            f"\"{self.object.album.title}\" albomidan o'chiriladi. "
            f"Albomning o'zi joyida qoladi."
        )
        context['bekor_url'] = self.object.album.get_absolute_url()
        return context

    def get_success_url(self):
        return self.object.album.get_absolute_url()

    def form_valid(self, form):
        messages.success(self.request, f"\"{self.object.title}\" o'chirildi.")
        return super().form_valid(form)


# ==========================================================
#  AVTOTO'LDIRISH — qidiruv maydoni uchun takliflar (JSON)
# ==========================================================
def suggest(request):
    """
    Qidiruv maydoniga yozilgan matn bo'yicha albom va ijrochilarni
    qaytaradi. Sahifa emas, JSON qaytaradi — uni JavaScript o'qiydi.

    Javob shakli:
        {"albums": [{"title", "artist", "url", "cover"}, ...],
         "artists": [{"name", "url", "photo", "albums"}, ...]}
    """
    query = request.GET.get('q', '').strip()

    # Ikki harfdan qisqa so'rovga javob bermaymiz: natija juda ko'p
    # bo'ladi va har bir bosilgan tugmada bazaga so'rov ketaveradi.
    if len(query) < 2:
        return JsonResponse({'albums': [], 'artists': []})

    albums = (
        Album.objects.select_related('artist')
        .filter(Q(title__icontains=query) | Q(artist__name__icontains=query))
        .order_by('title')[:6]
    )
    artists = (
        Artist.objects.annotate(albums_total=Count('albums'))
        .filter(name__icontains=query)
        .order_by('name')[:4]
    )

    return JsonResponse({
        'albums': [
            {
                'title': a.title,
                'artist': a.artist.name,
                'year': a.release_date.year if a.release_date else '',
                'url': a.get_absolute_url(),
                'cover': a.cover.url if a.cover else '',
            }
            for a in albums
        ],
        'artists': [
            {
                'name': ar.name,
                'albums': ar.albums_total,
                'url': ar.get_absolute_url(),
                'photo': ar.photo.url if ar.photo else '',
            }
            for ar in artists
        ],
    })


@login_not_required
def logout_view(request):
    """
    Tizimdan chiqish.

    Faqat POST qabul qiladi. Nega?
        Chiqish — holatni o'zgartiradigan amal. Oddiy havola bo'lsa,
        brauzerning oldindan yuklash funksiyasi yoki sahifadagi rasm
        so'rovi uni chaqirib, foydalanuvchini o'zi bilmagan holda
        tizimdan chiqarib yuborishi mumkin.
    GET bilan kelsa — hech narsa qilmay, bosh sahifaga qaytaradi.
    """
    if request.method == 'POST':
        logout(request)
    return redirect('music:album_list')


# Ro'yxatdan o'tish sahifasi kirmagan odam uchun — tabiiyki ochiq
@method_decorator(login_not_required, name='dispatch')
class SignupView(CreateView):
    """
    Ro'yxatdan o'tish. Muvaffaqiyatli bo'lsa foydalanuvchini
    darhol tizimga kiritadi — qaytadan parol so'ramaymiz.
    """

    form_class = RoyxatForm
    template_name = 'music/signup.html'
    success_url = reverse_lazy('music:album_list')

    def dispatch(self, request, *args, **kwargs):
        # Allaqachon kirgan odam ro'yxatdan o'tishi mantiqsiz
        if request.user.is_authenticated:
            return redirect('music:album_list')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        javob = super().form_valid(form)
        # backend nomi aniq ko'rsatiladi: ikkita backend bor, Django
        # qaysi biri bilan kirganini o'zi tanlay olmaydi.
        login(self.request, self.object,
              backend='django.contrib.auth.backends.ModelBackend')
        return javob


# ==========================================================
#  GOOGLE ORQALI KIRISH (Firebase)
# ==========================================================
# Qanday ishlaydi?
#   1. Brauzer Google oynasini ochadi (static/js/firebase-auth.js)
#   2. Google "ID token" beradi — bu imzolangan JWT
#   3. Brauzer o'sha tokenni shu view ga yuboradi
#   4. BIZ uni SERVERDA tekshiramiz va faqat shundan keyin
#      foydalanuvchini tizimga kiritamiz
#
# NEGA server tomonda tekshiramiz?
#   Brauzerdan kelgan hech narsaga ishonib bo'lmaydi. Kimdir
#   "men falonchiman" deb oddiy so'rov yuborishi mumkin. Token esa
#   Google tomonidan imzolangan — imzoni faqat Google'ning ochiq
#   kalitlari bilan tekshirib, haqiqiyligiga ishonch hosil qilamiz.
#
# Maxfiy kalit KERAK EMAS: verify_firebase_token Google'ning ochiq
# kalitlarini o'zi yuklab oladi. Bizga faqat loyiha ID si kerak.

def _google_foydalanuvchi(malumot):
    """
    Tekshirilgan token ma'lumotidan Django foydalanuvchisini topadi
    yoki yaratadi.

    Tartib:
      1. Shu e-pochtali foydalanuvchi bor bo'lsa — o'sha
      2. Bo'lmasa — yangisini yaratadi (paroli yo'q)
    """
    from django.contrib.auth.models import User

    email = (malumot.get('email') or '').strip().lower()
    if not email:
        return None

    # DIQQAT: faqat PAROLSIZ (avval Google orqali yaratilgan) akkauntga
    # avtomatik bog'laymiz. Aks holda kimdir boshqa birovning pochtasi
    # bilan oddiy ro'yxatdan o'tish orqali (tekshiruvsiz) akkaunt ochib
    # qo'yishi, keyin haqiqiy egasi Google bilan kirganda O'SHA
    # (begona odam biladigan parolli) akkauntga kiritilib qolishi mumkin
    # edi — akkauntni "band qilib qo'yish" hujumi. Parollik akkaunt
    # bo'lsa, uni Google bilan avtomatik bog'lamasdan, pastda YANGI
    # (alohida) akkaunt yaratamiz.
    mavjud = User.objects.filter(email__iexact=email).order_by('id').first()
    if mavjud and not mavjud.has_usable_password():
        return mavjud

    # Foydalanuvchi nomi pochtaning @ gacha bo'lgan qismidan.
    # Band bo'lsa oxiriga raqam qo'shamiz.
    asos = slugify(email.split('@')[0]) or 'foydalanuvchi'
    nom = asos
    raqam = 2
    while User.objects.filter(username__iexact=nom).exists():
        nom = f'{asos}{raqam}'
        raqam += 1

    yangi = User(username=nom, email=email)
    ism = (malumot.get('name') or '').strip()
    if ism:
        qismlar = ism.split(None, 1)
        yangi.first_name = qismlar[0][:150]
        if len(qismlar) > 1:
            yangi.last_name = qismlar[1][:150]

    # Parol o'rnatilmaydi: bu akkauntga faqat Google orqali kiriladi.
    # set_unusable_password() parol bilan kirishni butunlay bloklaydi.
    yangi.set_unusable_password()
    yangi.save()
    return yangi


@login_not_required
def google_login(request):
    """Brauzerdan kelgan Firebase ID tokenini tekshirib, tizimga kiritadi."""
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'xato': 'Faqat POST'}, status=405)

    loyiha = settings.FIREBASE.get('projectId')
    if not loyiha:
        return JsonResponse(
            {'ok': False, 'xato': 'Firebase sozlanmagan.'}, status=503)

    token = (request.POST.get('id_token') or '').strip()
    if not token:
        return JsonResponse({'ok': False, 'xato': 'Token yuborilmadi.'}, status=400)

    try:
        # audience=loyiha -> token AYNAN bizning loyihamiz uchun
        # berilganini tekshiradi. Busiz boshqa Firebase loyihasining
        # tokeni bilan ham kirib bo'lardi.
        malumot = id_token.verify_firebase_token(
            token, google_requests.Request(), audience=loyiha
        )
    except ValueError as exc:
        logger.warning('Firebase token tekshiruvdan o\'tmadi: %s', exc)
        return JsonResponse(
            {'ok': False, 'xato': 'Token yaroqsiz yoki muddati tugagan.'},
            status=401,
        )

    if not malumot.get('email'):
        return JsonResponse(
            {'ok': False, 'xato': 'Google e-pochta ulashmadi.'}, status=400)

    # Tasdiqlanmagan pochta bilan mavjud akkauntga kirib bo'lmasin:
    # aks holda begona odam o'sha pochtani "o'zimniki" deb kirishi
    # mumkin edi. Google hisoblarida email_verified deyarli doim True.
    if not malumot.get('email_verified'):
        return JsonResponse(
            {'ok': False, 'xato': 'Google e-pochtangiz tasdiqlanmagan.'},
            status=403,
        )

    foydalanuvchi = _google_foydalanuvchi(malumot)
    if foydalanuvchi is None:
        return JsonResponse(
            {'ok': False, 'xato': 'Foydalanuvchi yaratilmadi.'}, status=400)

    login(request, foydalanuvchi,
          backend='django.contrib.auth.backends.ModelBackend')
    return JsonResponse({'ok': True, 'keyingi': str(reverse_lazy('music:album_list'))})


@method_decorator(login_not_required, name='dispatch')
class KirishView(LoginView):
    """
    Kirish sahifasi.

    Django ning tayyor LoginView i, faqat bitta farq bilan: qayerga
    qaytarishni manzildagi ?next= dan emas, SESSIYADAN oladi
    (middleware.py o'sha yerga yozib qo'ygan).
    """

    template_name = 'music/login.html'
    authentication_form = KirishForm
    redirect_authenticated_user = True

    def get_success_url(self):
        manzil = self.request.session.pop(KEYINGI_MANZIL, None)

        # Sessiyadagi qiymat o'zimiznikidan kelgan bo'lsa ham
        # tekshiramiz. Bu "ochiq yo'naltirish" xavfidan himoya:
        # begona saytga yuboradigan manzil hech qachon o'tmasin.
        if manzil and url_has_allowed_host_and_scheme(
            url=manzil,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return manzil

        return resolve_url(settings.LOGIN_REDIRECT_URL)
