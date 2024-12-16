# ruff: noqa: D103

if True:
    assert __import__("mods_base").__version_info__ >= (1, 5), "Please update the SDK"

import argparse
import sys
import traceback
from functools import wraps
from pathlib import Path
from typing import Any, overload

import unrealsdk
from mods_base import AbstractCommand, Library, Mod, build_mod, command, hook
from unrealsdk import logging
from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct

from . import file_parser
from .builtins.chat import chat
from .builtins.clone import clone, clone_dbg_suppress_exists
from .builtins.clone_bpd import clone_bpd
from .builtins.exec_raw import exec_raw
from .builtins.keep_alive import keep_alive
from .builtins.load_package import load_package
from .builtins.pyb import pyb
from .builtins.regen_balance import regen_balance
from .builtins.set_early import set_early
from .builtins.suppress_chat import server_say_hook, suppress_next_chat
from .builtins.unlock_package import unlock_package

# region Public Interface

__version__: str
__version_info__: tuple[int, ...]

__all__: tuple[str, ...] = (
    "__version__",
    "__version_info__",
    "autoregister",
    "deregister",
    "register",
)


def register(cmd: AbstractCommand) -> None:
    """
    Registers a command to be run from inside mod files.

    Args:
        cmd: The command to register.
    """
    name = cmd.cmd.lower()

    # We need to do custom exec handling, can't let people overwrite it
    # Technically overwriting set would work, but it'd be ignored in blcmm files
    if name in {"exec", "set"}:
        raise KeyError(f"You cannot overwrite the '{name}' command!")

    # We don't let you overwrite the two python commands
    if name in command_map or name in {"py", "pyexec"}:
        raise KeyError(f"Command '{name}' already exists!")

    command_map[name] = cmd

    global commands_dirty
    commands_dirty = True


def deregister(cmd: AbstractCommand) -> None:
    """
    Deregisters a command, preventing it being run from inside mod files.

    Args:
        cmd: The command to deregister.
    """
    name = cmd.cmd.lower()

    # Since the two CE commands are implemented inside of the C++ parser, deregistering won't do
    # anything.
    # We don't let you overwrite the two python commands
    if name in {"ce_enableon", "ce_nextcmd", "py", "pyexec"}:
        raise KeyError(f"You cannot deregister the '{name}' command.")

    command_map.pop(name, None)

    global commands_dirty
    commands_dirty = True


@overload
def autoregister(obj: AbstractCommand, /) -> None: ...


@overload
def autoregister(obj: Mod, /) -> None: ...


def autoregister(obj: AbstractCommand | Mod, /) -> None:
    """
    Wraps the enable/disable methods to automatically (de)register commands when called.

    If already enabled when this is called, also immediately registers it.

    Args:
        obj: If a mod, autoregisters all commands currently set on it. If an individual command,
             autoregisters just that command.
    """
    if isinstance(obj, Mod):
        for cmd in mod.commands:
            autoregister(cmd)
        return

    old_enable = obj.enable
    old_disable = obj.disable

    @wraps(obj.enable)
    def new_enable() -> None:
        old_enable()
        register(obj)

    @wraps(obj.disable)
    def new_disable() -> None:
        old_disable()
        deregister(obj)

    obj.enable = new_enable
    obj.disable = new_disable

    if obj.is_registered():
        register(obj)


# endregion
# ==================================================================================================
# region Implementation


EXEC_ROOT = Path(sys.executable).parent.parent
PYEXEC_ROOT = Path(unrealsdk.config.get("pyunrealsdk", {}).get("pyexec_root", ""))

# To match pyunrealsdk, consecutive py commands reuse the same globals
# We choose to clear them for each new exec command however
DEFAULT_PY_GLOBALS: dict[str, Any] = {"unrealsdk": unrealsdk}
py_globals: dict[str, Any] = dict(DEFAULT_PY_GLOBALS)

# If the commands map has changed since we last ran a file, it's dirty, and we'll need to update the
# file parser's commands before executing the next one
commands_dirty: bool = True
command_map: dict[str, AbstractCommand] = {}

debug_logging: bool = False


def parse_exec_command(file_name: str) -> None:
    file_name = file_name.strip()

    if file_name[0] in "'\"" and file_name[0] == file_name[-1]:
        file_name = file_name[1:-1]

    full_path = EXEC_ROOT / file_name
    if not full_path.exists() or not full_path.is_file():
        return
    execute_file(full_path)


