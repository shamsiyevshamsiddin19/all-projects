from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from core.crypto import decrypt_card_number
from core.models import User
from orders.models import Withdrawal


class CardEncryptionTests(TestCase):
    def test_backfill_encrypts_legacy_values_and_clears_with_confirmation(self):
        seller = User.objects.create_user(
            username="legacy-card", email="legacy-card@example.com"
        )
        seller.card_number = "8600 0000 0000 1234"
        seller.save(update_fields=["card_number"])
        withdrawal = Withdrawal.objects.create(
            seller=seller,
            amount="50000",
            card_number="9860 0000 0000 5678",
        )

        output = StringIO()
        call_command(
            "backfill_encrypted_cards",
            "--clear-plaintext",
            "--confirm-clear-plaintext",
            stdout=output,
        )

        seller.refresh_from_db()
        withdrawal.refresh_from_db()
        self.assertEqual(seller.card_last4, "1234")
        self.assertEqual(
            decrypt_card_number(seller.encrypted_card_number), "8600000000001234"
        )
        self.assertEqual(withdrawal.card_last4, "5678")
        self.assertEqual(
            decrypt_card_number(withdrawal.encrypted_card_number), "9860000000005678"
        )
        self.assertEqual(seller.card_number, "")
        self.assertEqual(withdrawal.card_number, "")
        self.assertIn(
            "sotuvchi profili: 1 ta yozuv shifrlandi va ochiq maydon tozalandi",
            output.getvalue(),
        )

    def test_dry_run_does_not_change_legacy_value(self):
        user = User.objects.create_user(username="dry", email="dry@example.com")
        user.card_number = "8600 0000 0000 1234"
        user.save(update_fields=["card_number"])

        call_command("backfill_encrypted_cards", "--dry-run", stdout=StringIO())

        user.refresh_from_db()
        self.assertIsNone(user.encrypted_card_number)

    def test_clearing_plaintext_requires_explicit_confirmation(self):
        with self.assertRaisesMessage(ValueError, "--confirm-clear-plaintext"):
            call_command("backfill_encrypted_cards", "--clear-plaintext")
