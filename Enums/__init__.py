import unrealsdk
from enum import IntEnum
from typing import Dict, Tuple

from Mods.ModMenu import ModPriorities, ModTypes, RegisterMod, SDKMod

__version_info__: Tuple[int, ...] = (1, 0)
__version__: str = ".".join(map(str, __version_info__))


_all_enums = {}
for _enum in unrealsdk.FindAll("Enum", True):
    _values = {}
    _idx = 0
    while True:
        _name = _enum.GetEnum(_enum, _idx)
        if _name == "None":
            break
        _values[_name] = _idx
        _idx += 1
    _all_enums[_enum.Name] = IntEnum(_enum.Name, _values)

globals().update(_all_enums)
__all__ = list(_all_enums.keys())


# Provide an entry in the mods list just so users can see that this is loaded
class _Enums(SDKMod):
    Name: str = "Enums"
    Author: str = "apple1417"
    Description: str = (
        "Provides functionality for other mods, but does not do anything by itself."
    )
    Version: str = __version__

    Types: ModTypes = ModTypes.Library
    Priority: ModPriorities = ModPriorities.Library

    Status: str = "<font color=\"#00FF00\">Loaded</font>"
    SettingsInputs: Dict[str, str] = {}


RegisterMod(_Enums())
