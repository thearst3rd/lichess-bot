# A strategy that just plays random moves
# Created by Terry Hearst on 2020/12/29

import random
import chess

import strategy

class RandomMoveStrategy(strategy.BaseStrategy):
	def get_move(self, board: chess.Board) -> chess.Move:
		moves = list(board.legal_moves)
		move = random.choice(moves)

		return move
