import unrealsdk
import argparse
from typing import Optional, Tuple

from .. import RegisterConsoleCommand
from . import obj_name_splitter, parse_object, re_obj_name


def clone_object(
    src: unrealsdk.UObject,
    outer: Optional[unrealsdk.UObject],
    name: str
) -> Optional[unrealsdk.UObject]:
    cloned = unrealsdk.ConstructObject(
        Class=src.Class,
        Outer=outer,
        Name=name,
        Template=src
    )
    if cloned is None:
        return None

    unrealsdk.KeepAlive(cloned)
    # Don't ask me what on earth this means
    cloned.ObjectFlags.B |= 4
    return cloned


def parse_clone_target(
    name: str,
    src_class: str
) -> Tuple[Optional[unrealsdk.UObject], Optional[str]]:
    dst_match = re_obj_name.match(name)
    if dst_match is None:
        unrealsdk.Log(f"Unable to parse object name {name}")
        return None, None

    dst_class = dst_match.group("class") or "Object"
    if dst_class != "Object" and dst_class != src_class:
        unrealsdk.Log(f"Cannot clone object of class {src_class} as class {dst_class}")
        return None, None

    dst_outer = dst_match.group("outer")
    dst_outer_object = None
    if dst_outer:
        dst_outer_object = unrealsdk.FindObject("Object", dst_outer)
        if dst_outer_object is None:
            unrealsdk.Log(f"Unable to find outer object {dst_outer}")
            return None, None

    return dst_outer_object, dst_match.group("name")


def handler(args: argparse.Namespace) -> None:
    src = parse_object(args.base)
    if src is None:
        return
    outer, name = parse_clone_target(args.clone, src.Class.Name)
    if name is None:
        return

    clone_object(src, outer, name)


parser = RegisterConsoleCommand(
    "clone",
    handler,
    splitter=obj_name_splitter,
    description="Creates a clone of an existing object."
)
parser.add_argument("base", help="The object to create a copy of.")
parser.add_argument("clone", help="The name of the clone to create.")
