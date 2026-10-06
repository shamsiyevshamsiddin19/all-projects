import json
import random

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import ensure_csrf_cookie

from .models import Game

WINNING_COMBOS = [
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8),
    (0, 4, 8), (2, 4, 6)
]

def check_winner(board):
    for a, b, c in WINNING_COMBOS:
        if board[a] != ' ' and board[a] == board[b] == board[c]:
            return board[a], [a, b, c]
    if ' ' not in board:
        return 'DRAW', None
    return None, None

def minimax(board, depth, is_maximizing):
    winner, _ = check_winner(board)
    if winner == 'O':
        return 10 - depth
    elif winner == 'X':
        return depth - 10
    elif winner == 'DRAW':
        return 0

    if is_maximizing:
        best_score = -float('inf')
        for i in range(9):
            if board[i] == ' ':
                board[i] = 'O'
                score = minimax(board, depth + 1, False)
                board[i] = ' '
                best_score = max(score, best_score)
        return best_score
    else:
        best_score = float('inf')
        for i in range(9):
            if board[i] == ' ':
                board[i] = 'X'
                score = minimax(board, depth + 1, True)
                board[i] = ' '
                best_score = min(score, best_score)
        return best_score

def get_best_move(board, mode='pve_hard'):
    available = [i for i, val in enumerate(board) if val == ' ']
    if not available:
        return None
    
    if mode == 'pve_easy':
        return random.choice(available)
    
    if mode == 'pve_medium' and random.random() < 0.4:
        return random.choice(available)

    best_score = -float('inf')
    best_move = available[0]
    board_list = list(board)
    for i in available:
        board_list[i] = 'O'
        score = minimax(board_list, 0, False)
        board_list[i] = ' '
        if score > best_score:
            best_score = score
            best_move = i
    return best_move

@ensure_csrf_cookie
def index(request):
    return render(request, 'game/index.html')

def new_game(request):
    mode = request.GET.get('mode', 'pve_hard')
    if mode not in dict(Game.MODE_CHOICES):
        mode = 'pve_hard'
    game = Game.objects.create(game_mode=mode)
    return JsonResponse({
        'id': game.id,
        'board': list(game.board),
        'turn': game.current_turn,
        'winner': None,
        'mode': game.game_mode,
        'winning_line': None
    })

def make_move(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method talab qilinadi'}, status=405)
    
    try:
        data = json.loads(request.body)
        game_id = data.get('game_id')
        index = int(data.get('index'))
    except (json.JSONDecodeError, KeyError, ValueError, TypeError):
        return JsonResponse({'error': 'Noto\'g\'ri so\'rov parametrlari'}, status=400)

    game = get_object_or_404(Game, id=game_id)
    if game.winner:
        return JsonResponse({'error': 'O\'yin allaqachon yakunlangan'}, status=400)

    board = list(game.board)
    if index < 0 or index > 8 or board[index] != ' ':
        return JsonResponse({'error': 'Noto\'g\'ri katak'}, status=400)

    # Foydalanuvchi yurishi
    player = game.current_turn
    board[index] = player
    winner, win_line = check_winner(board)

    bot_move_index = None

    if not winner:
        if game.game_mode == 'pvp':
            game.current_turn = 'O' if player == 'X' else 'X'
        else:
            # Bot yurishi (O)
            bot_move_index = get_best_move(board, game.game_mode)
            if bot_move_index is not None:
                board[bot_move_index] = 'O'
                winner, win_line = check_winner(board)
            game.current_turn = 'X'
    
    game.board = "".join(board)
    if winner:
        game.winner = winner
    game.save()

    return JsonResponse({
        'id': game.id,
        'board': board,
        'turn': game.current_turn,
        'winner': game.winner,
        'winning_line': win_line,
        'bot_move': bot_move_index
    })

def game_stats(request):
    total = Game.objects.count()
    x_wins = Game.objects.filter(winner='X').count()
    o_wins = Game.objects.filter(winner='O').count()
    draws = Game.objects.filter(winner='DRAW').count()
    return JsonResponse({
        'total': total,
        'x_wins': x_wins,
        'o_wins': o_wins,
        'draws': draws
    })
