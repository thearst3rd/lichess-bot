# Bot that can play with multiple strategies
# Created by Terry Hearst on 2020/12/29

import berserk

from game import Game

# Only accept unrated challenges of standard games
def should_accept(challenge):
	if challenge["rated"] != False:
		return berserk.Reason.CASUAL
	if challenge["timeControl"]["type"] != "clock":
		return berserk.Reason.TIMECONTROL
	if challenge["variant"]["key"] != "standard":
		return berserk.Reason.STANDARD

	return None

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
		if event["type"] == "challenge":
			decline_reason = should_accept(event["challenge"])
			if decline_reason is None:
				client.bots.accept_challenge(event["challenge"]["id"])
			else:
				client.bots.decline_challenge(event["challenge"]["id"], decline_reason)
		elif event["type"] == "gameStart":
			game = Game(client, event["game"]["id"], player_id)
			game.start()

if __name__ == "__main__":
	main()
