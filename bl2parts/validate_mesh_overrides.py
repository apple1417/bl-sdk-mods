import unrealsdk
import importlib
import os
import re
import sys
from typing import Iterator, List, Optional, Tuple

try:
    raise NotImplementedError
except NotImplementedError:
    __file__ = sys.exc_info()[-1].tb_frame.f_code.co_filename  # type: ignore

if os.path.dirname(__file__) not in sys.path:
    sys.path.append(os.path.dirname(__file__))


if "tools.data" in sys.modules:
    importlib.reload(sys.modules["tools.data"])

from tools.data import MESH_OVERRIDES

"""
Part meshes are `name` fields. The SDK doesn't read these correctly, it drops the number. This
 script checks that our mesh overrides cover all cases where this happends.

To extract the actual value, we need to manually run console commands. This is a seperate script to
 avoid these drowing out errors.
"""

RE_OBJ_SPLIT: re.Pattern = re.compile("[.:]")  # type: ignore
MAX_SCROLLBACK_SIZE: int = 1024


def iter_console_lines() -> Iterator[str]:
    """ Iterates through lines in console, most recent first. """
    console = unrealsdk.GetEngine().GameViewport.ViewportConsole

    # SBHead points to the current line
    # If we haven't filled the scrollback yet, `SBHead + 1` will IndexError, which then tells us the
    #  actual scrollback size
    scrollback_size = MAX_SCROLLBACK_SIZE
    try:
        console.Scrollback[console.SBHead + 1]
    except IndexError:
        scrollback_size = console.SBHead + 1

    idx = console.SBHead
    end_idx = (console.SBHead + 1) % scrollback_size
    while idx != end_idx:
        line = console.Scrollback[idx]
        if line:
            yield line
        idx = (idx - 1) % scrollback_size


def get_console_property(obj: unrealsdk.UObject, prop: str) -> Optional[str]:
    """
    Gets the value of a property as it appears in console dumps.

    Actually dumps the object and reads the value from console - will spam it if you use it a lot.

    Args:
        obj: The object to get a value on.
        prop: The name of the property to search for.
    Returns:
        The value of the property, in a string
    """
    name = RE_OBJ_SPLIT.split(obj.PathName(obj))[-1]
    cmd = f"getall {obj.Class.Name} {prop} Name={name}"
    pattern = re.compile(f"^\\d+\\) {obj.Class.Name} {obj.PathName(obj)}.{prop} = (.+)$")

    unrealsdk.GetEngine().GamePlayers[0].Actor.ConsoleCommand(cmd)

    for line in iter_console_lines():
        match = pattern.match(line)
        if match:
            return match.group(1)
        elif line == cmd:
            return None
    return None


not_in_overrides: List[Tuple[unrealsdk.UObject, Optional[str], str]] = []  # part, real mesh, sdk mesh
mistakenly_in_overrides: List[Tuple[unrealsdk.UObject, Optional[str]]] = []  # part, real mesh


for part in unrealsdk.FindAll("WillowInventoryPartDefinition", True):
    sdk_value = part.GestaltModeSkeletalMeshName
    if sdk_value in ("", "None", None):
        sdk_value = None

    real_value = get_console_property(part, "GestaltModeSkeletalMeshName")
    if real_value == "None":
        real_value = None

    if real_value != sdk_value:
        if part not in MESH_OVERRIDES or MESH_OVERRIDES[part] != real_value:
            not_in_overrides.append((part, real_value, sdk_value))
    else:
        if part in MESH_OVERRIDES:
            mistakenly_in_overrides.append((part, real_value))

unrealsdk.Log("=== RESULTS: ===")
unrealsdk.Log("Parts not in mesh overrides:")
for part, real, sdk in not_in_overrides:
    unrealsdk.Log(f"'{part.PathName(part)}'  Real Mesh: '{real}', SDK Mesh: '{sdk}'")

unrealsdk.Log("Parts mistakenly in mesh overrides:")
for part, real in mistakenly_in_overrides:
    unrealsdk.Log(
        f"'{part.PathName(part)}'  Real Mesh: '{real}', Override: '{MESH_OVERRIDES[part]}'"
    )
