# The definition of a chess-playing strategy
# Created by Terry Hearst on 2020/12/29

import chess

class BaseStrategy():
	def __init__(self, **kwargs):
		# Here, a stateful strategy can declare variables about its state
		pass

	def get_name(self):
		# Returns the name of the strategy. As a default, it will return the class name.
		return type(self).__name__

	def get_move(self, board: chess.Board) -> chess.Move:
		# Here is the code in which a strategy will determine which move it would play on the given board
		# NOTE: If this strategy is stateful, it should NOT update its state here, rather in the next method

		# This method MUST be overwritten
		raise NotImplementedError

	def update_state(self, move: chess.Move, board: chess.Board) -> None:
		# Here, a stateful strategy is told which move was played and the resulting board state, which can be used to
		# update its state. By default, no changes need to be made
		pass
