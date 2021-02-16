import unrealsdk
import argparse
import fnmatch
from typing import Dict

from .. import RegisterConsoleCommand

suppressed_patterns: Dict[str, int] = {}
suppress_global_count: int = 0


def handler(args: argparse.Namespace) -> None:
    global suppress_global_count
    if args.pattern == "*":
        suppress_global_count += 1
        return

    if args.pattern not in suppressed_patterns:
        suppressed_patterns[args.pattern] = 0
    suppressed_patterns[args.pattern] += 1


parser = RegisterConsoleCommand(
    "suppress_next_chat",
    handler,
    description="""
Prevents the next chat message that matches a given glob pattern from being printed.  Multiple calls
to this stack, and suppress multiple messages.

This is intended to be used to suppress an error message, so that it only gets printed when someone
tries to exec your file without running Command Extensions.
"""[1:-1],
    formatter_class=argparse.RawDescriptionHelpFormatter
)
parser.add_argument(
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
