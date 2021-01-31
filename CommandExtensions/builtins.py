import unrealsdk
import argparse
import fnmatch
import glob
import re
import shlex
import sys
from os import path
from typing import Dict, List

from . import RegisterConsoleCommand

re_obj_name = re.compile(
    r"((?P<class>[\w?+!,'\"\\\-]+?)')?(?P<fullname>((?P<outer>[\w.:?+!,'\"\\\-]+)[.:])?(?P<name>[\w?+!,'\"\\\-]+))(?(class)'|)",
    flags=re.I
)


def obj_name_splitter(args: str) -> List[str]:
    """
    Custom argument splitter that returns object names as single tokens. This makes the splitting
    significantly less versatile.
    """
    lex = shlex.shlex(args)
    lex.wordchars += ".:?+!,'\"\\-"
    lex.quotes = ""
    output = []
    token = lex.get_token()
    while token:
        output.append(token)
        token = lex.get_token()
    return output


"""=============================================================================================="""


def handle_clone(args: argparse.Namespace) -> None:
    src_match = re_obj_name.match(args.base)
    if src_match is None:
        unrealsdk.Log(f"Unable to parse object name {args.base}")
        return

    src_class = src_match.group("class") or "Object"
    src_fullname = src_match.group("fullname")
    src_object = unrealsdk.FindObject(src_class, src_fullname)
    if src_object is None:
        unrealsdk.Log(f"Unable to find object {args.base}")
        return

    dst_match = re_obj_name.match(args.clone)
    if dst_match is None:
        unrealsdk.Log(f"Unable to parse object name {args.clone}")
        return

    dst_class = dst_match.group("class") or "Object"
    if dst_class != "Object" and dst_class != src_class:
        unrealsdk.Log(f"Cannot clone object of class {src_class} as class {dst_class}")
        return

    dst_outer = dst_match.group("outer")
    dst_outer_object = None
    if dst_outer:
        dst_outer_object = unrealsdk.FindObject("Object", dst_outer)
        if dst_outer_object is None:
            unrealsdk.Log(f"Unable to find outer object {dst_outer}")
            return

    dst_name = dst_match.group("name")

    cloned = unrealsdk.ConstructObject(
        Class=src_object.Class,
        Outer=dst_outer_object,
        Name=dst_name,
        Template=src_object
    )
    if cloned is not None:
        unrealsdk.KeepAlive(cloned)


clone_parser = RegisterConsoleCommand(
    "clone",
    handle_clone,
    splitter=obj_name_splitter,
    description="Creates a clone of an existing object."
)
clone_parser.add_argument("base", help="The object to create a copy of.")
clone_parser.add_argument("clone", help="The name of the clone to create.")


"""=============================================================================================="""


game_dir = path.abspath(path.join(path.dirname(sys.executable), "..", ".."))
all_upks = glob.glob(path.join(game_dir, "WillowGame", "CookedPCConsole", "*.upk"))
all_upks += glob.glob(path.join(game_dir, "DLC", "*", "*", "Content", "*.upk"))
all_upks = [path.splitext(path.basename(upk))[0] for upk in all_upks]


def handle_load_package(args: argparse.Namespace) -> None:
    upks = fnmatch.filter(all_upks, args.package)
    if len(upks) <= 0:
        unrealsdk.Log(f"Could not find package '{args.package}'!")
    elif len(upks) > 10:
        unrealsdk.Log(f"'{args.package}' matches more than 10 packages!")
    else:
        for package in upks:
            unrealsdk.LoadPackage(package)


load_parser = RegisterConsoleCommand(
    "load_package",
    handle_load_package,
    description=(
        "Loads a package and all objects contained within it. This freezes the game as it loads; it"
        " should be used sparingly. Supports using glob-style wildcards to load up to 10 packages"
        " at once, though being explicit should still be prefered."
    )
)
load_parser.add_argument(
    "package",
    help=(
        "The package(s) to load. This uses the full upk names; not the shortened version hotfixes"
        " use."
    )
)


"""=============================================================================================="""


def handle_keep_alive(args: argparse.Namespace) -> None:
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


keep_alive_parser = RegisterConsoleCommand(
    "keep_alive",
    handle_keep_alive,
    splitter=obj_name_splitter,
    description=(
        "Prevents an object from being garbaged collected, it will always be loaded until you"
        " restart the game."
    )
)
keep_alive_parser.add_argument("object", help="The object to keep alive.")


"""=============================================================================================="""


suppressed_patterns: Dict[str, int] = {}
suppress_global_count: int = 0


def handle_suppress_next_chat(args: argparse.Namespace) -> None:
    global suppress_global_count
    if args.pattern == "*":
        suppress_global_count += 1
        return

    if args.pattern not in suppressed_patterns:
        suppressed_patterns[args.pattern] = 0
    suppressed_patterns[args.pattern] += 1


suppress_next_chat_parser = RegisterConsoleCommand(
    "suppress_next_chat",
    handle_suppress_next_chat,
    description="""
Prevents the next chat message that matches a given glob pattern from being printed.  Multiple calls
to this stack, and suppress multiple messages.

This is intended to be used to suppress an error message, so that it only gets printed when someone
tries to exec your file without running Command Extensions.
"""[1:-1],
    formatter_class=argparse.RawDescriptionHelpFormatter
)
suppress_next_chat_parser.add_argument(
    "pattern",
    nargs="?",
    default="*",
    help="The glob pattern matching the message to suppress."
)


def ServerSay(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
    global suppress_global_count

    for pattern, count in suppressed_patterns.items():
        if fnmatch.fnmatch(params.msg, pattern):
            if count == 1:
                del suppressed_patterns[pattern]
            else:
                suppressed_patterns[pattern] -= 1
            return False

    if suppress_global_count > 0:
        suppress_global_count -= 1
        return False

    return True


unrealsdk.RunHook("Engine.PlayerController.ServerSay", __name__, ServerSay)
