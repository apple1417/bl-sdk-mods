import unrealsdk
import argparse

from .. import RegisterConsoleCommand
from . import obj_name_splitter, re_obj_name


def handler(args: argparse.Namespace) -> None:
    match = re_obj_name.match(args.object)
    if match is None:
        unrealsdk.Log(f"Unable to parse object name {args.object}")
        return

    klass = match.group("class") or "Object"
    name = match.group("fullname")
    obj = unrealsdk.FindObject(klass, name)
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
