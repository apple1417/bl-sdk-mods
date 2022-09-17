import unrealsdk
from enum import IntEnum
from typing import TYPE_CHECKING, Dict, Set, Tuple, Type

from Mods.ModMenu import ModPriorities, ModTypes, RegisterMod, SDKMod

__version_info__: Tuple[int, ...] = (1, 1)
__version__: str = ".".join(map(str, __version_info__))


_all_enums: Dict[str, Type[IntEnum]] = {}
_known_duplicate_names: Set[str] = set()


def _get_enum_name(enum: unrealsdk.UObject) -> str:
    """
    Gets the name to use for this enum.

    Will use the base name if it's unique, otherwise prefixes with the outer object name and an
     underscore - e.g. `NavigationPoint_CheckpointRecord`.

    Args:
        enum: The enum to get the name of.
    Returns:
        The enum's name.
    """
    name: str = enum.Name
    while enum.Name in _known_duplicate_names:
        # Deliberately not error checking this, so that we'll get an exception if we somehow come
        #  across two different structs with identical name
        enum = enum.Outer
        name = enum.Name + "_" + name
    return name


def _define_enum(enum: unrealsdk.UObject) -> None:
    """
    Defines an IntEnum for the given unreal enum.

    Does nothing if it already exists.

    Args:
        enum: The unreal enum to create an IntEnum of.
    """
    # Check for a duplicate name
    if enum.Name in _all_enums:
        if _all_enums[enum.Name]._unreal == enum:  # type: ignore
            return
        _known_duplicate_names.add(enum.Name)
        other_enum = _all_enums[enum.Name]._unreal  # type: ignore
        del _all_enums[enum.Name]
        _define_enum(other_enum)
    elif _get_enum_name(enum) in _all_enums:
        return

    values = {}
    idx = 0
    while True:
        val_name = enum.GetEnum(enum, idx)
        if val_name == "None":
            break
        values[val_name] = idx
        idx += 1

    int_enum = IntEnum(_get_enum_name(enum), values)  # type: ignore
    int_enum._unreal = enum  # type: ignore

    _all_enums[_get_enum_name(enum)] = int_enum


for _enum in unrealsdk.FindAll("Enum", True):
    _define_enum(_enum)


globals().update(_all_enums)
__all__ = list(_all_enums.keys())

if TYPE_CHECKING:
    class UnrealScriptEnum(type):
        def __getattr__(cls, name: str) -> IntEnum:
            raise NotImplementedError

    def __getattr__(name: str) -> UnrealScriptEnum:
        raise NotImplementedError


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
