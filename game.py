# The class that handles playing a game in a thread
# Created by Terry Hearst on 2020/12/29

import threading
import datetime
import time
import random
import berserk
import chess
import chess.engine
import shutil

from chesstournament.strats import *

strat_list = [
	RandomMove,
	MinResponses,
	SuicideKing,
	Stockfish,
	GnuChess,
	Worstfish,
	LightSquares,
	DarkSquares,
	Equalizer,
	Swarm,
	Huddle,
	LightSquaresHardMode,
	DarkSquaresHardMode,
]

# Remove engines if they can't be found
if shutil.which("stockfish") is None:
	print("Can't find stockfish, removing")
	strat_list.remove(Stockfish)
	strat_list.remove(Worstfish)
	strat_list.remove(LightSquaresHardMode)
	strat_list.remove(DarkSquaresHardMode)
if shutil.which("gnuchessu") is None:
	print("Can't find gnuchessu, removing")
	strat_list.remove(GnuChess)

class Game(threading.Thread):
	def __init__(self, client: berserk.Client, game_id, player_id, strategy: Strategy = None, **kwargs):
		super().__init__(**kwargs)
		self.client = client
		self.game_id = game_id
		self.player_id = player_id
		self.strategy = strategy
		self.waiting = False

		info = client.games.export(game_id)
		white_id = info["players"]["white"]["user"]["id"]
		black_id = info["players"]["black"]["user"]["id"]
		self.is_white = white_id == player_id

		print(self.game_id, "GAME STARTED:", white_id, "vs", black_id)

	def strat_select_thread(self):
		# This function will run in a thread while the user is selecting a strategy. If the user picks a strategy, this
		# function will end early. If not, it will select a strategy at random to use.

		time_left = 15	# seconds

		self.send_chat("Please select a strategy you would like me to use. A complete list of strategies can be found "
				+ "here:", False)
		names = list(map(lambda x: x.__name__, strat_list))
		for i in range(len(names) - 1):
			names[i] += ","
		while len(names) > 0:
			end_index = len(names)
			while len(" ".join(names[:end_index])) > 140:
				end_index -= 1
			self.send_chat(" ".join(names[:end_index]), False)
			names = names[end_index:]

		self.send_chat("If you don't respond in 15 seconds, I'll pick a strat at random. Or, you can type \"wait\" I "
				+ "won't pick a strat", False)

		while True:
			if self.waiting or self.strategy is not None:
				break
			if time_left == 10 or time_left == 5:
				self.send_chat(str(time_left) + " seconds left", False)

			if time_left == 0:
				self.pick_strategy()
				break

			time_left -= 1
			time.sleep(1)

	def pick_strategy(self, strategy = None):
		if strategy is None:
			self.strategy = random.choice(strat_list)()
			self.send_chat("Picking strategy: \"" + type(self.strategy).__name__ + "\"")
		else:
			self.strategy = strategy
			self.send_chat("You chose strategy: \"" + type(self.strategy).__name__ + "\"")
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
				self.strategy.setup()
				for move in moves_split:
					board.push(chess.Move.from_uci(move))
					self.strategy.update_state(board)
				self.play_move(board, game_state["wtime"], game_state["btime"], game_state["winc"], game_state["binc"])
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
			if not self.waiting and strat_name == "wait":
				self.waiting = True
				self.send_chat("Waiting", False)
				return
			if len(strat_name) >= 3:
				for strat_class in strat_list:
					if strat_class.__name__.lower().startswith(strat_name):
						self.pick_strategy(strat_class())

	def play_move(self, board: chess.Board, wtime = None, btime = None, winc = None, binc = None):
		limit = None
		if wtime is not None:
			# Workaround - why is this needed???
			if isinstance(wtime, datetime.datetime):
				wtime = wtime.timestamp() * 1000
				btime = btime.timestamp() * 1000
				winc = winc.timestamp() * 1000
				binc = binc.timestamp() * 1000
			limit = chess.engine.Limit(
					white_clock = float(wtime) / 1000.0,
					black_clock = float(btime) / 1000.0,
					white_inc = float(winc) / 1000.0,
					black_inc = float(binc) / 1000.0)
		move = self.strategy.get_move(board, limit = limit)

		uci = move.uci()
		print(self.game_id, "Sending move:", uci)
		self.client.bots.make_move(self.game_id, uci)

	def send_chat(self, chat_line, to_spectators = True):
		print(self.game_id, "Sending " + ("global" if to_spectators else "player") + " message:", chat_line)
		self.client.bots.post_message(self.game_id, chat_line)
		if to_spectators:
			self.client.bots.post_message(self.game_id, chat_line, spectator=True)
