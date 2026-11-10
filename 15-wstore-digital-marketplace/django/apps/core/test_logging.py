from django.test import TestCase

from .logging_utils import log_error, redact_sensitive
from .models import ErrorLog


class SafeErrorLoggingTests(TestCase):
    def test_sensitive_values_are_redacted(self):
        text = (
            "token=private-value password:secret-value card_number=8600 0000 0000 0000"
        )
        safe = redact_sensitive(text)
        self.assertNotIn("private-value", safe)
        self.assertNotIn("secret-value", safe)
        self.assertNotIn("8600 0000 0000 0000", safe)
        self.assertIn("[REDACTED]", safe)
        self.assertIn("[CARD-REDACTED]", safe)

    def test_persisted_error_log_is_redacted(self):
        try:
            raise ValueError("authorization=Bearer-private-token")
        except ValueError as exc:
            log_error(exc, context="card_number=8600000000000000")

        record = ErrorLog.objects.get()
        self.assertNotIn("private-token", record.message + record.stack)
        self.assertNotIn("8600000000000000", record.context)
