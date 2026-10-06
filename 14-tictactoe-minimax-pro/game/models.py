from django.db import models

class Game(models.Model):
    MODE_CHOICES = [
        ('pve_easy', "Oson (Bot)"),
        ('pve_medium', "O'rtacha (Bot)"),
        ('pve_hard', "Yengilmas (Minimax Bot)"),
        ('pvp', "2 O'yinchi (Do'st bilan)"),
    ]

    board = models.CharField(max_length=9, default=' ' * 9)
    current_turn = models.CharField(max_length=1, default='X')
    winner = models.CharField(max_length=10, blank=True, null=True)  # 'X', 'O', 'DRAW', or None
    game_mode = models.CharField(max_length=20, choices=MODE_CHOICES, default='pve_hard')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Game #{self.id} [{self.game_mode}] - G'olib: {self.winner or 'Davom etmoqda'}"
