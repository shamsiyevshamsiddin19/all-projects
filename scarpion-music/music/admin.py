from django.contrib import admin

# Nuqta (.) = "shu papkadagi", ya'ni music/models.py
from .models import Genre, Artist, Album, Song


# Inline = bitta modelni BOSHQA modelning sahifasi ichiga joylashtirish.
# Bu yerda: albom sahifasining pastida qo'shiqlar jadvali turadi.
# Aynan shu "qo'shiqlarni albomga biriktirish" talabini hal qiladi.
class SongInline(admin.TabularInline):   # TabularInline = jadval ko'rinishida
    model = Song
    extra = 3                            # bo'sh 3 qator tayyor tursin
    fields = ('track_number', 'title', 'duration_ms')
    ordering = ('track_number',)


# @admin.register(...) = dekorator. "Pastdagi klass - Genre uchun
# admin sozlamasi, uni panelga ulab qo'y" degani.
@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    # Ro'yxat sahifasida qaysi ustunlar ko'rinsin
    list_display = ('name', 'slug')
    # DIQQAT: oxiridagi vergul. ('name') - bu matn, ('name',) - bittalik ro'yxat!
    search_fields = ('name',)
    # slug ni name dan avtomatik to'ldiradi (brauzerda, yozayotganingizda)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    list_display = ('name', 'albums_count', 'source', 'created_at')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}

    # Oddiy maydon emas, hisoblab chiqariladigan ustun.
    # models.py dagi related_name='albums' aynan shu yerda ishlayapti.
    @admin.display(description='Albomlari')
    def albums_count(self, obj):
        return obj.albums.count()


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    list_display = ('title', 'artist', 'release_date', 'songs_count', 'source')
    # O'ng tomonda filtr paneli chiqadi
    list_filter = ('source', 'genres', 'release_date')
    # artist__name dagi IKKITA ostki chiziq = "albomdan artist ga o't,
    # undan name ni ol". Bog'langan jadvalga kirishning standart usuli.
    search_fields = ('title', 'artist__name')
    prepopulated_fields = {'slug': ('title',)}
    # M2M uchun qulay ikki panelli tanlagich
    filter_horizontal = ('genres',)
    # Kvadrat qavs - chunki bir nechta inline bo'lishi mumkin
    inlines = [SongInline]
    # Ijrochi ro'yxati uzun bo'lsa, oddiy select o'rniga qidiruvli maydon
    autocomplete_fields = ('artist',)

    # Ro'yxat sahifasida N+1 so'rovning oldini oladi:
    # har bir albom uchun alohida "ijrochi kim?" so'rovi yuborilmaydi.
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('artist')

    @admin.display(description="Qo'shiqlar")
    def songs_count(self, obj):
        return obj.songs.count()


@admin.register(Song)
class SongAdmin(admin.ModelAdmin):
    list_display = ('track_number', 'title', 'album', 'duration_display')
    list_filter = ('album',)
    search_fields = ('title', 'album__title')
    autocomplete_fields = ('album',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('album')


# Admin panelning sarlavhalarini o'zbekchaga o'giramiz
admin.site.site_header = 'Albomlar boshqaruvi'
admin.site.site_title = 'Albomlar'
admin.site.index_title = 'Boshqaruv paneli'
