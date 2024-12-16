import argparse

from mods_base import command, get_pc


@command(
    splitter=lambda m: [m.lstrip()],
    description=(
        "Behaves exactly like a `set` command. Only useful in files, as it's run during custom"
        " command parsing instead of afterwards."
    ),
)
def set_early(args: argparse.Namespace) -> None:  # noqa: D103
    get_pc().ConsoleCommand("set " + " ".join(args.args))


set_early.add_argument(
    "args",
    help="Standard set command arguments",
    # This doesn't do anything cause of the custom splitter, but it looks better in the help text
    nargs=argparse.REMAINDER,
)
