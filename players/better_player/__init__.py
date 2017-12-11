
#===============================================================================
# Imports
#===============================================================================

import abstract
from utils import INFINITY, run_with_limited_time, ExceededTimeError
from Reversi.consts import EM, OPPONENT_COLOR, BOARD_COLS, BOARD_ROWS, TIE
import time
import copy
from collections import defaultdict

#===============================================================================
# Player
#===============================================================================

class Player(abstract.AbstractPlayer):
    def __init__(self, setup_time, player_color, time_per_k_turns, k):
        abstract.AbstractPlayer.__init__(self, setup_time, player_color, time_per_k_turns, k)
        self.clock = time.time()

        # We are simply providing (remaining time / remaining turns) for each turn in round.
        # Taking a spare time of 0.05 seconds.
        self.turns_remaining_in_round = self.k
        self.time_remaining_in_round = self.time_per_k_turns
        self.time_for_current_move = self.time_remaining_in_round / self.turns_remaining_in_round - 0.05

    def get_move(self, game_state, possible_moves):
        self.clock = time.time()
        self.time_for_current_move = self.time_remaining_in_round / self.turns_remaining_in_round - 0.05
        if len(possible_moves) == 1:
            return possible_moves[0]

        best_move = possible_moves[0]
        next_state = copy.deepcopy(game_state)
        next_state.perform_move(best_move[0],best_move[1])
        # Choosing an arbitrary move
        # Get the best move according the utility function
        for move in possible_moves:
            new_state = copy.deepcopy(game_state)
            new_state.perform_move(move[0],move[1])
            if self.utility(new_state) > self.utility(next_state):
                next_state = new_state
                best_move = move

        if self.turns_remaining_in_round == 1:
            self.turns_remaining_in_round = self.k
            self.time_remaining_in_round = self.time_per_k_turns
        else:
            self.turns_remaining_in_round -= 1
            self.time_remaining_in_round -= (time.time() - self.clock)

        return best_move

    def utility(self, state):
        moves = len(state.get_possible_moves())
        if moves == 0:
            winner = state.get_winner()
            res = 0 if winner == TIE else (+1 if winner == state.curr_player else -1)
            return res * INFINITY

        opposite_state = copy.deepcopy(state)
        opposite_state.curr_player = OPPONENT_COLOR[state.curr_player]
        opposite_moves = len(opposite_state.get_possible_moves())

        op_color = OPPONENT_COLOR[self.color]
        my_moves = opposite_moves if state.curr_player != self.color else moves
        op_moves = moves if state.curr_player != self.color else opposite_moves

        my_units = sum(sum(c == self.color for c in row) for row in state.board)
        op_units = sum(sum(c == op_color for c in row) for row in state.board)

        if my_units == 0:
            return -INFINITY
        if op_units == 0:
            return INFINITY

        # Coin Parity
        p = 0 if my_units == op_units else (-1.0 if my_units < op_units else +1.0) * (my_units)/(my_units + op_units)

        # Corner Control
        c = 25 * (self._get_corner_occupancy(state, self.color) - self._get_corner_occupancy(state, op_color))

        # Corner Closeness
        l = -0.25 * (self._get_corner_close(state, self.color) - self._get_corner_close(state, op_color));
        # Mobility
        m = 0 if my_moves == op_moves else (-1.0 if my_moves < op_moves else +1.0) * my_moves/(my_moves + op_moves)

        return (10 * p) + c + l + 2 * m # + (74.396 * f) + (10 * d)
    
    def _get_corner_occupancy(self, state, color):
        board = state.board

        return ((board[0][0] == color) +
               (board[BOARD_ROWS-1][0] == color) +
               (board[0][BOARD_COLS-1] == color) +
               (board[BOARD_ROWS-1][BOARD_COLS-1] == color))

    def _get_corner_close(self, state, color):
        board = state.board

        return (self._get_specific_corner_control_score(board, color, 0, 0) +
               self._get_specific_corner_control_score(board, color, BOARD_ROWS-1, 0) +
               self._get_specific_corner_control_score(board, color, 0, BOARD_COLS-1) +
               self._get_specific_corner_control_score(board, color, BOARD_ROWS-1, BOARD_COLS-1))

    def _get_specific_corner_control_score(self, board, color, x, y):
        if not board[x][y] == EM:
            return 0

        dx = +1 if x == 0 else -1
        dy = +1 if y == 0 else -1

        return sum(c == color for c in [board[x+dx][y], board[x][y+dy], board[x+dx][y+dy]])

    def selective_deepening_criterion(self, state):
        # Better player does not selectively deepen into certain nodes.
        return False

    def no_more_time(self):
        return (time.time() - self.clock) >= self.time_for_current_move

    def __repr__(self):
        return '{} {}'.format(abstract.AbstractPlayer.__repr__(self), 'better')

# c:\python35\python.exe run_game.py 3 3 3 y better_player random_player
