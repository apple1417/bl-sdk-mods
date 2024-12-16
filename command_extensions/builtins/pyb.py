import argparse
import re
import shlex
import traceback

from mods_base import command
from unrealsdk import logging

RE_OPTIONAL_ARG = re.compile(r"^\s*--?\w+")  # type: ignore

cached_lines: list[str] = []


@command(
    splitter=lambda args: shlex.split(args) if RE_OPTIONAL_ARG.match(args) else [args],
    description=(
        "Runs a block of python statements, which may span multiple lines. Only one space after the"
        " command is consumed for arg parsing - `pyb[3*space]abc` extracts the line `[2*space]abc`."
    ),
    epilog=(
        "If an optional arg is specified, python code is ignored. Optional args must be at the"
        " start of the command to be recognised."
    ),
)
def pyb(args: argparse.Namespace) -> None:  # noqa: D103
    if args.print:
        for line in cached_lines:
            logging.info(line)
    if args.exec:
        joined = "\n".join(cached_lines)
        try:
            exec(joined, {})  # noqa: S102
        except Exception:  # noqa: BLE001
            logging.error("Error occured during 'pyb' command:")
            logging.error(joined)
            if len(cached_lines) > 1:
                logging.error("=" * 80)

            traceback.print_exc()
    if args.discard or args.exec:
        cached_lines.clear()

    if args.exec or args.discard or args.print:
        return

    # Skip the first whitespace character
    cached_lines.append(args.args[0][1:])


pyb.add_argument("args", help="Python code. Whitespace is preserved.", nargs=argparse.REMAINDER)
pyb.add_argument(
    "-x",
    "--exec",
    action="store_true",
    help="Executes stored lines.",
)
pyb.add_argument(
    "-d",
    "--discard",
    action="store_true",
    help="Discards stored lines.",
)
pyb.add_argument(
    "-p",
    "--print",
    action="store_true",
    help="Prints stored lines.",
)
