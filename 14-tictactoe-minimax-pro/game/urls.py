from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/new/', views.new_game, name='new_game'),
    path('api/move/', views.make_move, name='make_move'),
    path('api/stats/', views.game_stats, name='game_stats'),
]
