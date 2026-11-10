from unittest.mock import patch

from django.db import DatabaseError
from django.test import TestCase
from django.urls import reverse


class HealthcheckTests(TestCase):
    def test_reports_ok_when_database_is_available(self):
        response = self.client.get(reverse("healthcheck"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
        self.assertEqual(
            response["Cache-Control"],
            "max-age=0, no-cache, no-store, must-revalidate, private",
        )

    @patch("core.health.connection.cursor", side_effect=DatabaseError)
    def test_reports_unavailable_when_database_cannot_be_reached(self, _cursor):
        response = self.client.get(reverse("healthcheck"))
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"status": "unavailable"})
