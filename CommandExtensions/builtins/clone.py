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
    """
    Clones an object and sets it up for proper use while modding.

    Args:
        src: The object to use as the template.
        outer: The outer object the clone should be created under.
        name: The name of the cloned object.
    Returns:
        The cloned object, or None if it failed to clone.
    """
    cloned = unrealsdk.ConstructObject(
        Class=src.Class,
        Outer=outer,
        Name=name,
        Template=src
    )
    if cloned is None:
        return None

    unrealsdk.KeepAlive(cloned)
    cloned.ObjectArchetype = src.ObjectArchetype
    # Don't ask me what on earth this means, but it lets you reference objects cross package
    cloned.ObjectFlags.B |= 4
    return cloned


def parse_clone_target(
    name: str,
    src_class: str,
    suppress_exists: bool
) -> Tuple[Optional[unrealsdk.UObject], Optional[str]]:
    """
    Parses a full object name intended to be a clone target into it's outer object and name.

    If it's unable to parse or find the object, logs an error to console and returns None.

    Args:
        name: The full object name to parse.
        src_class: The class of the source object. The target must use this class (or object).
        suppress_exists: If true, doesn't log exists errors to console.
    Returns:
        A tuple of the target's outer object and it's name, or a tuple of two `None`s on error.
    """
    dst_match = re_obj_name.match(name)
    if dst_match is None:
        unrealsdk.Log(f"Unable to parse object name {name}")
        return None, None

    dst_class = dst_match.group("class") or "Object"
    if dst_class != "Object" and dst_class != src_class:
        unrealsdk.Log(f"Cannot clone object of class {src_class} as class {dst_class}")
        return None, None

    dst_obj = unrealsdk.FindObject(dst_class, dst_match.group("fullname"))
    if dst_obj is not None:
        if not suppress_exists:
            unrealsdk.Log(f"Object '{dst_obj.PathName(dst_obj)}' already exists")
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
    outer, name = parse_clone_target(args.clone, src.Class.Name, args.suppress_exists)
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
parser.add_argument(
    "-x", "--suppress-exists",
    action="store_true",
    help="Suppress the error message when an object already exists."
)
