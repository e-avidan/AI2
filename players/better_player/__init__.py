# ===============================================================================
# Imports
# ===============================================================================

import abstract
from utils import INFINITY, run_with_limited_time, ExceededTimeError, _expand_state,ExtractMostPopularOpenningMoves
from Reversi.consts import EM, OPPONENT_COLOR, BOARD_COLS, BOARD_ROWS, TIE
import time
import copy
import numpy as np
from Reversi.board import GameState

# ===============================================================================
# Player
# ===============================================================================

POSITIONS = [
    [4, -3, 2, 2, 2, 2, -3, 4],
    [-3, -4, -1, -1, -1, -1, -4, -3],
    [2, -1, 1, 0, 0, 1, -1, 2],
    [2, -1, 0, 1, 1, 0, -1, 2],
    [2, -1, 0, 1, 1, 0, -1, 2],
    [2, -1, 1, 0, 0, 1, -1, 2],
    [-3, -4, -1, -1, -1, -1, -4, -3],
    [4, -3, 2, 2, 2, 2, -3, 4]
]

TOTAL_POSITION_SCORE = float(sum(sum(abs(v) for v in row) for row in POSITIONS))
MAX_POSITION_SCORE = float(max(max(v for v in row) for row in POSITIONS))

X = [-1, -1, 0, 1, 1, 1, 0, -1]
Y = [0, 1, 1, 1, 0, -1, -1, -1]

