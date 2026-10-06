from django.urls import path
from . import views

app_name = "store"

urlpatterns = [
    path("", views.catalog_view, name="catalog"),
    path("product/<slug:slug>/", views.product_detail_view, name="product_detail"),
    path("product/<slug:slug>/edit/", views.product_edit_view, name="product_edit"),
    path("product/<slug:slug>/pause/", views.product_toggle_pause_view, name="product_toggle_pause"),
    path("product/<slug:slug>/delete/", views.product_delete_view, name="product_delete"),
    path("product/<slug:slug>/review/", views.add_review_view, name="add_review"),
    path("product/<slug:slug>/report/", views.report_product_view, name="report_product"),
    path("new-product/", views.product_create_view, name="product_create"),
    path("wishlist/", views.wishlist_list_view, name="wishlist"),
    path("wishlist/toggle/<uuid:product_id>/", views.wishlist_toggle_view, name="wishlist_toggle"),
]
