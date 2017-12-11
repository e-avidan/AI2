import abstract        
from utils import MiniMaxWithAlphaBetaPruning
from players.min_max_player import Player as MinMaxPlayer

class Player(MinMaxPlayer):
    def __init__(self, setup_time, player_color, time_per_k_turns, k, alg = None):
        MinMaxPlayer.__init__(self, setup_time, player_color, time_per_k_turns, k, MiniMaxWithAlphaBetaPruning)

    def __repr__(self):
        return '{} {}'.format(abstract.AbstractPlayer.__repr__(self), 'alpha_beta')

# c:\python35\python run_game.py 3 3 3 y random_player random_player
