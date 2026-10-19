import subprocess
import tempfile
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .models import Server, SshKey
from .services import fingerprint_for, generate_keypair
from .validators import validate_slug

User = get_user_model()


class SlugValidatorTests(TestCase):
    def test_accepts_normal_names(self):
        for ok in ("aisayt", "my-app", "a1b2", "x" * 63):
            validate_slug(ok)

    def test_rejects_reserved(self):
        for bad in ("www", "api", "admin", "mail", "whost"):
            with self.assertRaises(ValidationError, msg=bad):
                validate_slug(bad)

    def test_rejects_bad_format(self):
        for bad in ("ab", "-lead", "trail-", "UPPER", "has space", "a--b",
                    "under_score", "x" * 64, "xn--abc", ""):
            with self.assertRaises(ValidationError, msg=bad):
                validate_slug(bad)


class KeyGenerationTests(TestCase):
    def test_generates_valid_openssh_pair(self):
        key = generate_keypair("test@example.com (demo.whost.uz)")
        self.assertIn("BEGIN OPENSSH PRIVATE KEY", key.private_key)
        self.assertTrue(key.public_key.startswith("ssh-ed25519 "))
        self.assertTrue(key.fingerprint.startswith("SHA256:"))

    def test_fingerprint_matches_ssh_keygen(self):
        """Our fingerprint must equal what ssh-keygen reports."""
        key = generate_keypair("fp-check")
        with tempfile.TemporaryDirectory() as tmp:
            pub = Path(tmp) / "id.pub"
            pub.write_text(key.public_key + "\n")
            out = subprocess.run(
                ["ssh-keygen", "-lf", str(pub)],
                capture_output=True, text=True, check=True,
            ).stdout
        self.assertIn(key.fingerprint, out)

    def test_private_key_is_usable_by_ssh_keygen(self):
        key = generate_keypair("usable")
        with tempfile.TemporaryDirectory() as tmp:
            priv = Path(tmp) / "id_ed25519"
            priv.write_text(key.private_key)
            priv.chmod(0o600)
            out = subprocess.run(
                ["ssh-keygen", "-y", "-f", str(priv)],
                capture_output=True, text=True, check=True,
            ).stdout.strip()
        self.assertEqual(out.split()[1], key.public_key.split()[1])

    def test_keys_are_unique(self):
        a = generate_keypair("a")
        b = generate_keypair("b")
        self.assertNotEqual(a.fingerprint, b.fingerprint)

    def test_fingerprint_rejects_garbage(self):
        with self.assertRaises(ValueError):
            fingerprint_for("not-a-key")


class ServerFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("user@example.com", "pw-long-enough-1")
        self.other = User.objects.create_user("other@example.com", "pw-long-enough-2")
        self.client.force_login(self.user)

    def _create(self, name="Mening AI saytim", slug="aisayt"):
        return self.client.post(reverse("servers:create"), {"name": name, "slug": slug})

    def test_create_allocates_subdomain_and_key(self):
        resp = self._create()
        server = Server.objects.get(slug="aisayt")
        self.assertRedirects(resp, reverse("servers:key_ready", args=["aisayt"]))
        self.assertEqual(server.domain, "aisayt.whost.uz")
        self.assertEqual(server.owner, self.user)
        self.assertIsNotNone(server.active_key)

    def test_private_key_is_never_stored(self):
        self._create()
        key = SshKey.objects.get()
        for field in (key.public_key, key.fingerprint):
            self.assertNotIn("PRIVATE KEY", field)
        stored = " ".join(str(v) for v in SshKey.objects.values_list(flat=False)[0])
        self.assertNotIn("PRIVATE KEY", stored)

    def test_key_download_works_once(self):
        self._create()
        url = reverse("servers:key_download", args=["aisayt"])

        first = self.client.get(url)
        self.assertEqual(first.status_code, 200)
        self.assertIn("BEGIN OPENSSH PRIVATE KEY", first.content.decode())
        self.assertIn("aisayt_ed25519", first["Content-Disposition"])

        second = self.client.get(url)
        self.assertEqual(second.status_code, 302)  # gone — redirected

    def test_slug_must_be_unique(self):
        self._create()
        self.client.force_login(self.other)
        resp = self._create(name="Boshqa", slug="aisayt")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "band")
        self.assertEqual(Server.objects.filter(slug="aisayt").count(), 1)

    def test_reserved_slug_blocked_through_form(self):
        resp = self._create(slug="admin")
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Server.objects.filter(slug="admin").exists())

    def test_cannot_see_other_users_server(self):
        self._create()
        self.client.force_login(self.other)
        resp = self.client.get(reverse("servers:detail", args=["aisayt"]))
        self.assertEqual(resp.status_code, 404)

    def test_regenerate_revokes_old_key(self):
        self._create()
        old = SshKey.objects.get()
        self.client.post(reverse("servers:regenerate_key", args=["aisayt"]))
        old.refresh_from_db()
        self.assertTrue(old.is_revoked)
        self.assertEqual(SshKey.objects.filter(is_revoked=False).count(), 1)

    def test_delete_requires_matching_confirmation(self):
        self._create()
        detail = reverse("servers:delete", args=["aisayt"])

        self.client.post(detail, {"confirm": "wrong"})
        self.assertTrue(Server.objects.alive().filter(slug="aisayt").exists())

        self.client.post(detail, {"confirm": "aisayt"})
        self.assertFalse(Server.objects.alive().filter(slug="aisayt").exists())

    def test_server_limit_enforced(self):
        self.user.server_limit = 1
        self.user.save()
        self._create(slug="first")
        self._create(slug="second")
        self.assertEqual(Server.objects.alive().filter(owner=self.user).count(), 1)

    def test_check_slug_endpoint(self):
        url = reverse("servers:check_slug")
        self.assertTrue(self.client.get(url, {"slug": "freename"}).json()["ok"])
        self.assertFalse(self.client.get(url, {"slug": "admin"}).json()["ok"])
        self.assertEqual(
            self.client.get(url, {"name": "Mening AI Saytim"}).json()["slug"],
            "mening-ai-saytim",
        )

    def test_dashboard_requires_login(self):
        self.client.logout()
        resp = self.client.get(reverse("servers:dashboard"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/accounts/login/", resp["Location"])


class ApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("api@example.com", "pw-long-enough-3")
        self.client.force_login(self.user)

    def test_create_returns_private_key_once(self):
        resp = self.client.post(
            "/api/v1/servers/",
            {"name": "API server", "slug": "apisrv"},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertIn("BEGIN OPENSSH PRIVATE KEY", data["private_key"])
        self.assertEqual(data["domain"], "apisrv.whost.uz")
        self.assertEqual(data["ssh_remote"], "git@git.whost.uz:apisrv.git")

        detail = self.client.get("/api/v1/servers/apisrv/").json()
        self.assertNotIn("private_key", detail)

    def test_api_rejects_reserved_slug(self):
        resp = self.client.post(
            "/api/v1/servers/",
            {"name": "x", "slug": "api"},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_me_endpoint(self):
        data = self.client.get("/api/v1/me/").json()
        self.assertEqual(data["email"], "api@example.com")
        self.assertEqual(data["platform_domain"], "whost.uz")

    def test_api_requires_auth(self):
        self.client.logout()
        self.assertEqual(self.client.get("/api/v1/servers/").status_code, 401)

    def test_health_is_public(self):
        self.client.logout()
        self.assertEqual(self.client.get("/api/v1/health/").status_code, 200)


class AuthPageTests(TestCase):
    """These catch allauth/custom-user wiring breaks that force_login hides."""

    def test_login_page_renders(self):
        resp = self.client.get(reverse("account_login"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Hisobingizga kiring")

    def test_signup_page_renders(self):
        self.assertEqual(self.client.get(reverse("account_signup")).status_code, 200)

    def test_email_login_works(self):
        User.objects.create_user("login@example.com", "pw-long-enough-9")
        resp = self.client.post(
            reverse("account_login"),
            {"login": "login@example.com", "password": "pw-long-enough-9"},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(int(self.client.session["_auth_user_id"]),
                         User.objects.get(email="login@example.com").pk)
