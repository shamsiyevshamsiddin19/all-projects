"""Legacy plaintext card valuesini shifrlangan maydonlarga ko'chirish."""

from django.core.management.base import BaseCommand
from django.db import transaction

from core.crypto import card_last4, encrypt_card_number
from core.models import User
from orders.models import Withdrawal


class Command(BaseCommand):
    help = (
        "Ochiq karta raqamlarini shifrlangan maydonlarga bosqichma-bosqich "
        "ko'chiradi. Ochiq maydonlarni o'chirmaydi."
    )

    def add_arguments(self, parser):
        parser.add_argument("--batch-size", type=int, default=100)
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="O'zgarishsiz nechta yozuv topilishini ko'rsatadi.",
        )

    def handle(self, *args, **options):
        batch_size = options["batch_size"]
        if batch_size < 1:
            raise ValueError("--batch-size kamida 1 bo'lishi kerak.")

        targets = (
            ("sotuvchi profili", User, "id"),
            ("pul yechish so'rovi", Withdrawal, "id"),
        )
        total = 0
        for label, model, key_name in targets:
            queryset = model.objects.filter(
                encrypted_card_number__isnull=True,
                card_number__isnull=False,
            ).exclude(card_number="")
            count = queryset.count()
            total += count
            if options["dry_run"]:
                self.stdout.write(f"{label}: {count} ta yozuv topildi.")
                continue

            processed = 0
            for item in queryset.iterator(chunk_size=batch_size):
                card_number = "".join(ch for ch in item.card_number if ch.isdigit())
                if len(card_number) != 16:
                    self.stderr.write(
                        f"{label} {getattr(item, key_name)} o'tkazib yuborildi: "
                        "karta formati noto'g'ri."
                    )
                    continue
                with transaction.atomic():
                    model.objects.filter(pk=item.pk).update(
                        encrypted_card_number=encrypt_card_number(card_number),
                        card_last4=card_last4(card_number),
                    )
                processed += 1
            self.stdout.write(f"{label}: {processed} ta yozuv shifrlandi.")

        if options["dry_run"]:
            self.stdout.write(f"Jami: {total} ta yozuv ko'chirishga tayyor.")