def execute_file(file_path: Path) -> None:
    global commands_dirty
    if commands_dirty:
        command_list = list(command_map)
        command_list += ["exec", "py", "pyexec"]
        file_parser.update_commands(command_list)
        commands_dirty = False

    for cmd, line, cmd_len in file_parser.parse(file_path):
        if debug_logging:
            logging.info("[CE]: " + line)

        name = cmd.lower()
        match name:
            case "exec":
                parse_exec_command(line[cmd_len:])

            case "py":
                try:
                    exec(line[cmd_len:].lstrip(), py_globals)  # noqa: S102
                except Exception:  # noqa: BLE001
                    logging.error("Error occured during 'py' command:")
                    logging.error(line)
                    traceback.print_exc()

            case "pyexec":
                try:
                    path = PYEXEC_ROOT / line[cmd_len:].strip()
                    with path.open() as file:
                        # To match pyunrealsdk, each pyexec gets a new empty of globals
                        exec(file.read(), {"__file__": str(path)})  # noqa: S102
                except Exception:  # noqa: BLE001
                    logging.error("Error occured during 'pyexec' command:")
                    logging.error(line)
                    traceback.print_exc()

            case _:
                if name in command_map:
                    command_map[name]._handle_cmd(line, cmd_len)  # pyright: ignore[reportPrivateUsage]


# endregion
# ==================================================================================================
# region Core Builtins


# We can't create a command for the exec handler, since doing so would block using it normally
@hook("Engine.PlayerController:ConsoleCommand")
def exec_command_hook(
    _1: UObject,
    args: WrappedStruct,
    _3: Any,
    _4: BoundFunction,
) -> None:
    command: str = args.Command
    cmd, _, file_name = command.lstrip().partition(" ")
    if cmd != "exec":
        return

    parse_exec_command(file_name)

    # Reset the py command's globals between files
    py_globals.clear()
    py_globals.update(DEFAULT_PY_GLOBALS)


@command(
    "CE_Debug",
    description=(
        "Enables/disables Command Extension debug logging. This logs a copy of each command to be"
        " run, useful for checking that your blcm files are being handled correctly."
    ),
    formatter_class=argparse.RawDescriptionHelpFormatter,
)
def ce_debug(args: argparse.Namespace) -> None:
    global debug_logging
    if args.value == "Enable":
        debug_logging = True
        logging.info("CommandExtensions debug logging enabled")
    elif args.value == "Disable":
        debug_logging = False
        logging.info("CommandExtensions debug logging disabled")
    else:
        logging.error(f"Unrecognised value '{args.value}'")


ce_debug.add_argument("value", type=str.title, choices=("Enable", "Disable"))


@command(
    "CE_EnableOn",
    description="""
Can only be used in BLCMM files.

Changes the strategy used to determine if a custom command is enabled or not. Defaults to 'Any'.
This change applies until the end of the category, or until the next instance of this command. It
*does* recurse into subcategories.

Using each strategy, a custom command is enabled if:
All:   All regular commands in the same category are enabled.
Any:   Any regular command in the same category is enabled.
Force: It is always enabled.
Next:  The next regular command after it (in the same category) is enabled.
"""[1:-1],
    formatter_class=argparse.RawDescriptionHelpFormatter,
)
def ce_enableon(_: argparse.Namespace) -> None:
    logging.error("'CE_EnableOn' can only be used in BLCMM files.")


ce_enableon.add_argument("strategy", type=str.title, choices=file_parser.EnableStrategy.__members__)


@command(
    "CE_NewCmd",
    description=(
        "Can only be used in files.\n"
        "\n"
        "As an optimization, when parsing though a file the known commands are collected all at"
        " once, and only executed after. This means if those commands register new commands, the"
        " new ones aren't yet known and thus won't get collected.\n"
        "\n"
        "This command marks a new command for collection within a mod file. The command MUST still"
        " be registered via normal mechanisms beforehand in order for it to have any effect."
    ),
)
def ce_newcmd(_: argparse.Namespace) -> None:
    logging.error("'CE_NewCmd' can only be used in files.")


ce_newcmd.add_argument("cmd")


# endregion
# ==================================================================================================


mod = build_mod(
    cls=Library,
    commands=(
        ce_debug,
        ce_enableon,
        ce_newcmd,
        chat,
        clone_bpd,
        clone_dbg_suppress_exists,
        clone,
        exec_raw,
        keep_alive,
        load_package,
        pyb,
        regen_balance,
        set_early,
        suppress_next_chat,
        unlock_package,
    ),
    hooks=(
        exec_command_hook,
        server_say_hook,
    ),
)
autoregister(mod)