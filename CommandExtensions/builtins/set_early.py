import unrealsdk
import argparse

from .. import RegisterConsoleCommand


def handler(args: argparse.Namespace) -> None:
    unrealsdk.GetEngine().GamePlayers[0].Actor.ConsoleCommand("set " + args.args)


parser = RegisterConsoleCommand(
    "set_early",
    handler,
    splitter=lambda m: [m],
    description=(
        "Behaves exactly like a set command. Only useful in files, as it's run during custom"
        " command parsing instead of afterwards."
    ),
)
parser.add_argument(
    "args",
    help="Standard set command arguments",
    # This doesn't do anything cause of the custom splitter, but it looks better in the help text
    nargs="+"
)
