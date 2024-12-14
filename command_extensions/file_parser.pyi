from os import PathLike

class EnableStrategy:
    All: EnableStrategy
    Any: EnableStrategy
    Force: EnableStrategy
    Next: EnableStrategy

    __members__: dict[str, EnableStrategy]

    def __init__(self, value: int) -> None: ...
    def __int__(self) -> int: ...
    def __getstate__(self) -> int: ...
    def __setstate__(self, state: int) -> None: ...
    @property
    def name(self) -> str: ...
    @property
    def value(self) -> int: ...

class BLCMParserError(RuntimeError): ...

def parse(filename: PathLike[str]) -> list[tuple[str, str, int]]:
    """
    Parses custom commands out of mod file.

    Must have called update_commands() first, otherwise this won't match anything.

    Args:
        filename: The file to parse.
    Returns:
        A list of 3-tuples, of the raw command name, the full line, and the command length.
    """

def update_commands(commands: list[str]) -> None:
    """
    Updates the commands which are matched by parse().

    Args:
        commands: The commands to match.
    """
