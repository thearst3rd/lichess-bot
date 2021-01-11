# A strategy that moves pieces onto the same color
# Created by Terry Hearst on 2021/01/10

import random
import chess

import strategy

class SameOrOppositeColorStrategy(strategy.BaseStrategy):
	def __init__(self, same: bool = None):
		if same is None:
			self.same = random.choice([True, False])
		else:
			self.same = same

	def get_name(self):
		return "Same Color" if self.same else "Opposite Color"

	def get_move(self, board: chess.Board) -> chess.Move:
		ourColor = board.turn
		mostColorCount = 0
		mostColorMoves = None

		for move in board.legal_moves:
			board.push(move)
			count = self.countPieces(board, ourColor, ourColor if self.same else not ourColor)
			board.pop()

			if count > mostColorCount:
				mostColorCount = count
				mostColorList = []
				mostColorList.append(move)
			elif count == mostColorCount:
				mostColorList.append(move)

		move = random.choice(mostColorList)
		return move

	def countPieces(self, board: chess.Board, ourColor: chess.Color, desiredColor: chess.Color):
		bitboard = chess.BB_LIGHT_SQUARES if (desiredColor == chess.WHITE) else chess.BB_DARK_SQUARES
		squareSet = chess.SquareSet(bitboard)

		# I couldn't find a way to return them all in one...
		ourPieces = board.pieces(chess.PAWN, ourColor)
		ourPieces |= board.pieces(chess.KNIGHT, ourColor)
		ourPieces |= board.pieces(chess.BISHOP, ourColor)
		ourPieces |= board.pieces(chess.ROOK, ourColor)
		ourPieces |= board.pieces(chess.QUEEN, ourColor)
		ourPieces |= board.pieces(chess.KING, ourColor)

		squareSet &= ourPieces
		return len(squareSet)
