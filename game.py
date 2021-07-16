# The class that handles playing a game in a thread
# Created by Terry Hearst on 2020/12/29

import threading
import time
import random
import berserk
import chess

import strategy

from strategies.random import RandomMoveStrategy
from strategies.minopponentmoves import MinOpponentMovesStrategy
from strategies.worstfish import WorstfishStrategy
from strategies.lightdarksquares import LightOrDarkSquaresStrategy
from strategies.suicideking import SuicideKingStrategy

class Game(threading.Thread):
	def __init__(self, client: berserk.Client, game_id, player_id, strategy: strategy.BaseStrategy = None, **kwargs):
		super().__init__(**kwargs)
		self.client = client
		self.game_id = game_id
		self.player_id = player_id
		self.strategy = strategy

		info = client.games.export(game_id)
		white_id = info["players"]["white"]["user"]["id"]
		black_id = info["players"]["black"]["user"]["id"]
		self.is_white = white_id == player_id

		print(self.game_id, "GAME STARTED:", white_id, "vs", black_id)

	def strat_select_thread(self):
		# This function will run in a thread while the user is selecting a strategy. If the user picks a strategy, this
		# function will end early. If not, it will select a strategy at random to use.

		time_left = 15	# seconds

		self.send_chat("Please select a strategy you would like me to play:", False)
		self.send_chat("Random, Worstfish, Light Squares, Dark Squares, Min Opponent Moves, Suicide King", False)
		self.send_chat("If you don't choose a strategy in " + str(time_left) + " seconds, I'll pick one at random.",
				False)

		while True:
			if self.strategy is not None:
				break
			if time_left == 10 or time_left == 5:
				self.send_chat(str(time_left) + " seconds left", False)

			if time_left == 0:
				random_strat = random.choice([
					RandomMoveStrategy(),
					WorstfishStrategy(),
					LightOrDarkSquaresStrategy(chess.WHITE),
					LightOrDarkSquaresStrategy(chess.BLACK),
					MinOpponentMovesStrategy(),
					SuicideKingStrategy(),
				])
				self.pick_strategy(random_strat)
				break

			time_left -= 1
			time.sleep(1)

	def pick_strategy(self, strategy):
		self.strategy = strategy
		strat_name = strategy.get_name()
		print(self.game_id, "USING STRATEGY:", strat_name)
		self.send_chat("Using strategy: \"" + strat_name + "\"")
		if self.current_game_state is not None:
			self.handle_state_change(self.current_game_state)
			self.current_game_state = None


	def run(self):
		for event in self.client.bots.stream_game_state(self.game_id):
			if event["type"] == "gameFull":
				self.send_chat("Thanks for playing!")
				self.current_game_state = None
				if self.strategy is None:
					self.strat_selector_thread = threading.Thread(target = self.strat_select_thread)
					self.strat_selector_thread.start()
				else:
					self.pick_strategy(self.strategy)
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

		moves_split = game_state["moves"].split()

		# Is it our turn?
		if len(moves_split) % 2 == (0 if self.is_white else 1):
			if self.strategy is not None:
				# Recreate the chess board from the moves
				board = chess.Board()
				for move in moves_split:
					board.push(chess.Move.from_uci(move))
				self.play_move(board)
			else:
				self.current_game_state = game_state

	def handle_chat_line(self, chat_line):
		if chat_line["username"].lower() == self.player_id:
			return

		msg = chat_line["username"] + ": " + chat_line["text"]
		if chat_line["room"] == "spectator":
			msg = "[Spectator] " + msg
		print(self.game_id, msg)

		# Pick strategy
		if self.strategy is None:
			strat_name = chat_line["text"].lower()
			if len(strat_name) >= 3:
				if "random".startswith(strat_name):
					self.pick_strategy(RandomMoveStrategy())
				elif "worstfish".startswith(strat_name):
					self.pick_strategy(WorstfishStrategy())
				elif "light squares".startswith(strat_name):
					self.pick_strategy(LightOrDarkSquaresStrategy(chess.WHITE))
				elif "dark squares".startswith(strat_name):
					self.pick_strategy(LightOrDarkSquaresStrategy(chess.BLACK))
				elif "min opponent moves".startswith(strat_name):
					self.pick_strategy(MinOpponentMovesStrategy())
				elif "suicide king".startswith(strat_name):
					self.pick_strategy(SuicideKingStrategy())

	def play_move(self, board: chess.Board):
		move = self.strategy.get_move(board)

		uci = move.uci()
		print(self.game_id, "Sending move:", uci)
		self.client.bots.make_move(self.game_id, uci)

		board.push(move)
		self.strategy.update_state(move, board)

	def send_chat(self, chat_line, to_spectators = True):
		print(self.game_id, "Sending " + ("global" if to_spectators else "player") + " message:", chat_line)
		self.client.bots.post_message(self.game_id, chat_line)
		if to_spectators:
			self.client.bots.post_message(self.game_id, chat_line, spectator=True)
