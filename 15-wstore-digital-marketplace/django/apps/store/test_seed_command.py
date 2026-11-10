"""Demo ma'lumot yuklovchi productionga chiqib ketmasligini tekshiradi."""

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, override_settings


class SeedDataCommandTests(SimpleTestCase):
    @override_settings(DEBUG=True)
    def test_explicit_opt_in_is_required(self):
        with self.assertRaisesMessage(CommandError, "--allow-demo-data"):
            call_command("seed_data")

    @override_settings(DEBUG=False)
    def test_production_execution_is_refused(self):
        with self.assertRaisesMessage(CommandError, "production muhitida"):
            call_command(
                "seed_data",
                allow_demo_data=True,
                admin_password="at-least-twelve-characters",
            )
