"""Generic utility functions
"""
# from __future__ import print_function
from threading import Thread
from multiprocessing import Queue
import time
import copy
import operator

INFINITY = float(6000)


class ExceededTimeError(RuntimeError):
    """Thrown when the given function exceeded its runtime.
    """
    pass


def function_wrapper(func, args, kwargs, result_queue):
    """Runs the given function and measures its runtime.

    :param func: The function to run.
    :param args: The function arguments as tuple.
    :param kwargs: The function kwargs as dict.
    :param result_queue: The inter-process queue to communicate with the parent.
    :return: A tuple: The function return value, and its runtime.
    """
    start = time.time()
    try:
        result = func(*args, **kwargs)
    except MemoryError as e:
        result_queue.put(e)
        return

    runtime = time.time() - start
    result_queue.put((result, runtime))


def run_with_limited_time(func, args, kwargs, time_limit):
    """Runs a function with time limit

    :param func: The function to run.
    :param args: The functions args, given as tuple.
    :param kwargs: The functions keywords, given as dict.
    :param time_limit: The time limit in seconds (can be float).
    :return: A tuple: The function's return value unchanged, and the running time for the function.
    :raises PlayerExceededTimeError: If player exceeded its given time.
    """
    q = Queue()
    t = Thread(target=function_wrapper, args=(func, args, kwargs, q))
    t.start()

    # This is just for limiting the runtime of the other thread, so we stop eventually.
    # It doesn't really measure the runtime.
    t.join(time_limit)

    if t.is_alive():
        raise ExceededTimeError

    q_get = q.get()
    if isinstance(q_get, MemoryError):
        raise q_get
    return q_get


class MiniMaxAlgorithm:

    def __init__(self, utility, my_color, no_more_time, selective_deepening):
        """Initialize a MiniMax algorithms without alpha-beta pruning.

        :param utility: The utility function. Should have state as parameter.
        :param my_color: The color of the player who runs this MiniMax search.
        :param no_more_time: A function that returns true if there is no more time to run this search, or false if
                             there is still time left.
        :param selective_deepening: A functions that gets the current state, and
                        returns True when the algorithm should continue the search
                        for the minimax value recursivly from this state.
                        optional
        """
        self.utility = utility
        self.my_color = my_color
        self.no_more_time = no_more_time
        self.selective_deepening = selective_deepening

    def search(self, state, depth, maximizing_player = True):
        """Start the MiniMax algorithm.

        :param state: The state to start from.
        :param depth: The maximum allowed depth for the algorithm.
        :param maximizing_player: Whether this is a max node (True) or a min node (False).
        :return: A tuple: (The min max algorithm value, The move in case of max node or None in min mode)
        """
        depth_exceeded = depth <= 0 and not (self.selective_deepening and self.selective_deepening(state));
        if depth_exceeded:
            return (self.utility(state), None)

        moves = state.get_possible_moves()
        if len(moves) == 0: # todo TIES
            winner = state.get_winner()

            res = 0 if winner == 'tie' else (+1 if winner == self.my_color else -1)
            return (res * INFINITY, None)
            
        my_turn = maximizing_player # state.curr_player == self.my_color
        f = max if my_turn else min
        
        child_res = ((self.search(_expand_state(state, m), depth-1, not maximizing_player)[0], m) for m in moves)
        child_res = provide_while(child_res, self.no_more_time)

        val = f(child_res, key=lambda t: t[0], default=(-INFINITY if my_turn else INFINITY, None))
        return val if my_turn else (val[0], None)

def _expand_state(state, move):
    state = copy.deepcopy(state)
    state.perform_move(move[0], move[1])
    return state

ALPHA = 'alpha'
BETA = 'beta'

class MiniMaxWithAlphaBetaPruning:

    def __init__(self, utility, my_color, no_more_time, selective_deepening):
        """Initialize a MiniMax algorithms with alpha-beta pruning.

        :param utility: The utility function. Should have state as parameter.
        :param my_color: The color of the player who runs this MiniMax search.
        :param no_more_time: A function that returns true if there is no more time to run this search, or false if
                             there is still time left.
        :param selective_deepening: A functions that gets the current state, and
                        returns True when the algorithm should continue the search
                        for the minimax value recursivly from this state.
        """
        self.utility = utility
        self.my_color = my_color
        self.no_more_time = no_more_time
        self.selective_deepening = selective_deepening

    def search(self, state, depth, alpha=-INFINITY, beta=+INFINITY, maximizing_player=True):
        """Start the MiniMax algorithm.

        :param state: The state to start from.
        :param depth: The maximum allowed depth for the algorithm.
        :param alpha: The alpha of the alpha-beta pruning.
        :param beta: The beta of the alpha-beta pruning.
        :param maximizing_player: Whether this is a max node (True) or a min node (False).
        :return: A tuple: (The alpha-beta algorithm value, The move in case of max node or None in min mode)
        """
        depth_exceeded = depth <= 0 and not (self.selective_deepening and self.selective_deepening(state));
        moves = state.get_possible_moves()
        if depth_exceeded or len(moves) == 0:
            return (self.utility(state), None)

        my_turn = maximizing_player # state.curr_player == self.my_color
        f = max if my_turn else min
        target_param = ALPHA if my_turn else BETA

        params = { }
        params[ALPHA] = alpha
        params[BETA] = beta

        child_res = ((self.search(_expand_state(state, m), depth-1, params[ALPHA], params[BETA], not maximizing_player)[0], m) for m in moves)
        child_res = after_each(child_res, lambda v: operator.setitem(params, target_param, f(params[target_param], v[0])))
        child_res = provide_while(child_res, lambda: params[BETA] <= params[ALPHA]) # Alpha-Beta Pruning
        child_res = provide_while(child_res, self.no_more_time)

        val = f(child_res, key=lambda t: t[0], default=(-INFINITY if my_turn else INFINITY, None))
        return val if my_turn else (val[0], None)

def after_each(iter, post_process):
    for i in iter:     
        post_process(i)
        yield i

def provide_while(iter, stop):
    for i in iter:
        if stop():
            return
        
        yield i