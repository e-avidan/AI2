import abstract
import random
from utils import MiniMaxAlgorithm, INFINITY, provide_while
from players.better_player import Player as BetterPlayer
import time

class Player(BetterPlayer):
    def __init__(self, setup_time, player_color, time_per_k_turns, k):
        BetterPlayer.__init__(self, setup_time, player_color, time_per_k_turns, k)

    def get_move(self, game_state, possible_moves):
        self.clock = time.time()
        self.time_for_current_move = self.time_remaining_in_round / self.turns_remaining_in_round - 0.05

        alg = MiniMaxAlgorithm(self.utility, self.color, self.no_more_time, False)
        runs = (alg.search(game_state, d, True) for d in range(1, int(INFINITY)))
        runs = provide_while(runs, self.no_more_time)

        # Get final run, unless no time for move and then just any move
        res = (list(runs) or [(None, possible_moves[random.choice(range(len(possible_moves)))])])[-1]

        if self.turns_remaining_in_round == 1:
            self.turns_remaining_in_round = self.k
            self.time_remaining_in_round = self.time_per_k_turns
        else:
            self.turns_remaining_in_round -= 1
            self.time_remaining_in_round -= (time.time() - self.clock)

        return res[1]

    def __repr__(self):
        return '{} {}'.format(abstract.AbstractPlayer.__repr__(self), 'min_max')

# c:\python35\python run_game.py 3 3 3 y random_player random_player
