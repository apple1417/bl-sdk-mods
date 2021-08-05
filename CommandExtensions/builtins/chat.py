import unrealsdk
import argparse

from .. import RegisterConsoleCommand


def handler(args: argparse.Namespace) -> None:
    chat_movie = unrealsdk.GetEngine().GamePlayers[0].Actor.GetTextChatMovie()
    source = args.source
    if source is None:
        timestamp = chat_movie.GetTimestampString(
            unrealsdk.FindAll("WillowSaveGameManager")[0].TimeFormat
        )
        player = unrealsdk.GetEngine().GamePlayers[0].Actor.PlayerReplicationInfo.PlayerName
        source = player + " " + timestamp
    chat_movie.AddChatMessageInternal(source, args.msg)


parser = RegisterConsoleCommand(
    "chat",
    handler,
    description=(
        "Similarly to the `say` command, writes a message in chat, but without chance of crashing"
        " the game. Also lets you customize the message source. Note this does not use the same"
        " parsing as the `say` command, make sure you quote your message if it includes spaces."
    ),
)
parser.add_argument(
    "source",
    help=(
        "What the message source should be. Defaults to the same as a normal chat message,"
        " username/timestamp."
    ),
    nargs="?",
)
parser.add_argument("msg", help="The message to write.")
