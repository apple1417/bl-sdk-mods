import unrealsdk
import argparse

from .. import RegisterConsoleCommand
from . import obj_name_splitter, parse_object


def handler(args: argparse.Namespace) -> None:
    obj = parse_object(args.object)
    if obj is None:
        unrealsdk.Log(f"Unable to find object {args.object}")
        return

    unrealsdk.KeepAlive(obj)


parser = RegisterConsoleCommand(
    "keep_alive",
    handler,
    splitter=obj_name_splitter,
    description=(
        "Prevents an object from being garbaged collected, it will always be loaded until you"
        " restart the game."
    )
)
parser.add_argument("object", help="The object to keep alive.")
