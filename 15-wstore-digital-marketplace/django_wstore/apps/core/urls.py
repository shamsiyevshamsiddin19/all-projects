from django.urls import path
from . import oauth, views

app_name = "core"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),
    path("demo-login/", views.demo_login_view, name="demo_login"),
    # Google OAuth. Callback manzili Google konsolidagi
    # "Authorized redirect URI" bilan bir xil bo'lishi shart.
    path("google/", oauth.google_login_view, name="google_login"),
    path("google/callback/", oauth.google_callback_view, name="google_callback"),
]
