import json
from django.test import TestCase, Client
from django.urls import reverse
from .models import Game
from .views import check_winner, get_best_move

class TicTacToeTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_index_page_loads(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'TIC')

    def test_new_game_creation(self):
        response = self.client.get(reverse('new_game'), {'mode': 'pve_hard'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('id', data)
        self.assertEqual(data['mode'], 'pve_hard')
        self.assertEqual(data['turn'], 'X')

    def test_pvp_moves(self):
        game = Game.objects.create(game_mode='pvp')
        # X plays index 0
        res = self.client.post(
            reverse('make_move'),
            data=json.dumps({'game_id': game.id, 'index': 0}),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data['board'][0], 'X')
        self.assertEqual(data['turn'], 'O')

    def test_win_detection(self):
        # Row win
        winner, line = check_winner(['X', 'X', 'X', ' ', ' ', ' ', ' ', ' ', ' '])
        self.assertEqual(winner, 'X')
        self.assertEqual(line, [0, 1, 2])

        # Draw
        draw_board = ['X', 'O', 'X', 'X', 'O', 'O', 'O', 'X', 'X']
        winner, line = check_winner(draw_board)
        self.assertEqual(winner, 'DRAW')
        self.assertIsNone(line)

    def test_minimax_prevents_immediate_loss(self):
        # X is about to win at index 2 (has 0 and 1)
        # O should block at 2
        board = ['X', 'X', ' ', ' ', 'O', ' ', ' ', ' ', ' ']
        move = get_best_move(board, mode='pve_hard')
        self.assertEqual(move, 2)
