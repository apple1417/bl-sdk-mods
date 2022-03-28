import unrealsdk
import argparse

from .. import RegisterConsoleCommand


def handler(args: argparse.Namespace) -> None:
    unrealsdk.GetEngine().GamePlayers[0].Actor.ConsoleCommand("exec " + " ".join(args.args))


parser = RegisterConsoleCommand(
    "exec_raw",
    handler,
    splitter=lambda m: [m],
    description="Behaves exactly like an `exec` command, but disables custom command parsing."
)
parser.add_argument(
    "args",
    help="Standard exec command arguments",
    # This doesn't do anything cause of the custom splitter, but it looks better in the help text
    nargs=argparse.REMAINDER
)
