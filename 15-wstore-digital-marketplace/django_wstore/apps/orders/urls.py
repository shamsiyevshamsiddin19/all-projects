from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path("checkout/<uuid:product_id>/", views.checkout_view, name="checkout"),
    path("listing-pay/<uuid:product_id>/", views.listing_pay_view, name="listing_pay"),
    path("<uuid:order_id>/", views.order_status_view, name="order_status"),
    path("poll/<uuid:order_id>/", views.order_status_poll_api, name="order_status_poll"),
    path("<uuid:order_id>/simulate-pay/", views.order_simulate_pay_view, name="order_simulate_pay"),
    path("download/<str:token>/", views.download_file_view, name="download_file"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("seller/", views.seller_dashboard_view, name="seller_dashboard"),
    path("seller/balance/", views.seller_balance_view, name="seller_balance"),
    # Click webhook endpoints
    path("api/payment/click/prepare/", views.click_prepare_webhook, name="click_prepare"),
    path("api/payment/click/complete/", views.click_complete_webhook, name="click_complete"),
]
