# Bot that can play with multiple strategies
# Created by Terry Hearst on 2020/12/29

import random
import berserk
import chess

from game import Game

from strategies.random import RandomMoveStrategy
from strategies.minopponentmoves import MinOpponentMovesStrategy
from strategies.worstfish import WorstfishStrategy
from strategies.sameoppcolor import SameOrOppositeColorStrategy

# Only accept unrated challenges of standard games
def should_accept(challenge):
	if challenge["variant"]["key"] != "standard":
		return False
	if challenge["rated"] != False:
		return False

	return True

# Main loop, stream events and start playing games
def main():
	with open("bot.token") as f:
		token = f.read().strip()

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
			if should_accept(event["challenge"]):
				client.bots.accept_challenge(event["challenge"]["id"])
			else:
				client.bots.decline_challenge(event["challenge"]["id"])
		elif event["type"] == "gameStart":
			strategy = WorstfishStrategy()
			game = Game(client, event["game"]["id"], player_id, strategy)
			game.start()

if __name__ == "__main__":
	main()
