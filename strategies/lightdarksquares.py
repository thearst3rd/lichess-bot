# A strategy that prefers moves pieces onto certain color squares
# Created by Terry Hearst on 2021/01/10

import random
import chess

import strategy

class LightOrDarkSquaresStrategy(strategy.BaseStrategy):
	def __init__(self, target_color: chess.Color = None):
		if target_color is None:
			self.target_color = random.choice([chess.WHITE, chess.BLACK])
		else:
			self.target_color = target_color

	def get_name(self):
		return "Light Squares" if (self.target_color == chess.WHITE) else "Dark Squares"

	def get_move(self, board: chess.Board) -> chess.Move:
		candidates = []
		highest_count = 0

		for move in board.legal_moves:
			board.push(move)
			count = self.count_pieces(board, not board.turn, self.target_color)
			board.pop()

			if count > highest_count:
				highest_count = count
				candidates = []
				candidates.append(move)
			elif count == highest_count:
				candidates.append(move)

		move = random.choice(candidates)
		return move

	def count_pieces(self, board: chess.Board, our_color: chess.Color, desired_color: chess.Color):
		bitboard = chess.BB_LIGHT_SQUARES if (desired_color == chess.WHITE) else chess.BB_DARK_SQUARES
		square_set = chess.SquareSet(bitboard)

		# I couldn't find a way to return them all in one...
		our_pieces  = board.pieces(chess.PAWN, our_color)
		our_pieces |= board.pieces(chess.KNIGHT, our_color)
		our_pieces |= board.pieces(chess.BISHOP, our_color)
		our_pieces |= board.pieces(chess.ROOK, our_color)
		our_pieces |= board.pieces(chess.QUEEN, our_color)
		our_pieces |= board.pieces(chess.KING, our_color)

		square_set &= our_pieces
		return len(square_set)
