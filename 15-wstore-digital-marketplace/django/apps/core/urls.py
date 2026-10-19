from django.urls import path
from . import oauth, profile_views, views

app_name = "core"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),
    path("demo-login/", views.demo_login_view, name="demo_login"),
    # Google OAuth. Callback manzili Google konsolidagi
    # "Authorized redirect URI" bilan bir xil bo'lishi shart.
    path("google/", oauth.google_login_view, name="google_login"),
    path("google/callback", oauth.google_callback_view),
    path("google/callback/", oauth.google_callback_view, name="google_callback"),
    path("google/dev-mock/", oauth.google_dev_mock_view, name="google_dev_mock"),

    # Profil va sotuvchi bo'limi
    path("profile/", profile_views.profile_view, name="profile"),
    path("profile/seller/", profile_views.seller_onboarding_view, name="seller_onboarding"),
    path("profile/api/", profile_views.api_tokens_view, name="api_tokens"),
    path("profile/api/<int:token_id>/revoke/", profile_views.api_token_revoke_view, name="api_token_revoke"),
]
