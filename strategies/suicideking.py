# A strategy that minimizes the number of responses that could be made
# Created by Terry Hearst on 2020/12/29

import math
import random
import chess

import strategy

class SuicideKingStrategy(strategy.BaseStrategy):
	def get_move(self, board: chess.Board) -> chess.Move:
		candidates = []
		min_dist = 9999

		# Make a list of moves in which the kings are the closest distance
		moves = list(board.legal_moves)
		for move in moves:
			board.push(move)
			dist = self.calc_king_dist(board)
			board.pop()

			if dist == min_dist:
				candidates.append(move)
			elif dist < min_dist:
				candidates = []
				candidates.append(move)
				min_dist = dist

		# Pick a random move from this list
		move = random.choice(candidates)

		return move

	def calc_king_dist(self, board: chess.Board):
		king_white = board.king(chess.WHITE)
		king_black = board.king(chess.BLACK)

		file_diff = abs(chess.square_file(king_white) - chess.square_file(king_black))
		rank_diff = abs(chess.square_rank(king_white) - chess.square_rank(king_black))

		return math.sqrt((file_diff * file_diff) + (rank_diff * rank_diff))
