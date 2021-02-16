import unrealsdk
import argparse
import fnmatch
import glob
import sys
from os import path

from .. import RegisterConsoleCommand

game_dir = path.abspath(path.join(path.dirname(sys.executable), "..", ".."))
all_upks = glob.glob(path.join(game_dir, "WillowGame", "CookedPCConsole", "*.upk"))
all_upks += glob.glob(path.join(game_dir, "DLC", "*", "*", "Content", "*.upk"))
all_upks = [path.splitext(path.basename(upk))[0] for upk in all_upks]


def handler(args: argparse.Namespace) -> None:
    upks = fnmatch.filter(all_upks, args.package)
    if len(upks) <= 0:
        unrealsdk.Log(f"Could not find package '{args.package}'!")
    elif len(upks) > 10:
        unrealsdk.Log(f"'{args.package}' matches more than 10 packages!")
    else:
        for package in upks:
            unrealsdk.LoadPackage(package)


parser = RegisterConsoleCommand(
    "load_package",
    handler,
    description=(
        "Loads a package and all objects contained within it. This freezes the game as it loads; it"
        " should be used sparingly. Supports using glob-style wildcards to load up to 10 packages"
        " at once, though being explicit should still be prefered."
    )
)
parser.add_argument(
    "package",
    help=(
        "The package(s) to load. This uses the full upk names; not the shortened version hotfixes"
        " use."
    )
)
