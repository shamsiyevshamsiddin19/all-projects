from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from apps.hotels.admin_views import booking_calendar_view, dashboard_view
from bot.webhook_views import telegram_webhook

urlpatterns = [
    path("admin/dashboard/", dashboard_view, name="admin-dashboard"),
    path("admin/bookings/calendar/", booking_calendar_view, name="admin-booking-calendar"),
    path("admin/", admin.site.urls),
    path("payments/", include("apps.payments.urls")),
    path("bot/webhook/", telegram_webhook, name="bot-webhook"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
