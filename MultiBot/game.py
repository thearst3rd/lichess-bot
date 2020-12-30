# The class that handles playing a game in a thread
# Created by Terry Hearst on 2020/12/29

import threading
import berserk
import chess

import strategy

class Game(threading.Thread):
	def __init__(self, client: berserk.Client, game_id, player_id, strategy: strategy.BaseStrategy, **kwargs):
		super().__init__(**kwargs)
		self.client = client
		self.game_id = game_id
		self.player_id = player_id
		self.strategy = strategy

		info = client.games.export(game_id)
		white_id = info["players"]["white"]["user"]["id"]
		black_id = info["players"]["black"]["user"]["id"]
		self.is_white = white_id == player_id

		stratName = type(strategy).__name__
		print("stratName:", stratName)
		client.bots.post_message(game_id, "Thanks for playing! Right now using strategy: " + stratName)
		print(game_id, "GAME STARTED:", white_id, "vs", black_id)

	def run(self):
		for event in self.client.bots.stream_game_state(self.game_id):
			#print("Game " + self.game_id + " event received: " + event["type"])
			if event["type"] == "gameFull":
				self.handle_state_change(event["state"])
			elif event["type"] == "gameState":
				self.handle_state_change(event)
			elif event["type"] == "chatLine":
				self.handle_chat_line(event)

	def handle_state_change(self, game_state):
		# Is the game over?
		if game_state["status"] != "started":
			print(self.game_id, "GAME OVER:", game_state["status"])
			return

		movesSplit = game_state["moves"].split()

		# Is it our turn?
		if len(movesSplit) % 2 == (0 if self.is_white else 1):
			# Recreate the chess board from the moves
			board = chess.Board()
			for move in movesSplit:
				board.push(chess.Move.from_uci(move))

			#print(self.game_id, "Board state:", board.fen())
			self.play_move(board)

	def handle_chat_line(self, chat_line):
		print(self.game_id, chat_line["username"], ":", chat_line["text"])

	def play_move(self, board: chess.Board):
		move = self.strategy.get_move(board)

		uci = move.uci()
		print(self.game_id, "Sending move:", uci)
		self.client.bots.make_move(self.game_id, uci)

		board.push(move)
		self.strategy.update_state(move, board)
