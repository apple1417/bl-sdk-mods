import argparse

from mods_base import command, get_pc
from unrealsdk.hooks import prevent_hooking_direct_calls


@command(
    splitter=lambda m: [m.lstrip()],
    description="Behaves exactly like an 'exec' command, but disables custom command parsing.",
)
def exec_raw(args: argparse.Namespace) -> None:  # noqa: D103
    with prevent_hooking_direct_calls():
        get_pc().ConsoleCommand("exec " + " ".join(args.args))


exec_raw.add_argument(
    "args",
    help="Standard exec command arguments",
    # This doesn't do anything cause of the custom splitter, but it looks better in the help text
    nargs=argparse.REMAINDER,
)
