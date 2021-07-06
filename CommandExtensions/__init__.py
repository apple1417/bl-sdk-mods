import unrealsdk
import argparse
import html
import re
import shlex
import sys
import traceback
import xml.etree.ElementTree as et
from enum import Enum, auto
from os import path
from typing import Any, Callable, Dict, IO, List, NoReturn, Optional, Set, Tuple, cast

from Mods.ModMenu import ModPriorities, ModTypes, RegisterMod, SDKMod
import Mods

__all__: Tuple[str, ...] = (
    "CommandCallback",
    "RegisterConsoleCommand",
    "SplitterFunction",
    "UnregisterConsoleCommand"
    "VersionMajor",
    "VersionMinor",
)

VersionMajor: int = 1
VersionMinor: int = 5

CommandCallback = Callable[[argparse.Namespace], None]
SplitterFunction = Callable[[str], List[str]]

DEBUG_LOGGING: bool = False

native_path = path.join(path.dirname(__file__), "Native")
if native_path not in sys.path:
    sys.path.append(native_path)


class ConsoleArgParser(argparse.ArgumentParser):
    """
    A small ArgumentParser wrapper.

    Fixes two small issues with using these objects with the SDK:
    1. `prog` now defaults to the empty string instead of reading from `sys.argv` (which is empty).
    2. It prints to console instead of stderr/stdout (which are None).

    Also has an extra small tweak useful for our specific case: It raises a `_ParsingFailedError`
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


class EnableStrategy(Enum):
    """ The various enable strategies we might use when parsing BLCMM files. """
    All = auto()
    Any = auto()
    Force = auto()
    Next = auto()


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
    # Technically overwriting set would work, but only from console, in blcmm files it's different
    if name in ("exec", "set"):
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

    # We use a custom parser for enableon anyway
    # The sdk py commands use a different hook we can't affect
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
    lambda args: unrealsdk.Log("ERROR: 'CE_EnableOn' can only be used in BLCMM files."),  # type: ignore
    description="""
Can only be used in BLCMM files.

Changes the strategy used to determine if custom command is enabled or not. Defaults to 'Any'.
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
    choices=EnableStrategy.__members__
)


def try_parse_strategy(cmd: Optional[str]) -> Optional[EnableStrategy]:
    """
    Takes in a string, and, if it's a 'CE_EnableOn' command, returns the new enable strategy.
    This is a special command only using during parsing blcmm files, so the callback just returns an
    error message, we need a seperate function to parse it ourselves.
    """
    if cmd is None:
        return None

    name, _, cmd_args = cmd.partition(" ")
    if name.lower() == "ce_enableon":
        try:
            args = enable_on_parser.parse_args(shlex.split(cmd_args))
            return EnableStrategy.__members__.get(args.strategy)
        except (ParsingFailedError, SystemExit):
            pass
    return None


# For some bizzare reason blcmm basically doesn't escape text anywhere
# The closest thing is that quotes in attributes are escaped using `\"`
# A few regexes and some manual html escaping fix this for us
blcm_escape_patterns: Set[re.Pattern] = {  # type: ignore
    re.compile(
        r"((?P<code><code profiles=\".*?\">)|<comment>)(?P<escape>.*?)(?(code)</code>|</comment>)",
        flags=re.I
    ),
    re.compile(
        r"(current|level|name|offline|package|profiles|v|mut|lock)=\"(?P<escape>(\\\"|[^\"])*)\"",
        flags=re.I
    )
}


def parse_blcmm_file(file: IO[str]) -> et.Element:
    """ Parses an open blcmm file object and returns an ET Element (roughly) containing it. """
    parser = et.XMLParser()
    for line in file:
        # Stop before trying to parse the lines after the end of the xml
        if line.startswith("</BLCMM>"):
            parser.feed(line)
            break
        # The filtertool warning isn't valid xml
        if line.startswith("#<!!!"):
            continue
        # Deal with the lack of escaping
        for pattern in blcm_escape_patterns:
            match = re.search(pattern, line)
            if match is None:
                continue
            base = match.group("escape")
            escaped = html.escape(base)
            line = line.replace(base, escaped, 1)
        parser.feed(line)
    return cast(et.Element, parser.close())


