import argparse

from .. import RegisterConsoleCommand
from . import obj_name_splitter, parse_object


def handler(args: argparse.Namespace) -> None:
    obj = parse_object(args.object)
    if obj is None:
        return

    if args.undo:
        obj.ObjectFlags.B &= ~4
    else:
        obj.ObjectFlags.B |= 4


parser = RegisterConsoleCommand(
    "unlock_package",
    handler,
    splitter=obj_name_splitter,
    description="Unlocks an object allowing it to be referenced cross-package."
)
parser.add_argument("object", help="The object to unlock.")
parser.add_argument(
    "-u", "--undo",
    action="store_true",
    help="Undo a previous unlock package call."
)
