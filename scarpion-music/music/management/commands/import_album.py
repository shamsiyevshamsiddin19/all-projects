"""
Terminaldan ishlatiladigan buyruq.

Ishlatish:
    python manage.py import_album --search "the eminem show"
    python manage.py import_album 103248
    python manage.py import_album 103248 --provider spotify

Nega brauzer emas, terminal ham bor?
    Tashqi API bilan ishlashni avval shu yerda sinash osonroq:
    xato bo'lsa to'liq matni ko'rinadi, sahifa yuklanishini kutish shart emas.
    (Brauzerdagi varianti ham bor: saytda "Import" tugmasi.)
"""

from django.core.management.base import BaseCommand, CommandError

from music.services.importers import import_album
from music.services.providers import PROVIDER_ERRORS, get_client


class Command(BaseCommand):
    help = "Deezer/Spotify dan albomni qo'shiqlari bilan import qiladi"

    def add_arguments(self, parser):
        parser.add_argument('external_id', nargs='?', help='Albomning tashqi ID si')
        parser.add_argument('--search', help='ID o\'rniga nom bo\'yicha qidirish')
        parser.add_argument(
            '--provider',
            help="Xizmatni majburan tanlash: deezer yoki spotify "
                 "(bo'sh qolsa .env dagi MUSIC_PROVIDER ishlatiladi)",
        )

    def handle(self, *args, **options):
        try:
            client = get_client(options.get('provider'))
            self.stdout.write(f'Xizmat: {client.source}')

            if options['search']:
                results = client.search_albums(options['search'])
                if not results:
                    raise CommandError('Hech narsa topilmadi.')

                self.stdout.write('Topildi:')
                for item in results:
                    self.stdout.write(
                        f"  {item['external_id']:<12} {item['artist_name']} - "
                        f"{item['title']} ({item['release_date']})"
                    )
                self.stdout.write(self.style.WARNING(
                    '\nKeraklisini tanlab: python manage.py import_album <ID>'
                ))
                return

            if not options['external_id']:
                raise CommandError('Tashqi ID yoki --search kerak.')

            album, created = import_album(options['external_id'], client=client)

        except PROVIDER_ERRORS as exc:
            raise CommandError(str(exc))

        if created:
            self.stdout.write(self.style.SUCCESS(
                f'Qo\'shildi: {album}  ({album.songs.count()} ta qo\'shiq)'
            ))
        else:
            self.stdout.write(self.style.WARNING(f'Allaqachon mavjud: {album}'))
