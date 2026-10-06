from django.urls import path
from . import views


urlpatterns = [
    path('', views.hisobla, name='hisobla')
]
