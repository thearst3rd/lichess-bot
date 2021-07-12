# A strategy that minimizes the number of responses that could be made
# Created by Terry Hearst on 2020/12/29

import random
import chess

import strategy

class MinOpponentMovesStrategy(strategy.BaseStrategy):
	def get_move(self, board: chess.Board) -> chess.Move:
		candidates = []
		count = 9999

		# Make a list of moves in which the opponent has the fewest responses
		moves = list(board.legal_moves)
		for move in moves:
			board.push(move)
			responses = board.legal_moves.count()
			board.pop()

			if responses == count:
				candidates.append(move)
			elif responses < count:
				candidates = []
				candidates.append(move)
				count = responses

		# Pick a random move from this list
		move = random.choice(candidates)

		return move
