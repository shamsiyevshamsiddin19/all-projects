from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from store import views as store_views
from core import views as core_views
from core import oauth as core_oauth
from orders import views as orders_views

urlpatterns = [
    path("admin/", admin.site.urls),
    # Django'ning set_language view'i — navbar'dagi til almashtirgich
    # shu manzilga POST yuboradi va tilni cookie'ga yozadi.
    path("i18n/", include("django.conf.urls.i18n")),
    # Sotuvchi API'si (Bearer token bilan)
    path("api/v1/", include("core.api_urls")),
    
    # Kanonik Next.js manzillar (1:1 moslik)
    path("dashboard/", orders_views.dashboard_view, name="canonical_dashboard"),
    path("seller/", orders_views.seller_dashboard_view, name="canonical_seller"),
    path("seller/balance/", orders_views.seller_balance_view, name="canonical_seller_balance"),
    path("seller/new/", store_views.product_create_view, name="canonical_seller_new"),
    path("seller/<uuid:product_id>/edit/", store_views.product_edit_view, name="canonical_seller_edit_id"),
    path("seller/<slug:slug>/edit/", store_views.product_edit_view, name="canonical_seller_edit_slug"),
    path("loyiha-qoshish/", store_views.product_create_view, name="canonical_loyiha_qoshish"),
    path("login/", core_views.login_view, name="canonical_login"),
    path("register/", core_views.register_view, name="canonical_register"),
    path("wishlist/", store_views.wishlist_list_view, name="canonical_wishlist"),
    path("order/<uuid:order_id>/", orders_views.order_status_view, name="canonical_order_status"),
    path("api/download/<str:token>/", orders_views.download_file_view, name="canonical_api_download"),
    path("api/wishlist/<uuid:product_id>/", store_views.wishlist_toggle_view, name="canonical_api_wishlist"),
    path("api/click/prepare", orders_views.click_prepare_webhook),
    path("api/click/prepare/", orders_views.click_prepare_webhook),
    path("api/click/complete", orders_views.click_complete_webhook),
    path("api/click/complete/", orders_views.click_complete_webhook),
    path("api/auth/signin/google", core_oauth.google_login_view),
    path("api/auth/signin/google/", core_oauth.google_login_view),
    path("api/auth/callback/google", core_oauth.google_callback_view),
    path("api/auth/callback/google/", core_oauth.google_callback_view),
    path("google/", core_oauth.google_login_view),
    path("google-login/", core_oauth.google_login_view),

    path("", include("store.urls", namespace="store")),
    path("auth/", include("core.urls", namespace="core")),
    path("orders/", include("orders.urls", namespace="orders")),
]

if settings.DEBUG:
    # staticfiles ilovasi DEBUG rejimida /static/ ni o'zi beradi —
    # bu yerda faqat media kerak.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