def handle_blcmm_file(file: IO[str]) -> None:
    """ Handles any custom commands within the provided blcmm file object. """
    root = parse_blcmm_file(file)

    profile = root.find("./head/profiles/profile[@name][@current='true']")
    profile_name = "default" if profile is None else profile.get("name")

    def is_enabled(code: et.Element) -> bool:
        """ Returns if an xml code element is enabled. """
        return profile_name in code.get("profiles", "").split(",")

    def handle_category(category: et.Element, strategy: EnableStrategy) -> None:
        """ Recursively handles all custom commands in a category. """
        # Split all children into groups based on the enable strategy we're using for them
        strategy_groups: List[Tuple[List[et.Element], EnableStrategy]] = []

        last_strategy = strategy
        last_change_idx = 0
        all_children = list(category)
        for idx, child in enumerate(category):
            if child.tag == "hotfix":
                all_children[idx + 1:idx + 1] = list(child)
                continue
            elif child.tag == "comment":
                new_strategy = try_parse_strategy(child.text)
                if new_strategy is None:
                    continue
                strategy_groups.append((
                    # Exclude this child element
                    all_children[last_change_idx:idx],
                    last_strategy
                ))
                last_strategy = new_strategy
                last_change_idx = idx + 1
        strategy_groups.append((
            all_children[last_change_idx:],
            last_strategy
        ))

        for group, strategy in strategy_groups:
            if strategy is EnableStrategy.All:
                handle_group_all(group)
            elif strategy is EnableStrategy.Any:
                handle_group_any(group)
            elif strategy is EnableStrategy.Force:
                handle_group_force(group)
            elif strategy is EnableStrategy.Next:
                handle_group_next(group)

    def handle_group_all(group: List[et.Element]) -> None:
        enabled = True
        comments: List[str] = []
        for child in group:
            if child.tag == "category":
                handle_category(child, EnableStrategy.All)

            elif child.tag == "code" and not is_enabled(child):
                enabled = False
                comments = []

            elif enabled and child.tag == "comment" and child.text is not None:
                comments.append(child.text)

        for comment in comments:
            try_handle_command(comment)

    def handle_group_any(group: List[et.Element]) -> None:
        enabled = False
        inital_comments: List[str] = []
        for child in group:
            if child.tag == "category":
                handle_category(child, EnableStrategy.Any)

            elif not enabled and child.tag == "code" and is_enabled(child):
                enabled = True
                for comment in inital_comments:
                    try_handle_command(comment)

            elif child.tag == "comment" and child.text is not None:
                if enabled:
                    try_handle_command(child.text)
                else:
                    inital_comments.append(child.text)

    def handle_group_force(group: List[et.Element]) -> None:
        for child in group:
            if child.tag == "category":
                handle_category(child, EnableStrategy.Force)

            elif child.tag == "comment" and child.text is not None:
                try_handle_command(child.text)

    def handle_group_next(group: List[et.Element]) -> None:
        cached_comments: List[str] = []
        for child in group:
            if child.tag == "category":
                handle_category(child, EnableStrategy.Next)

            elif child.tag == "comment" and child.text is not None:
                cached_comments.append(child.text)
                continue

            elif child.tag == "code":
                if is_enabled(child):
                    for comment in cached_comments:
                        try_handle_command(comment)
                cached_comments = []

    root_category = root.find("./body/category")
    if root_category is not None:
        handle_category(root_category, EnableStrategy.Any)


exec_globals = {"unrealsdk": unrealsdk, "Mods": Mods}


def try_handle_command(cmd: str) -> bool:
    """
    Takes in a command string `cmd` and tries to handle it.

    Returns:
        True if the command string corosponded to one of our custom commands, or False otherwise.
    """
    name, _, args = cmd.partition(" ")
    name = name.lower()

    if name == "exec":
        try:
            file_path = args.strip()
            if file_path[0] == "\"" and file_path[-1] == "\"":
                file_path = file_path[1:-1]
            full_path = path.abspath(path.join(path.dirname(sys.executable), "..", file_path))
            if not path.isfile(full_path):
                return False

            with open(full_path) as file:
                firstline = file.readline().strip()
                file.seek(0)

                # Handle it as a blcm file if we can
                if firstline.startswith("<BLCMM"):
                    handle_blcmm_file(file)
                    return False

                # Otherwise treat each line as it's own command
                for line in file:
                    try_handle_command(line)

        except (ParsingFailedError, SystemExit):
            pass
        return False
    elif name not in parser_callback_map:
        return False

    if DEBUG_LOGGING:
        unrealsdk.Log("[CE]: " + cmd)

    # The sdk hooks an earlier function than we do for these commands, so we'll only fall into these
    #  when running from file
    if name == "py":
        try:
            exec(args, exec_globals)
        except Exception:
            unrealsdk.Log(traceback.format_exc())
        return True
    elif name == "pyexec":
        with open(path.abspath(path.join(path.dirname(sys.executable), args))) as file:
            try:
                exec(file.read(), exec_globals)
            except Exception:
                unrealsdk.Log(traceback.format_exc())
        return True

    parser, callback, splitter = parser_callback_map[name]
    try:
        callback(parser.parse_args(splitter(args)))
    except ParsingFailedError as ex:
        ex.log()
    except SystemExit:
        pass
    except Exception:
        unrealsdk.Log(traceback.format_exc())

    return True


def console_command_hook(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
    return not try_handle_command(params.Command)


unrealsdk.RegisterHook("Engine.PlayerController.ConsoleCommand", __name__, console_command_hook)


# load our builtin commands
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
