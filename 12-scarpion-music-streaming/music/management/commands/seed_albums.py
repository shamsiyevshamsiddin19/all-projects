"""
Bazani mashhur albomlar bilan to'ldiradi.

Ishlatish:
    python manage.py seed_albums              # ro'yxatdagi hammasini
    python manage.py seed_albums --limit 10   # faqat birinchi 10 tasini
    python manage.py seed_albums --delay 1.5  # so'rovlar orasini kengaytirish

Nega kerak?
    Yangi o'rnatilgan loyihada baza bo'sh bo'ladi va sayt qanday
    ko'rinishini tushunish qiyin. Bu buyruq bir urinishda tanishroq
    albomlarni olib keladi.

Qanday ishlaydi?
    Har bir albom uchun katalogdan "nom + ijrochi" bo'yicha qidiradi,
    natijalardan eng mosini tanlaydi va import qiladi. Import ijrochini
    ham, muqovani ham, qo'shiqlarni ham o'zi oladi.
"""

import time
import unicodedata

from django.core.management.base import BaseCommand

from music.models import Album
from music.services.importers import import_album
from music.services.providers import PROVIDER_ERRORS, get_client

# (ijrochi, albom) juftliklari. Turli janr va o'n yilliklardan tanlangan.
#
# DIQQAT: Deezer kataloging HUDUDIY cheklovlari bor. Ba'zi mashhur
# albomlar (Dua Lipa, Gorillaz, Coldplay, Linkin Park, Red Hot Chili
# Peppers, Ed Sheeran) bu yerdan umuman ochilmaydi — faqat singl va
# jonli yozuvlari ko'rinadi. Shuning uchun ro'yxatda ular yo'q.
# Yangi albom qo'shishdan oldin mavjudligini tekshiring:
#     python manage.py import_album --search "albom nomi ijrochi"
ALBOMLAR = [
    # --- Klassikalar ---
    ('Pink Floyd', 'The Dark Side of the Moon'),
    ('Pink Floyd', 'The Wall'),
    ('Pink Floyd', 'Wish You Were Here'),
    ('The Beatles', 'Revolver'),
    ('The Beatles', 'Let It Be'),
    ('Led Zeppelin', 'Houses of the Holy'),
    ('Queen', 'Greatest Hits'),
    ('The Rolling Stones', 'Let It Bleed'),
    ('David Bowie', "Let's Dance"),
    ('Elton John', 'Goodbye Yellow Brick Road'),
    ('Abba', 'Gold'),

    # --- Pop ---
    ('Michael Jackson', 'Thriller'),
    ('Michael Jackson', 'Bad'),
    ('Michael Jackson', 'Off the Wall'),
    ('Adele', '21'),
    ('Adele', '25'),
    ('Adele', '30'),
    ('Taylor Swift', '1989'),
    ('Taylor Swift', 'folklore'),
    ('Rihanna', 'Anti'),
    ('Rihanna', 'Loud'),
    ('Beyonce', 'Lemonade'),
    ('Dua Lipa', 'Radical Optimism'),
    ('Maroon 5', 'Songs About Jane'),
    ('Imagine Dragons', 'Night Visions'),

    # --- Rok va alternativ ---
    ('Nirvana', 'Nevermind'),
    ('Nirvana', 'In Utero'),
    ('Radiohead', 'OK Computer'),
    ('Radiohead', 'The Bends'),
    ('Metallica', 'Metallica'),
    ('Metallica', 'Master of Puppets'),
    ('AC/DC', 'Back in Black'),
    ('AC/DC', 'Highway to Hell'),
    ('Oasis', "(What's the Story) Morning Glory?"),
    ('Arctic Monkeys', 'AM'),
    ('Arctic Monkeys', 'Favourite Worst Nightmare'),

    # --- Hip-hop va R&B ---
    ('Eminem', 'The Marshall Mathers LP'),
    ('50 Cent', 'Get Rich or Die Tryin'),
    ('Kendrick Lamar', 'good kid, m.A.A.d city'),
    ('Kendrick Lamar', 'DAMN.'),
    ('Kendrick Lamar', 'To Pimp a Butterfly'),
    ('Kanye West', 'Graduation'),
    ('Kanye West', 'The College Dropout'),
    ('Drake', 'Take Care'),
    ('Drake', 'Views'),
    ('The Weeknd', 'After Hours'),
    ('The Weeknd', 'Starboy'),
    ('Post Malone', "Hollywood's Bleeding"),
    ('SZA', 'SOS'),
    ('Stevie Wonder', 'Songs in the Key of Life'),
    ('Marvin Gaye', "What's Going On"),

    # --- Boshqa janrlar ---
    ('Amy Winehouse', 'Back to Black'),
    ('Amy Winehouse', 'Frank'),
    ('Lana Del Rey', 'Born To Die'),
    ('Lana Del Rey', 'Norman Fucking Rockwell'),
    ('Billie Eilish', 'When We All Fall Asleep, Where Do We Go?'),
    ('Billie Eilish', 'Happier Than Ever'),
    ('Bob Marley', 'Legend'),
    ('Bob Marley', 'Exodus'),
    ('Miles Davis', 'Kind of Blue'),
    ('Miles Davis', 'Bitches Brew'),
    ('Norah Jones', 'Come Away With Me'),
    ('Johnny Cash', 'At Folsom Prison'),
]

