"""
.po fayllarini .mo ga kompilyatsiya qiladi — `polib` orqali, sof Python'da.

Nega standart `compilemessages` emas: u tizimda GNU gettext (`msgfmt`)
o'rnatilgan bo'lishini talab qiladi. Bu mashinada u yo'q va server uchun
ham qo'shimcha paket o'rnatish kerak bo'lardi. polib esa oddiy pip paketi
va aynan shu ishni bajaradi.

Ishlatish:
    python manage.py compilepo          # barcha tillar
    python manage.py compilepo --lang ru
"""
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = ".po fayllarini .mo ga kompilyatsiya qiladi (gettext shart emas)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--lang",
            help="Faqat shu tilni kompilyatsiya qilish (masalan: ru)",
        )

    def handle(self, *args, **options):
        try:
            import polib
        except ImportError:
            raise CommandError(
                "polib o'rnatilmagan. O'rnatish: pip install polib"
            )

        locale_paths = [Path(p) for p in getattr(settings, "LOCALE_PATHS", [])]
        if not locale_paths:
            raise CommandError("settings.LOCALE_PATHS bo'sh.")

        only = options.get("lang")
        total = 0

        for base in locale_paths:
            if not base.exists():
                self.stderr.write(f"Topilmadi: {base}")
                continue
            for po_path in sorted(base.glob("*/LC_MESSAGES/*.po")):
                lang = po_path.parent.parent.name
                if only and lang != only:
                    continue
                po = polib.pofile(str(po_path))
                mo_path = po_path.with_suffix(".mo")
                po.save_as_mofile(str(mo_path))
                translated = len([e for e in po if e.msgstr])
                self.stdout.write(
                    f"  {lang}: {translated}/{len(po)} tarjima -> {mo_path.name}"
                )
                total += 1

        if not total:
            raise CommandError("Hech qanday .po fayl topilmadi.")
        self.stdout.write(self.style.SUCCESS(f"{total} ta fayl kompilyatsiya qilindi."))
