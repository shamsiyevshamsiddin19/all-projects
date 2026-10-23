from unittest.mock import Mock, patch
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse


@override_settings(GOOGLE_OAUTH_CLIENT_ID="test", GOOGLE_OAUTH_CLIENT_SECRET="test", DEMO_MODE=False)
class AuthRegressionTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("disabled", email="disabled@example.com", google_id="sub-123", is_active=False)

    @patch("core.oauth.requests.get")
    @patch("core.oauth.requests.post")
    def test_disabled_google_account_cannot_login(self, post, get):
        post.return_value = Mock(json=lambda: {"access_token": "test"})
        get.return_value = Mock(json=lambda: {"sub": "sub-123", "email": self.user.email, "email_verified": True})
        session = self.client.session
        session["google_oauth_state"] = "test-state"
        session.save()
        response = self.client.get(reverse("core:google_callback"), {"code": "test", "state": "test-state"})
        self.assertEqual(response.status_code, 302)
        self.assertNotIn("_auth_user_id", self.client.session)

    @patch("core.oauth.requests.post")
    def test_invalid_oauth_state_does_not_exchange_code(self, post):
        self.client.get(reverse("core:google_callback"), {"code": "test", "state": "untrusted"})
        post.assert_not_called()

    def test_logout_requires_post(self):
        self.assertEqual(self.client.get(reverse("core:logout")).status_code, 405)
        self.assertEqual(self.client.post(reverse("core:logout")).status_code, 302)
