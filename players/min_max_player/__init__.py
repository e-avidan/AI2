import abstract
import random
from utils import MiniMaxAlgorithm, INFINITY, provide_while
from players.better_player import Player as ParentPlayer
import time

class Player(ParentPlayer):
    def __init__(self, setup_time, player_color, time_per_k_turns, k, alg = None):
        ParentPlayer.__init__(self, setup_time, player_color, time_per_k_turns, k)

        self._alg = alg or MiniMaxAlgorithm

    def get_move(self, game_state, possible_moves):
        if len(possible_moves) == 1:
            return possible_moves[0]

        self.clock = time.time()
        self.time_for_current_move = self.time_remaining_in_round / self.turns_remaining_in_round - 0.05

        alg = self._alg(self.utility, self.color, self.no_more_time, None)
        runs = (alg.search(game_state, d) for d in range(1, int(INFINITY)))
        runs = provide_while(runs, self.no_more_time)

        # Get final run, unless no time for move and then just any move
        res = list(runs)
        print (self, len(res))
        res = (res or [(None, None)])[-1][1]
        res = res or possible_moves[random.choice(range(len(possible_moves)))]

        if self.turns_remaining_in_round == 1:
            self.turns_remaining_in_round = self.k
            self.time_remaining_in_round = self.time_per_k_turns
        else:
            self.turns_remaining_in_round -= 1
            self.time_remaining_in_round -= (time.time() - self.clock)

        return res

    def __repr__(self):
        return '{} {}'.format(abstract.AbstractPlayer.__repr__(self), 'min_max')

# c:\python35\python run_game.py 3 3 3 y random_player random_player
