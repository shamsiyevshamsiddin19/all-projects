from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.servers import api, views

router = DefaultRouter()
router.register("servers", api.ServerViewSet, basename="server")

urlpatterns = [
    path("", views.landing, name="landing"),
    path("dashboard/", include("apps.servers.urls")),
    path("accounts/", include("allauth.urls")),
    path("admin/", admin.site.urls),
    path("api/v1/", include(router.urls)),
    path("api/v1/me/", api.me, name="api-me"),
    path("api/v1/health/", api.health, name="api-health"),
]
