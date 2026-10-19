"""REST API v1 manzillari — config/urls.py dan `api/v1/` prefiksi bilan ulanadi."""
from django.urls import path

from . import api

app_name = "api_v1"

urlpatterns = [
    path("me", api.me_view, name="me"),
    path("categories", api.categories_view, name="categories"),
    path("products", api.products_view, name="products"),
    path("products/<uuid:product_id>", api.product_detail_view, name="product_detail"),
    path("stats", api.stats_view, name="stats"),
]
