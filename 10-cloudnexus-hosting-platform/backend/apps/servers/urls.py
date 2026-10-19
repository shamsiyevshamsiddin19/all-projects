from django.urls import path

from . import views

app_name = "servers"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("new/", views.create, name="create"),
    path("check-slug/", views.check_slug, name="check_slug"),
    path("<slug:slug>/", views.detail, name="detail"),
    path("<slug:slug>/key/", views.key_ready, name="key_ready"),
    path("<slug:slug>/key/download/", views.key_download, name="key_download"),
    path("<slug:slug>/key/regenerate/", views.regenerate_key, name="regenerate_key"),
    path("<slug:slug>/delete/", views.delete, name="delete"),
]
