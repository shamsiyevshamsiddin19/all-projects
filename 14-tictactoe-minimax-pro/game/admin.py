from django.contrib import admin
from .models import Game

@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('id', 'game_mode', 'current_turn', 'winner', 'created_at')
    list_filter = ('game_mode', 'winner', 'created_at')
    search_fields = ('id',)