class Player(abstract.AbstractPlayer):
    def __init__(self, setup_time, player_color, time_per_k_turns, k):
        abstract.AbstractPlayer.__init__(self, setup_time, player_color, time_per_k_turns, k)
        self.clock = time.time()

        # We are simply providing (remaining time / remaining turns) for each turn in round.
        # Taking a spare time of 0.05 seconds.
        self.turns_remaining_in_round = self.k
        self.time_remaining_in_round = self.time_per_k_turns
        self.time_for_current_move = self.time_remaining_in_round / self.turns_remaining_in_round - 0.05
        self._last_game_state = ''
        self._last_game_board = GameState().board
        self.opening_dict = ExtractMostPopularOpenningMoves(70)
        self.opponent_sign = '-' if self.color == 'X' else '+'

    def get_move(self, game_state, possible_moves):
        self.clock = time.time()
        self.time_for_current_move = self.time_remaining_in_round / self.turns_remaining_in_round - 0.05

        open_move = None if self._last_game_state == None else self._opening_move(game_state.board)

        if  open_move!= None:
            return open_move
        else:
            self._last_game_state = None

        if len(possible_moves) == 1:
            return possible_moves[0]

        best_move = possible_moves[0]
        next_state = copy.deepcopy(game_state)
        next_state.perform_move(best_move[0], best_move[1])
        # Choosing an arbitrary move
        # Get the best move according the utility function
        for move in possible_moves:
            new_state = copy.deepcopy(game_state)
            new_state.perform_move(move[0], move[1])
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

    def utility(self, state, is_expanded=False):
        op_color = OPPONENT_COLOR[self.color]

        # Exhaust no-brainer states
        ran_once = 0
        while not ran_once or len(moves) <= 1:
            ran_once = True
            moves = state.get_possible_moves()

            reverse_state = copy.deepcopy(state)
            reverse_state.curr_player = op_color
            reverse_moves = reverse_state.get_possible_moves()

            my_moves = len(moves)
            op_moves = len(reverse_moves)

            my_units = sum(sum(c == self.color for c in row) for row in state.board)
            op_units = sum(sum(c == op_color for c in row) for row in state.board)

            if my_units == 0:
                return -INFINITY
            if op_units == 0:
                return INFINITY
            if my_moves == 0 or op_moves == 0:
                return 0 if my_units == op_units else (-INFINITY if my_units < op_units else +INFINITY)

            if len(moves) != 1:
                break

            # Go to next state
            state = copy.deepcopy(state)
            state.perform_move(moves[0][0], moves[0][1])

        player_mod = -1 if state.curr_player != self.color else +1

        units = my_units + op_units

        # Coin Parity
        p = 100*(my_units - op_units)/ float(units)

        # Mobility
        m = 0 if my_moves + op_moves == 0 else 100*(my_moves - op_moves)/float(my_moves + op_moves)

        # Stability
        my_stab = self._get_stability_value(state, self.color)
        op_stab =self._get_stability_value(state, op_color)
        s = 0 if (my_stab + op_stab) == 0 else 50*(my_stab - op_stab)/float(my_stab + op_stab)

        # Corner Occupancy
        my_corners = self._get_corner_occupancy(state, self.color)
        op_corners = self._get_corner_occupancy(state, op_color)
        c = 25 * (my_corners - op_corners)

        # Corner Closeness
        my_cornerclose=self._get_corner_close(state, self.color)
        op_cornerclose=self._get_corner_close(state, op_color)
        l = 0 if (my_cornerclose+op_cornerclose) == 0 else 100*(my_cornerclose-op_cornerclose)/float(my_cornerclose+op_cornerclose)

        vec = (p, c, l, m, s)

        if units < 16:
            w = (0, 15, 5, 30, 50)
        elif units < 32:
            w = (5, 15, 10, 20, 40)
        elif units < 48:
            w = (15, 40, 15, 10, 20)
        else:
            w = (40, 30, 5, 5, 20)

        h = sum((vec[i] * w[i] for i in range(0, len(vec))))

        return player_mod * h

    def _get_stability_value(self, state, target_color):
        return sum(sum(POSITIONS[r][c] if color == target_color else 0 for c, color in enumerate(row)) for r, row in
                   enumerate(state.board))

    def _get_corner_occupancy(self, state, color):
        board = state.board

        return float((board[0][0] == color) +
                     (board[BOARD_ROWS - 1][0] == color) +
                     (board[0][BOARD_COLS - 1] == color) +
                     (board[BOARD_ROWS - 1][BOARD_COLS - 1] == color))

    def _get_corner_close(self, state, color):
        board = state.board

        return (self._get_specific_corner_control_score(board, color, 0, 0) +
                self._get_specific_corner_control_score(board, color, BOARD_ROWS - 1, 0) +
                self._get_specific_corner_control_score(board, color, 0, BOARD_COLS - 1) +
                self._get_specific_corner_control_score(board, color, BOARD_ROWS - 1, BOARD_COLS - 1))

    def _get_specific_corner_control_score(self, board, color, x, y):
        if not board[x][y] == EM:
            return 0

        dx = +1 if x == 0 else -1
        dy = +1 if y == 0 else -1

        return sum(c == color for c in [board[x + dx][y], board[x][y + dy], board[x + dx][y + dy]])

    def selective_deepening_criterion(self, state):
        # Better player does not selectively deepen into certain nodes.
        return False

    def no_more_time(self):
        return (time.time() - self.clock) >= self.time_for_current_move

    def __repr__(self):
        return '{} {}'.format(abstract.AbstractPlayer.__repr__(self), 'better')

    def _opening_move(self, board):
        self._updateNewOpponentMove(board)

        nextMove = self.opening_dict.get(self._last_game_state)
        if nextMove == None: return None

        self._last_game_state += nextMove
        coord = [ord(nextMove[1]) -97, int(nextMove[2]) - 1]
        self._last_game_board[coord[0]][coord[1]] = self.color
        return coord

    def _updateNewOpponentMove(self, board):

        for x in range(8):
            for y in range(8):
                    if self._last_game_board[x][y] == ' ' and board[x][y] != ' ':
                        self._last_game_state += self.opponent_sign + chr(x + 97) + str(y + 1)
                        self._last_game_board = board
                        return True;

# c:\python35\python.exe run_game.py 3 3 3 y better_player random_player

