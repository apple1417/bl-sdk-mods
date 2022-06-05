import unrealsdk
import argparse
import re
import shlex
from typing import List

from .. import RegisterConsoleCommand, log_traceback, pyexec_globals

RE_OPTIONAL_ARG: re.Pattern = re.compile(r"^\s*--?\w+")  # type: ignore

_cached_lines: List[str] = []


def handler(args: argparse.Namespace) -> None:
    if args.print:
        for line in _cached_lines:
            unrealsdk.Log(line)
    if args.exec:
        joined = "\n".join(_cached_lines)
        try:
            exec(joined, pyexec_globals)
        except Exception:
            log_traceback()
    if args.discard or args.exec:
        _cached_lines.clear()

    if args.exec or args.discard or args.print:
        return

    _cached_lines.append(args.args[0])


parser = RegisterConsoleCommand(
    "pyb",
    handler,
    splitter=lambda args: shlex.split(args) if RE_OPTIONAL_ARG.match(args) else [args],
    description=(
        "Runs a block of python statements, which may span multiple lines. Only one space after the"
        " command is consumed for arg parsing - `pyb[3*space]abc` extracts the line `[2*space]abc`."
    ),
    epilog=(
        "If an optional arg is specified, python code is ignored. Optional args must be at the"
        " start of the command to be recognised."
    )
)

parser.add_argument(
    "args",
    help="Python code. Whitespace is preserved.",
    nargs=argparse.REMAINDER
)
parser.add_argument(
    "-x", "--exec",
    action="store_true",
    help="Executes stored lines.",
)
parser.add_argument(
    "-d", "--discard",
    action="store_true",
    help="Discards stored lines.",
)
parser.add_argument(
    "-p", "--print",
    action="store_true",
    help="Prints stored lines.",
)
