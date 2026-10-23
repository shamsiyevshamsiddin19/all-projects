"""Sotuvchi API chegaralari va shu mahsulotlarni tahrirlovchi formalar."""
import json
from decimal import Decimal
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone
from PIL import Image

from core.api import MAX_BODY
from core.models import ApiToken, User
from orders.models import Order
from store.forms import ProductForm, ReviewForm
from store.models import Category, Product


class SellerApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.seller = User.objects.create_user(
            username="seller", email="seller@example.com", role=User.Role.SELLER,
        )
        cls.other = User.objects.create_user(
            username="other", email="other@example.com", role=User.Role.SELLER,
        )
        cls.buyer = User.objects.create_user(username="buyer", email="buyer@example.com")
        cls.token, cls.raw_token = ApiToken.generate(cls.seller, "Regression")
        cls.category = Category.objects.create(name="Saytlar", slug="sites")
        cls.product = Product.objects.create(
            title="Own product", description="Original", price="12.34",
            category=cls.category, seller=cls.seller, status=Product.Status.ACTIVE,
        )
        cls.foreign = Product.objects.create(
            title="Other product", price="20.00", category=cls.category,
            seller=cls.other, status=Product.Status.ACTIVE,
        )

    def setUp(self):
        self.client.defaults["HTTP_AUTHORIZATION"] = f"Bearer {self.raw_token}"
        self.detail = f"/api/v1/products/{self.product.pk}"

    def payload(self, **changes):
        return {"title": "New product", "price": "19.99", "category": "sites", **changes}

    def write(self, method, url, data):
        return self.client.generic(method.upper(), url, json.dumps(data), content_type="application/json")

    def test_create_is_owned_draft_and_preserves_decimal(self):
        response = self.write("post", "/api/v1/products", self.payload(
            seller=str(self.other.pk), status="ACTIVE", sales_count=99,
            title="  New product  ", tech_stack=[" Django "], features=["API"],
            demo_url="https://example.com/demo", cover_url="http://example.com/cover.png",
        ))
        self.assertEqual(response.status_code, 201, response.content)
        product = Product.objects.get(pk=response.json()["product"]["id"])
        self.assertEqual(product.seller, self.seller)
        self.assertEqual(product.status, Product.Status.DRAFT)
        self.assertEqual(product.sales_count, 0)
        self.assertEqual(product.price, Decimal("19.99"))
        self.assertEqual(product.title, "New product")
        self.assertEqual(product.tech_stack, ["Django"])

    def test_ownership_for_reads_writes_and_stats(self):
        Order.objects.create(buyer=self.buyer, product=self.foreign, amount=500, status="PAID")
        response = self.client.get("/api/v1/products")
        self.assertEqual(response.json()["count"], 1)
        self.assertEqual(response.json()["products"][0]["id"], str(self.product.pk))
        foreign_url = f"/api/v1/products/{self.foreign.pk}"
        for method in ("get", "patch", "delete"):
            with self.subTest(method=method):
                response = self.write(method, foreign_url, {"title": "Stolen"})
                self.assertEqual(response.status_code, 404)
        self.foreign.refresh_from_db()
        self.assertEqual(self.foreign.title, "Other product")
        self.assertFalse(self.foreign.is_deleted)
        stats = self.client.get("/api/v1/stats").json()
        self.assertEqual(stats["summary"]["paid_orders"], 0)
        self.assertEqual(stats["summary"]["revenue_som"], 0)
        self.assertEqual([row["id"] for row in stats["by_product"]], [str(self.product.pk)])

    def test_missing_invalid_and_revoked_tokens(self):
        self.token.revoked_at = timezone.now()
        self.token.save(update_fields=["revoked_at"])
        for header in ("", "Bearer wst_invalid", f"Bearer {self.raw_token}"):
            self.client.defaults["HTTP_AUTHORIZATION"] = header
            for url in ("/api/v1/me", "/api/v1/categories", "/api/v1/products",
                        "/api/v1/stats", self.detail):
                with self.subTest(header=header[:12], url=url):
                    self.assertEqual(self.client.get(url).status_code, 401)
            self.assertEqual(self.write("post", "/api/v1/products", self.payload()).status_code, 401)
            self.assertEqual(self.write("patch", self.detail, {"title": "Changed"}).status_code, 401)
            self.assertEqual(self.client.delete(self.detail).status_code, 401)
        self.token.refresh_from_db()
        self.assertIsNone(self.token.last_used_at)

    def test_inactive_and_no_longer_seller_tokens_are_rejected(self):
        for updates in ({"is_active": False}, {"is_active": True, "role": User.Role.BUYER}):
            User.objects.filter(pk=self.seller.pk).update(**updates)
            for method, url, payload in (
                ("get", "/api/v1/me", {}), ("get", "/api/v1/categories", {}),
                ("get", "/api/v1/stats", {}), ("get", "/api/v1/products", {}),
                ("post", "/api/v1/products", self.payload()),
                ("patch", self.detail, {"title": "Changed"}), ("delete", self.detail, {}),
            ):
                with self.subTest(updates=updates, method=method, url=url):
                    self.assertEqual(self.write(method, url, payload).status_code, 403)
        self.token.refresh_from_db()
        self.assertIsNone(self.token.last_used_at)

    def test_malformed_json_and_non_object_bodies(self):
        bodies = [b"{", b"\xff", b"[]", b"null", b"true", b"12", b'"text"',
                  b'{"price": NaN}', b'{"price": Infinity}', b'{"price": -Infinity}',
                  b"[" * 1100 + b"]" * 1100]
        for method, url in (("post", "/api/v1/products"), ("patch", self.detail)):
            for body in bodies:
                with self.subTest(method=method, body=body[:30]):
                    response = getattr(self.client, method)(url, body, content_type="application/json")
                    self.assertEqual(response.status_code, 400, response.content)
                    self.assertFalse(response.json()["ok"])
            response = getattr(self.client, method)(url, b" " * (MAX_BODY + 1),
                                                     content_type="application/json")
            self.assertEqual(response.status_code, 413)

    @override_settings(DATA_UPLOAD_MAX_MEMORY_SIZE=10)
    def test_django_body_limit_returns_json_error(self):
        response = self.write("post", "/api/v1/products", self.payload())
        self.assertEqual(response.status_code, 413)
        self.assertFalse(response.json()["ok"])

    def test_invalid_fields_return_400_without_mutation(self):
        invalid = {
            "title": [None, False, 1, [], {}, "", "  ", "x" * 256],
            "description": [None, False, 1, [], {}],
            "subcategory": [False, 1, [], {}, "x" * 51],
            "category": [None, False, 1, [], {}, "missing", "x" * 101],
            "status": [None, False, 1, [], {}],
            "price": [None, True, False, [], {}, "bad", "NaN", "sNaN", "Infinity",
                      "-Infinity", 0, -1, "0.001", "10000000000", "1e100000", "1e-100000"],
            "cover_url": [False, 1, [], {}, "javascript:alert(1)", "ftp://example.com/a",
                          "//example.com/a", "https://", "https://example.com/" + "x" * 500],
            "demo_url": [False, 1, [], {}, "data:text/html,test", "ftp://example.com/a",
                         "https://example.com/" + "x" * 200],
            "tech_stack": [None, False, 1, {}, "Django", [1], [None], [{}], [[]], [""]],
            "features": [None, False, 1, {}, "feature", [True], ["  "], [{}]],
        }
        for field, values in invalid.items():
            for value in values:
                for method, url in (("post", "/api/v1/products"), ("patch", self.detail)):
                    with self.subTest(field=field, value=value, method=method):
                        payload = (self.payload(**{field: value}) if method == "post"
                                   else {"description": "Must not persist", field: value})
                        response = self.write(method, url, payload)
                        self.assertEqual(response.status_code, 400, response.content)
                        self.assertFalse(response.json()["ok"])
                        self.assertEqual(Product.objects.count(), 2)
                        self.product.refresh_from_db()
                        self.assertEqual(self.product.title, "Own product")
                        self.assertEqual(self.product.description, "Original")
                        self.assertEqual(self.product.price, Decimal("12.34"))

    def test_required_fields_and_empty_patch(self):
        for field in ("title", "price", "category"):
            payload = self.payload()
            del payload[field]
            self.assertEqual(self.write("post", "/api/v1/products", payload).status_code, 400)
        for payload in ({}, {"seller": self.other.pk}, {"is_deleted": False}):
            self.assertEqual(self.write("patch", self.detail, payload).status_code, 400)

    def test_price_bounds_and_numeric_json(self):
        for price in ("0.01", "9999999999.99", 12.34, 1):
            with self.subTest(price=price):
                response = self.write("patch", self.detail, {"price": price})
                self.assertEqual(response.status_code, 200, response.content)
                self.product.refresh_from_db()
                self.assertEqual(self.product.price, Decimal(str(price)))

    def test_maximum_title_length_and_duplicate_slug(self):
        for _ in range(2):
            response = self.write("post", "/api/v1/products", self.payload(title="a" * 255))
            self.assertEqual(response.status_code, 201, response.content)
            self.assertLessEqual(len(response.json()["product"]["slug"]), 255)

    def test_valid_patch_can_clear_optional_fields(self):
        response = self.write("patch", self.detail, {
            "description": "", "cover_url": None, "demo_url": "", "subcategory": None,
            "features": [], "tech_stack": [], "status": "paused", "title": " Renamed ",
        })
        self.assertEqual(response.status_code, 200, response.content)
        self.product.refresh_from_db()
        self.assertEqual(self.product.description, "")
        self.assertEqual(self.product.title, "Renamed")
        self.assertEqual(self.product.status, Product.Status.PAUSED)
        self.assertIsNone(self.product.demo_url)
        self.assertEqual(self.write("patch", self.detail, {"status": "active"}).status_code, 200)

    def test_moderation_cannot_be_bypassed(self):
        for status in (Product.Status.DRAFT, Product.Status.PENDING, Product.Status.REJECTED):
            Product.objects.filter(pk=self.product.pk).update(status=status)
            response = self.write("patch", self.detail, {"status": "ACTIVE", "title": "Changed"})
            self.assertEqual(response.status_code, 409)
            self.product.refresh_from_db()
            self.assertEqual(self.product.status, status)
            self.assertEqual(self.product.title, "Own product")
        self.assertEqual(self.write("patch", self.detail, {"status": "DRAFT"}).status_code, 400)

    def test_paid_order_blocks_deletion_even_with_zero_sales_counter(self):
        order = Order.objects.create(buyer=self.buyer, product=self.product, amount=100, status="PAID")
        self.assertEqual(self.product.sales_count, 0)
        self.assertEqual(self.client.delete(self.detail).status_code, 409)
        self.product.refresh_from_db()
        order.refresh_from_db()
        self.assertFalse(self.product.is_deleted)
        self.assertEqual(order.product_id, self.product.pk)

    def test_sales_counter_also_blocks_deletion(self):
        Product.objects.filter(pk=self.product.pk).update(sales_count=1)
        self.assertEqual(self.client.delete(self.detail).status_code, 409)

    def test_delete_archives_and_cannot_resurface(self):
        order = Order.objects.create(buyer=self.buyer, product=self.product, amount=100)
        self.assertEqual(self.client.delete(self.detail).status_code, 200)
        self.product.refresh_from_db()
        order.refresh_from_db()
        self.assertTrue(self.product.is_deleted)
        self.assertEqual(self.product.status, Product.Status.PAUSED)
        self.assertEqual(order.product_id, self.product.pk)
        for method in ("get", "patch", "delete"):
            response = self.write(method, self.detail, {"status": "ACTIVE", "is_deleted": False})
            self.assertEqual(response.status_code, 404)
        for query in ("", "?status=PAUSED"):
            self.assertEqual(self.client.get("/api/v1/products" + query).json()["count"], 0)
        stats = self.client.get("/api/v1/stats").json()
        self.assertEqual(stats["summary"]["products"], 0)
        self.assertEqual(stats["by_product"], [])

    def test_archived_product_revenue_remains_in_history(self):
        Order.objects.create(buyer=self.buyer, product=self.product, amount=123, status="PAID")
        Product.objects.filter(pk=self.product.pk).update(is_deleted=True)
        stats = self.client.get("/api/v1/stats").json()
        self.assertEqual(stats["summary"]["revenue_som"], 123)
        self.assertEqual(stats["summary"]["paid_orders"], 1)
        self.assertEqual(stats["by_product"], [])


class StoreFormValidationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(name="Saytlar", slug="sites")

    def form(self, files=None, **changes):
        data = {"title": "Website", "description": "Description", "price": "12.34",
                "category": self.category.pk, **changes}
        return ProductForm(data=data, files=files)

    def test_price_must_be_positive_finite_and_fit_database(self):
        for price in ("0", "-1", "NaN", "Infinity", "-Infinity", "0.001", "10000000000"):
            with self.subTest(price=price):
                form = self.form(price=price)
                self.assertFalse(form.is_valid())
                self.assertIn("price", form.errors)
        for price in ("0.01", "9999999999.99"):
            form = self.form(price=price)
            self.assertTrue(form.is_valid(), form.errors)

    def test_review_rating_is_one_to_five(self):
        for rating in ("-1", "0", "6", "32768", "1.5", "NaN"):
            form = ReviewForm(data={"rating": rating, "comment": "Review"})
            self.assertFalse(form.is_valid())
            self.assertIn("rating", form.errors)
        for rating in range(1, 6):
            form = ReviewForm(data={"rating": rating, "comment": "Review"})
            self.assertTrue(form.is_valid(), form.errors)

    def test_urls_accept_only_http_and_https(self):
        for field in ("screenshots_raw", "demo_url", "cover_image_url"):
            for url in ("javascript:alert(1)", "data:image/png;base64,abc", "ftp://example.com/a",
                        "https://", "not a URL"):
                with self.subTest(field=field, url=url):
                    form = self.form(**{field: url})
                    self.assertFalse(form.is_valid())
                    self.assertIn(field, form.errors)
        form = self.form(screenshots_raw=" https://example.com/a.png \n\nhttp://example.com/b.jpg",
                         demo_url="https://example.com", cover_image_url="http://example.com/c.png")
        self.assertTrue(form.is_valid(), form.errors)
        product = form.save(commit=False)
        self.assertEqual(product.screenshots, ["https://example.com/a.png", "http://example.com/b.jpg"])

    def test_one_bad_screenshot_invalidates_the_entire_list(self):
        for url in ("javascript:alert(1)", "//example.com/a"):
            form = self.form(screenshots_raw=f"https://example.com/a.png\n{url}")
            self.assertFalse(form.is_valid())
            self.assertIn("screenshots_raw", form.errors)

    def test_archive_extensions(self):
        for name in ("source.exe", "source.zip.exe", "source.tar", "source.gz", "source"):
            form = self.form(files={"file_archive": SimpleUploadedFile(name, b"content")})
            self.assertFalse(form.is_valid())
            self.assertIn("file_archive", form.errors)
        for name in ("source.zip", "source.TAR.GZ", "source.RAR"):
            form = self.form(files={"file_archive": SimpleUploadedFile(name, b"content")})
            self.assertTrue(form.is_valid(), form.errors)

    @override_settings(PRODUCT_ARCHIVE_MAX_SIZE=8)
    def test_archive_upload_size_boundary(self):
        for size in (8, 9):
            form = self.form(files={"file_archive": SimpleUploadedFile("source.zip", b"a" * size)})
            self.assertEqual(form.is_valid(), size == 8, form.errors)
            if size == 9:
                self.assertIn("file_archive", form.errors)

    def test_cover_image_upload_size_boundary(self):
        image = BytesIO()
        Image.new("RGB", (1, 1)).save(image, format="PNG")
        content = image.getvalue()
        for limit in (len(content), len(content) - 1):
            with self.settings(PRODUCT_IMAGE_MAX_SIZE=limit):
                form = self.form(files={"cover_image_file": SimpleUploadedFile(
                    "cover.png", content, content_type="image/png",
                )})
                self.assertEqual(form.is_valid(), limit == len(content), form.errors)
                if limit < len(content):
                    self.assertIn("cover_image_file", form.errors)

    def test_existing_archive_is_retained_without_reading_storage(self):
        instance = Product(title="Existing", category=self.category, price=1,
                           file_archive="products/archives/legacy.zip")
        # FileField boshlang'ich qiymati odatdagi tahrirlash formasida olinadi.
        data = {"title": "Existing", "category": self.category.pk, "price": 1,
                "description": "Description"}
        form = ProductForm(data=data, instance=instance)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["file_archive"].name, "products/archives/legacy.zip")
