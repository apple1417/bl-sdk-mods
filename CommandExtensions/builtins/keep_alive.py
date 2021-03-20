import unrealsdk
import argparse

from .. import RegisterConsoleCommand
from . import obj_name_splitter, parse_object


def handler(args: argparse.Namespace) -> None:
    obj = parse_object(args.object)
    if obj is None:
        return

    if args.undo:
        obj.ObjectFlags.A &= ~0x4000
    else:
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
parser.add_argument(
    "-u", "--undo",
    action="store_true",
    help=(
        "Undo a previous keep alive call. Note that this only affects the specific provided object,"
        " a normal keep alive command might also have affected a parent object."
    )
)
