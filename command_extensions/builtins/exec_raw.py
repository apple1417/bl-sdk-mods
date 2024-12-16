import argparse

from mods_base import command, get_pc


@command(
    splitter=lambda m: [m],
    description="Behaves exactly like an 'exec' command, but disables custom command parsing.",
)
def exec_raw(args: argparse.Namespace) -> None:  # noqa: D103
    get_pc().ConsoleCommand("exec " + " ".join(args.args))


exec_raw.add_argument(
    "args",
    help="Standard exec command arguments",
    # This doesn't do anything cause of the custom splitter, but it looks better in the help text
    nargs=argparse.REMAINDER,
)
