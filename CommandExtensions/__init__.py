import unrealsdk
import argparse
import shlex
import sys
import traceback
from os import path
from typing import Any, Callable, Dict, IO, List, NoReturn, Optional, Tuple

from Mods.ModMenu import ModPriorities, ModTypes, RegisterMod, SDKMod
import Mods

from . import file_parser

__all__: Tuple[str, ...] = (
    "CommandCallback",
    "RegisterConsoleCommand",
    "SplitterFunction",
    "UnregisterConsoleCommand"
    "VersionMajor",
    "VersionMinor",
)

VersionMajor: int = 1
VersionMinor: int = 8

CommandCallback = Callable[[argparse.Namespace], None]
SplitterFunction = Callable[[str], List[str]]

DEBUG_LOGGING: bool = False


class ConsoleArgParser(argparse.ArgumentParser):
    """
    A small ArgumentParser wrapper.

    Fixes two small issues with using these objects with the SDK:
    1. `prog` now defaults to the empty string instead of reading from `sys.argv` (which is empty).
    2. It prints to console instead of stderr/stdout (which are None).

    Also has an extra small tweak useful for our specific case: It raises a `ParsingFailedError`
    rather than a generic `SystemExit` when parsing fails, which we can catch to suppress logs.
    """
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        if "prog" not in kwargs:
            kwargs["prog"] = ""

        super().__init__(*args, **kwargs)

    def _print_message(self, message: str, file: Optional[IO[str]] = None) -> None:
        if message and file is None:
            unrealsdk.Log(message)
        else:
            super()._print_message(message, file)

    def error(self, message: str) -> NoReturn:
        raise ParsingFailedError(self, message)


class ParsingFailedError(Exception):
    """ Small helper exception we use to detect failed parsing. """
    parser: ConsoleArgParser
    message: str

    def __init__(self, parser: ConsoleArgParser, message: str) -> None:
        super().__init__(message)
        self.parser = parser
        self.message = message

    def log(self, name_override: Optional[str] = None) -> None:
        """ Prints the equivalent of what `parser.error()` normally would to console. """
        self.parser.print_usage()
        unrealsdk.Log(f"{self.parser.prog}: error: {self.message}\n")


parser_callback_map: Dict[str, Tuple[ConsoleArgParser, CommandCallback, SplitterFunction]] = {}


def RegisterConsoleCommand(
    name: str,
    callback: CommandCallback,
    *,
    splitter: SplitterFunction = shlex.split,
    **kwargs: Any
) -> argparse.ArgumentParser:
    """
    Registers a new console command. This is a small wrapper around `argparse.ArgumentParser`.

    Args:
        name:
            The name of the console command; the leftmost part of what you type. May not include
            spaces.
        callback:
            A function run whenever your command is successfully parsed, which accepts the parsed
            `Namespace` object.
        splitter:
            A function that splits a full argument string into a list of strings to be passed to the
            `ArgumentParser`. Defaults to `shlex.split()`.
        **kwargs:
            Any other arguments to pass through to the underlying `ArgumentParser` constructor.
    Returns:
        An `ArgumentParser` object you can use to configure your command's arguments.
    """
    if "prog" not in kwargs:
        kwargs["prog"] = name

    name = name.lower()
    if name in parser_callback_map:
        raise KeyError(f"A command with name '{name}' already exists!")
    if " " in name:
        raise ValueError(f"Command name '{name}' cannot include spaces!")

    # We need to do custom exec handling, can't let people overwrite it
    # Technically overwriting set would work, but only from console, for files it's ignored
    # We don't let you remove the python commands, so can't let you register them in the first place
    # While we don't let you remove ce_enableon, we do register that command normally
    if name in ("exec", "set", "py", "pyexec"):
        raise KeyError(f"You cannot overwrite the '{name}' command!")

    parser = ConsoleArgParser(**kwargs)
    parser_callback_map[name] = (parser, callback, splitter)

    return parser


def UnregisterConsoleCommand(name: str, *, allow_missing: bool = False) -> None:
    """
    Removes a previously registered console command.

    Args:
        name: The name of the console command to remove.
        allow_missing: Don't throw an exception if the command hasn't been registed yet.
    """
    name = name.lower()

    # These all only exist in c++ where we can't actually affect them
    # We do have a local ce_enableon, but it's only used to print errors in console
    if name in ("ce_enableon", "py", "pyexec"):
        raise KeyError(f"You cannot unregister the '{name}' command.")

    if name not in parser_callback_map:
        if allow_missing:
            return
        else:
            raise KeyError(f"No command with name '{name}' has been registered.")

    del parser_callback_map[name]


