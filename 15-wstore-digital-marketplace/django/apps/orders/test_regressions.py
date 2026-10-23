import hashlib
import tempfile
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from store.models import Category, Product
from .models import ClickTransaction, Order, Withdrawal
from .utils import amounts_match, check_click_auth

User = get_user_model()


@override_settings(DEMO_MODE=False, CLICK_BRIDGE_SECRET="test-only-bridge-secret", CLICK_SECRET_KEY="test-only-direct-secret")
class PaymentRegressionTests(TestCase):
    def setUp(self):
        self.seller = User.objects.create_user("seller-a", email="seller-a@example.com", role="SELLER", seller_since=timezone.now(), balance=100000)
        self.buyer = User.objects.create_user("buyer-a", email="buyer-a@example.com")
        self.product = Product.objects.create(title="Source archive", description="A project", seller=self.seller,
            category=Category.objects.create(name="Code", slug="code"), price=10, status="ACTIVE")
        self.order = Order.objects.create(buyer=self.buyer, product=self.product, amount=126000)
        self.tx = ClickTransaction.objects.create(order=self.order, product=self.product, kind="PURCHASE", amount=126000)
        self.tx.merchant_trans_id = f"WSTP{self.tx.pk}"
        self.tx.save()

    def complete(self, **extra):
        payload = {"secret": "test-only-bridge-secret", "merchant_trans_id": self.tx.merchant_trans_id,
                   "amount": "126000", "click_trans_id": "12345", "error": "0", **extra}
        return self.client.post("/api/click/complete", payload)

    def test_completion_and_retry_credit_only_once(self):
        self.assertEqual(self.complete().json()["error"], 0)
        self.order.refresh_from_db()
        token = self.order.download_token
        self.assertEqual(self.complete().json()["error"], 0)
        self.order.refresh_from_db()
        self.seller.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual(self.seller.balance, 226000)
        self.assertEqual(self.product.sales_count, 1)
        self.assertEqual(self.order.download_token, token)

    def test_second_transaction_for_same_order_does_not_credit_twice(self):
        self.complete()
        self.tx = ClickTransaction.objects.create(order=self.order, product=self.product, kind="PURCHASE", amount=126000)
        self.tx.merchant_trans_id = f"WSTP{self.tx.pk}"
        self.tx.save()
        self.assertEqual(self.complete().json()["error"], 0)
        self.seller.refresh_from_db()
        self.assertEqual(self.seller.balance, 226000)

    def test_failed_payment_cannot_later_complete(self):
        self.assertEqual(self.complete(error="-1").json()["error"], -9)
        self.assertEqual(self.complete().json()["error"], -9)
        self.seller.refresh_from_db()
        self.assertEqual(self.seller.balance, 100000)

    def test_invalid_payloads_do_not_raise_server_errors(self):
        for payload in ([], ["bad"], 42, {"sign_string": ["bad"]}):
            with self.subTest(payload=payload):
                response = self.client.post("/api/click/complete", payload, content_type="application/json")
                self.assertEqual(response.status_code, 200)
                self.assertNotEqual(response.json()["error"], 0)
        self.assertEqual(self.complete(error="invalid").json()["error"], -8)

    @override_settings(CLICK_BRIDGE_SECRET="wstore_secret_bridge_key", CLICK_SECRET_KEY="")
    def test_public_default_secret_is_never_accepted(self):
        self.assertFalse(check_click_auth({"secret": "wstore_secret_bridge_key"}, 1))
        self.assertNotEqual(self.complete(secret="wstore_secret_bridge_key").json()["error"], 0)

    def test_complete_signature_includes_prepare_id_and_exact_amount(self):
        payload = {"click_trans_id": "12345", "service_id": "99657", "merchant_trans_id": self.tx.merchant_trans_id,
                   "merchant_prepare_id": str(self.tx.pk), "amount": "126000.00", "action": "1", "sign_time": "2026-10-22 12:00:00"}
        raw = f"1234599657test-only-direct-secret{self.tx.merchant_trans_id}{self.tx.pk}126000.0012026-10-22 12:00:00"
        payload["sign_string"] = hashlib.md5(raw.encode()).hexdigest()
        self.assertTrue(check_click_auth(payload, 1))
        self.assertEqual(self.client.post("/api/click/complete", payload).json()["error"], 0)
        payload["merchant_prepare_id"] = "999999"
        self.assertFalse(check_click_auth(payload, 1))

    def test_amounts_are_finite_and_exact(self):
        self.assertTrue(amounts_match("126000.00", Decimal("126000")))
        for value in ("NaN", "Infinity", "126000.001", None, {}):
            self.assertFalse(amounts_match(value, 126000))

    def test_missing_archive_does_not_create_checkout_or_fake_download(self):
        self.client.force_login(self.buyer)
        count = Order.objects.count()
        self.assertEqual(self.client.post(reverse("orders:checkout", args=[self.product.pk])).status_code, 302)
        self.assertEqual(Order.objects.count(), count)
        self.order.status = "PAID"
        self.order.download_token = "paid-no-archive"
        self.order.save()
        self.assertEqual(self.client.get("/api/download/paid-no-archive/").status_code, 404)
        self.order.refresh_from_db()
        self.assertEqual(self.order.download_count, 0)

    def test_download_requires_owner_and_preserves_real_archive(self):
        with tempfile.TemporaryDirectory() as media, override_settings(MEDIA_ROOT=media):
            self.product.file_archive.save("project.tar.gz", SimpleUploadedFile("project.tar.gz", b"test archive"))
            self.order.status = "PAID"
            self.order.download_token = "real-archive"
            self.order.save()
            self.client.force_login(self.seller)
            self.assertEqual(self.client.get("/api/download/real-archive/").status_code, 403)
            self.client.force_login(self.buyer)
            response = self.client.get("/api/download/real-archive/")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(b"".join(response.streaming_content), b"test archive")
            self.assertIn(".tar.gz", response["Content-Disposition"])
            self.assertEqual(response["Cache-Control"], "private, no-store")

    @patch("orders.views.send_telegram_notification")
    def test_withdrawal_succeeds_and_balance_cannot_go_negative(self, notify):
        self.client.force_login(self.seller)
        data = {"amount": "60000", "card_number": "8600000000000000"}
        self.assertEqual(self.client.post(reverse("orders:seller_balance"), data).status_code, 302)
        self.seller.refresh_from_db()
        self.assertEqual(self.seller.balance, 40000)
        self.client.post(reverse("orders:seller_balance"), data)
        self.seller.refresh_from_db()
        self.assertEqual(self.seller.balance, 40000)
        self.assertEqual(Withdrawal.objects.count(), 1)
        self.assertNotIn("8600000000000000", notify.call_args.args[0])

    def test_deleted_product_is_hidden_but_purchase_remains(self):
        self.product.is_deleted = True
        self.product.save()
        self.assertEqual(self.client.get(reverse("store:product_detail", args=[self.product.slug])).status_code, 404)
        self.client.force_login(self.buyer)
        self.assertEqual(self.client.get(reverse("orders:order_status", args=[self.order.pk])).status_code, 200)

    def test_nonfinite_catalog_filters_are_ignored(self):
        for value in ("NaN", "Infinity", "1e999999", "abc"):
            self.assertEqual(self.client.get("/", {"min_price": value, "max_price": value}).status_code, 200)

    def test_revenue_uses_paid_order_amount_not_current_product_price(self):
        self.order.status = "PAID"
        self.order.save()
        self.product.price = 999
        self.product.is_deleted = True
        self.product.save()
        self.client.force_login(self.seller)
        response = self.client.get(reverse("orders:seller_dashboard"))
        self.assertEqual(response.context["total_sales"], 1)
        self.assertEqual(response.context["revenue"], 126000)
