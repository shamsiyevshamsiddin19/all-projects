from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    # Django'ning set_language view'i — navbar'dagi til almashtirgich
    # shu manzilga POST yuboradi va tilni cookie'ga yozadi.
    path("i18n/", include("django.conf.urls.i18n")),
    path("", include("store.urls", namespace="store")),
    path("auth/", include("core.urls", namespace="core")),
    path("orders/", include("orders.urls", namespace="orders")),
]

if settings.DEBUG:
    # staticfiles ilovasi DEBUG rejimida /static/ ni o'zi beradi —
    # bu yerda faqat media kerak.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
