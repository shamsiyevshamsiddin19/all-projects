"""
Bazadagi ijrochilarga TheAudioDB dan chiroyli rasmlar qo'shadi.

Ishlatish:
    python manage.py fetch_artist_art              # bo'sh maydonlarni to'ldiradi
    python manage.py fetch_artist_art --force      # eski rasm ustiga yozadi
    python manage.py fetch_artist_art --name Queen # faqat bitta ijrochiga

Nega alohida buyruq?
    Import paytida ham chaqiriladi, lekin bu maydonlar keyin qo'shilgani
    uchun ILGARI import qilinganlarda bo'sh. Shu buyruq ularni to'ldiradi.
"""

import time

from django.core.management.base import BaseCommand

from music.models import Artist
from music.services.importers import fetch_artist_artwork


class Command(BaseCommand):
    help = "Ijrochilarga TheAudioDB dan cutout/banner/portret rasm qo'shadi"

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Mavjud rasmlar ustiga yozadi',
        )
        parser.add_argument(
            '--name',
            help="Faqat shu nomdagi ijrochi (qismiy moslik ham bo'ladi)",
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=1.2,
            help="So'rovlar orasidagi tanaffus, soniyada (sukut: 1.2)",
        )

    def handle(self, *args, **options):
        qs = Artist.objects.all().order_by('name')
        if options['name']:
            qs = qs.filter(name__icontains=options['name'])

        jami = qs.count()
        if not jami:
            self.stdout.write(self.style.WARNING('Ijrochi topilmadi.'))
            return

        self.stdout.write(f'{jami} ta ijrochi tekshiriladi...\n')
        yangilangan = topilmagan = 0

        for i, artist in enumerate(qs, start=1):
            try:
                natija = fetch_artist_artwork(artist, force=options['force'])
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f'  {artist.name}: {exc}'))
                continue

            if natija:
                yangilangan += 1
                self.stdout.write(self.style.SUCCESS(
                    f'  {artist.name:24} + {", ".join(natija)}'
                ))
            else:
                topilmagan += 1
                self.stdout.write(f'  {artist.name:24}   topilmadi yoki allaqachon bor')

            # TheAudioDB so'rovlar sonini cheklaydi — ketma-ket urmaymiz.
            if i < jami:
                time.sleep(options['delay'])

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Tayyor: {yangilangan} ta yangilandi, {topilmagan} ta o\'zgarmadi.'
        ))