# Qidiruv natijalarida uchraydigan, bizga KERAK EMAS nusxalar.
# Karaoke va tribute albomlarining muqovasi ham, ijrochisi ham boshqa —
# ular ro'yxatni buzadi.
KERAKSIZ = ('karaoke', 'tribute', 'made famous by', 'in the style of',
            'instrumental', 'cover version', 'workout', 'lullaby',
            'a tribute to', 'piano cover', 'the violin covers',
            'renditions of', 'hip hop takes on')

# Jonli yozuvlar: studiya albomi o'rniga tushib qolmasin.
# Agar SO'RALGAN nomda "live" bo'lsa bu filtr o'chadi.
JONLI = ('live at', 'live in', 'live from', '(live)', '- live',
         'live 19', 'live 20', 'concert', 'unplugged', 'tour')


def sodda(matn):
    """
    Taqqoslash uchun matnni soddalashtiradi:
        "Beyoncé" -> "beyonce",  "AC/DC" -> "ac/dc"

    Nega kerak? Ro'yxatda "Beyonce" deb yozgan bo'lsak, katalogda
    "Beyoncé" turadi — urg'u belgisi tufayli moslik topilmay qolardi.
    NFKD harfni "e" + "urg'u" ga ajratadi, keyin urg'uni tashlaymiz.
    """
    matn = unicodedata.normalize('NFKD', matn)
    return ''.join(c for c in matn if not unicodedata.combining(c)).lower()


class Command(BaseCommand):
    help = "Bazani mashhur albomlar bilan to'ldiradi"

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, help='Nechta albom qo\'shilsin')
        parser.add_argument(
            '--delay', type=float, default=0.8,
            help="So'rovlar orasidagi tanaffus, soniyada (sukut: 0.8)",
        )

    def tanla(self, natijalar, ijrochi, albom):
        """
        Qidiruv natijalaridan eng mosini tanlaydi.

        Tartib:
          1. Ijrochi nomi mos VA albom nomi mos
          2. Faqat ijrochi nomi mos
          3. Hech nima — None
        Karaoke/tribute nusxalari umuman ko'rib chiqilmaydi.
        """
        ijrochi_k = sodda(ijrochi)
        albom_k = sodda(albom)
        jonli_soralgan = 'live' in albom_k

        tozalar = []
        for item in natijalar:
            nom = sodda(item['title'])
            matn = nom + ' ' + sodda(item['artist_name'])
            if any(x in matn for x in KERAKSIZ):
                continue
            if not jonli_soralgan and any(x in nom for x in JONLI):
                continue
            tozalar.append(item)

        # 1-bosqich: ijrochi ham, albom nomi ham mos
        for item in tozalar:
            if (ijrochi_k in sodda(item['artist_name'])
                    and albom_k[:12] in sodda(item['title'])):
                return item

        # 2-bosqich: faqat ijrochi mos, lekin albom nomi ham yaqin bo'lsin.
        # Busiz "Rumours" so'ralganda o'sha ijrochining butunlay boshqa
        # albomi tushib qolardi.
        for item in tozalar:
            if (ijrochi_k in sodda(item['artist_name'])
                    and albom_k[:6] in sodda(item['title'])):
                return item

        return None

    def handle(self, *args, **options):
        # Terminaldan qo'shilgan albomlar birinchi administratorga
        # tegishli bo'lsin — aks holda egasiz qolib, ularni faqat
        # admin panel orqali boshqarish mumkin bo'lardi.
        from django.contrib.auth.models import User
        egasi = User.objects.filter(is_superuser=True).order_by('id').first()

        client = get_client()
        royxat = ALBOMLAR[:options['limit']] if options['limit'] else ALBOMLAR

        self.stdout.write(f'Xizmat: {client.source} | {len(royxat)} ta albom\n')
        qoshildi = bor_edi = topilmadi = xato = 0

        for i, (ijrochi, albom) in enumerate(royxat, start=1):
            nom = f'{ijrochi} — {albom}'
            try:
                natijalar = client.search_albums(f'{albom} {ijrochi}', limit=8)
                tanlangan = self.tanla(natijalar, ijrochi, albom)

                if not tanlangan:
                    topilmadi += 1
                    self.stdout.write(self.style.WARNING(f'  ?  {nom}  — topilmadi'))
                    continue

                if Album.objects.filter(
                    source=client.source, external_id=tanlangan['external_id']
                ).exists():
                    bor_edi += 1
                    self.stdout.write(f'  =  {nom}  — allaqachon bor')
                    continue

                obj, yangi = import_album(
                    tanlangan['external_id'], client=client, owner=egasi
                )
                qoshildi += 1
                self.stdout.write(self.style.SUCCESS(
                    f"  +  {obj}  ({obj.songs.count()} ta qo'shiq)"
                ))

            except PROVIDER_ERRORS as exc:
                xato += 1
                self.stdout.write(self.style.ERROR(f'  !  {nom}  — {exc}'))
            except Exception as exc:
                xato += 1
                self.stdout.write(self.style.ERROR(f'  !  {nom}  — {type(exc).__name__}: {exc}'))

            # Katalog so'rovlar sonini cheklaydi — ketma-ket urmaymiz
            if i < len(royxat):
                time.sleep(options['delay'])

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Tayyor: {qoshildi} ta qo\'shildi, {bor_edi} ta bor edi, '
            f'{topilmadi} ta topilmadi, {xato} ta xato.'
        ))
        self.stdout.write(
            f'Bazada jami: {Album.objects.count()} ta albom.\n'
            f"Ijrochi rasmlarini olish uchun: python manage.py fetch_artist_art"
        )