def debug_handler(args: argparse.Namespace) -> None:
    global DEBUG_LOGGING
    if args.value == "Enable":
        DEBUG_LOGGING = True
    elif args.value == "Disable":
        DEBUG_LOGGING = False
    else:
        unrealsdk.Log(f"Unrecognised value '{args.value}'")


debug_parser = RegisterConsoleCommand(
    "CE_Debug",
    debug_handler,
    description=(
        "Enables/disables Command Extension debug logging. This logs a copy of each command to be"
        " run, useful for checking that your blcm files are being handled correctly."
    )
)
debug_parser.add_argument(
    "value",
    type=str.title,
    choices=("Enable", "Disable")
)


enable_on_parser = RegisterConsoleCommand(
    "CE_EnableOn",
    lambda _: unrealsdk.Log("ERROR: 'CE_EnableOn' can only be used in BLCMM files."),  # type: ignore
    description="""
Can only be used in BLCMM files.

Changes the strategy used to determine if a custom command is enabled or not. Defaults to 'Any'.
This change applies until the end of the category, or until the next instance of this command.

Using each strategy, a custom command is enabled if:
All:   All regular commands in the same category are enabled.
Any:   Any regular command in the same category is enabled.
Force: It is always enabled.
Next:  The next regular command after it (in the same category) is enabled.
"""[1:-1],
    formatter_class=argparse.RawDescriptionHelpFormatter
)
enable_on_parser.add_argument(
    "strategy",
    type=str.title,
    choices=file_parser.EnableStrategy.__members__
)


pyexec_globals = {"unrealsdk": unrealsdk, "Mods": Mods}


def log_traceback() -> None:
    """
    Prints the current exception traceback to the sdk log.
    """
    for line in traceback.format_exc().split('\n'):
        unrealsdk.Log(line)


def try_handle_command(cmd: str, args: str) -> bool:
    """
    Tries to handle the given command.

    Args:
        cmd: The command name
        args: The command's arguments
    Returns:
        True if the command string corosponded to one of our custom commands, or False otherwise.
        Returns True for `py` and `pyexec` commands, and False for `exec` commands.
    """
    cmd = cmd.lower()
    known_cmds = set(parser_callback_map).union({"exec", "py", "pyexec"})

    if cmd == "exec":
        file_path = args.strip()
        if file_path[0] == "\"" and file_path[-1] == "\"":
            file_path = file_path[1:-1]
        full_path = path.abspath(path.join(path.dirname(sys.executable), "..", file_path))
        if not path.isfile(full_path):
            return False

        try:
            for file_cmd, file_args in file_parser.parse(full_path, known_cmds):
                try_handle_command(file_cmd, file_args)

        except file_parser.ParserError:
            log_traceback()
        return False
    elif cmd not in known_cmds:
        return False

    if DEBUG_LOGGING:
        unrealsdk.Log(f"[CE]: {cmd} {args}")

    # The sdk hooks an earlier function than we do for these two commands, so we'll only fall into
    #  these when running from file
    if cmd == "py":
        try:
            exec(args, pyexec_globals)
        except Exception:
            log_traceback()
    elif cmd == "pyexec":
        with open(path.abspath(path.join(path.dirname(sys.executable), args))) as file:
            try:
                exec(file.read(), pyexec_globals)
            except Exception:
                log_traceback()

    else:
        parser, callback, splitter = parser_callback_map[cmd]
        try:
            callback(parser.parse_args(splitter(args)))
        except ParsingFailedError as ex:
            ex.log()
        except SystemExit:
            pass
        except Exception:
            log_traceback()

    return True


def console_command_hook(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
    cmd, _, args = params.Command.partition(" ")
    return not try_handle_command(cmd, args)


unrealsdk.RegisterHook("Engine.PlayerController.ConsoleCommand", __name__, console_command_hook)


# Load our builtin commands
from . import builtins  # noqa: F401, E402


# Provide an entry in the mods list just so users can see that this is loaded
class CommandExtensions(SDKMod):
    Name: str = "Command Extensions"
    Author: str = "apple1417"
    Description: str = (
        "Adds a few new console commands, and provides functionality for other mods to do the same."
    )
    Version: str = f"{VersionMajor}.{VersionMinor}"

    Types: ModTypes = ModTypes.Library
    Priority = ModPriorities.Library

    Status: str = "<font color=\"#00FF00\">Loaded</font>"
    SettingsInputs: Dict[str, str] = {}


RegisterMod(CommandExtensions())
