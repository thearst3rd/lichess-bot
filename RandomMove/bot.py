# Lichess bot test
# by Terry Hearst on 2020/12/27

import threading
import random

import berserk
import chess

# Only accept unrated challenges of standard games
def should_accept(event):
	challenge = event["challenge"]

	if challenge["variant"]["key"] != "standard":
		return False
	if challenge["rated"] != False:
		return False

	return True

# The class that handles the playing of games
class Game(threading.Thread):
	def __init__(self, client, game_id, player_id, **kwargs):
		super().__init__(**kwargs)
		self.game_id = game_id
		self.player_id = player_id
		self.client = client
		self.stream = client.bots.stream_game_state(game_id)
		self.current_state = next(self.stream)

		info = client.games.export(game_id)
		white_id = info["players"]["white"]["user"]["id"]
		black_id = info["players"]["black"]["user"]["id"]

		print(game_id, "GAME STARTED:", white_id, "vs", black_id)

		client.bots.post_message(game_id, "Thanks for playing! Right now, I'm making random moves.")

		self.is_white = white_id == player_id

		self.handle_state_change(self.current_state["state"])

	def run(self):
		for event in self.stream:
			#print("Game " + self.game_id + " event received: " + event["type"])
			if event["type"] == "gameState":
				self.handle_state_change(event)
			elif event["type"] == "chatLine":
				self.handle_chat_line(event)

	def handle_state_change(self, game_state):
		# Recreate the chess board from the moves
		movesSplit = game_state["moves"].split()

		board = chess.Board()
		for move in movesSplit:
			board.push(chess.Move.from_uci(move))

		print(self.game_id, "Board state:", board.fen())

		# Is the game over?
		if game_state["status"] != "started":
			print(self.game_id, "GAME OVER:", game_state["status"])
			return

		# Is it our turn?
		if len(movesSplit) % 2 == (0 if self.is_white else 1):
			self.play_move(board)

	def handle_chat_line(self, chat_line):
		print(self.game_id, chat_line["username"], ":", chat_line["text"])

	def play_move(self, board):
		moves = list(board.legal_moves)
		n = random.randint(0, len(moves) - 1)
		move = moves[n]
		uci = move.uci()

		print(self.game_id, "Sending move:", uci)
		self.client.bots.make_move(self.game_id, uci)

# Main loop, stream events and start playing games
def main():
	with open("../bot.token") as f:
		token = f.read()

	session = berserk.TokenSession(token)
	client = berserk.Client(session)

	try:
		player_id = client.account.get()["id"]
	except berserk.exceptions.ResponseError as e:
		print("Exception:", e)
		return

	print("Connected to Lichess as:", player_id)
	print("Listening for events...")

	for event in client.bots.stream_incoming_events():
		#print("Global event received: " + event["type"])
		if event["type"] == "challenge":
			if should_accept(event):
				client.bots.accept_challenge(event["challenge"]["id"])
			else:
				client.bots.decline_challenge(event["challenge"]["id"])
		elif event["type"] == "gameStart":
			game = Game(client, event["game"]["id"], player_id)
			game.start()

if __name__ == "__main__":
	main()
