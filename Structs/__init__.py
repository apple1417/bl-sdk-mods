import unrealsdk
from collections import namedtuple
from functools import wraps
from typing import TYPE_CHECKING, Any, Dict, NamedTuple, Set, Tuple, Type

from Mods.ModMenu import ModPriorities, ModTypes, RegisterMod, SDKMod

__version_info__: Tuple[int, ...] = (1, 1)
__version__: str = ".".join(map(str, __version_info__))


# The default value to use for each property type
_PROP_DEFAULTS_BY_TYPE: Dict[str, Any] = {
    # Deliberately ignoring "StructProperty", to give it more complex initalization later
    "StrProperty": "",
    "ObjectProperty": None,
    "ComponentProperty": None,
    "ClassProperty": None,
    "NameProperty": "",
    "InterfaceProperty": None,
    "DelegateProperty": None,
    "FloatProperty": 0.0,
    "IntProperty": 0,
    "ByteProperty": 0,
    "BoolProperty": False,
    "ArrayProperty": [],
}


"""
The SDK currently cannot read FNames with a number. This causes problems for the few structs which
 have fields with duplicate names, but different numbers - we can't create a named tuple with
 duplicates.

Since it's a small amount, just hardcode the actual field names (by index) for these structs.

We will still have problems with the FStruct constructor, as we can't read these other field names
 off the object. Doesn't seem to be a good way around this without a fix in the sdk itself.
"""
_KNOWN_FIELD_OVERRIDES: Dict[str, Dict[int, str]] = {
    "LightingChannelContainer": {
        6: "Unnamed_1",
        7: "Unnamed_2",
        8: "Unnamed_3",
        9: "Unnamed_4",
        10: "Unnamed_5",
        11: "Unnamed_6",
        12: "Cinematic_1",
        13: "Cinematic_2",
        14: "Cinematic_3",
        15: "Cinematic_4",
        16: "Cinematic_5",
        17: "Cinematic_6",
        18: "Cinematic_7",
        19: "Cinematic_8",
        20: "Cinematic_9",
        21: "Cinematic_10",
        22: "Gameplay_1",
        23: "Gameplay_2",
        24: "Gameplay_3",
        25: "Gameplay_4",
    },
    "NxDestructibleDepthParameters": {
        5: "USER_FLAG_1",
        6: "USER_FLAG_2",
        7: "USER_FLAG_3",
    },
    "TurnData": {
        1: "Left_45",
        2: "Right_45",
        3: "Left_90",
        4: "Right_90",
        5: "Left_180",
        6: "Right_180",
    },
}


_all_structs: Dict[str, Type[Tuple[Any, ...]]] = {}
_known_duplicate_names: Set[str] = set()


def _get_struct_name(struct: unrealsdk.UStruct) -> str:
    """
    Gets the name to use for this struct.

    Will use the base name if it's unique, otherwise prefixes with the outer object name and an
     underscore - e.g. `NavigationPoint_CheckpointRecord`.

    Args:
        struct: The struct to get the name of.
    Returns:
        The struct's name.
    """
    name: str = struct.Name
    while struct.Name in _known_duplicate_names:
        # Deliberately not error checking this, so that we'll get an exception if we somehow come
        #  across two different structs with identical name
        struct = struct.Outer
        name = struct.Name + "_" + name
    return name


def _define_struct(struct: unrealsdk.UStruct) -> None:
    """
    Defines a named tuple for the given struct.

    Does nothing if it already exists.

    Args:
        struct: The struct to create a named tuple of.
    """
    # Check for a duplicate name
    if struct.Name in _all_structs:
        if _all_structs[struct.Name]._unreal == struct:  # type: ignore
            return
        _known_duplicate_names.add(struct.Name)
        other_struct = _all_structs[struct.Name]._unreal  # type: ignore
        del _all_structs[struct.Name]
        _define_struct(other_struct)

    # Check if we've already been created
    # Deliberately not using elif, in case the previous call created this struct
    if _get_struct_name(struct) in _all_structs:
        return

    fields = []
    defaults = []

    # Technically, some structs inherit others (e.g. Plane2D), we should also loop over superfield
    # The SDK struct setter does not do this though, so copying it

    prop = struct.Children
    while prop:
        fields.append(prop.Name)

        # If the field is a struct, import the actual namedtuple as the default
        # Since there can't be an infinite loop of nested structs, we will always eventually
        #  find our way to a struct which has no struct fields
        if prop.Class.Name == "StructProperty":
            nested_struct = prop.GetStruct()
            if _get_struct_name(struct) not in _all_structs:
                _define_struct(nested_struct)
            defaults.append(_all_structs[nested_struct.Name]())
        else:
            defaults.append(_PROP_DEFAULTS_BY_TYPE[prop.Class.Name])

        prop = prop.Next

    name = _get_struct_name(struct)
    for idx, actual_field in _KNOWN_FIELD_OVERRIDES.get(name, {}).items():
        fields[idx] = actual_field

    tup = namedtuple(name, fields, defaults=defaults)  # type: ignore
    tup._unreal = struct  # type: ignore

    # Replace the new method with one that converts fstructs
    old_new = tup.__new__

    def convert_fstruct(
        fstruct: unrealsdk.FStruct,
        field_error: str,
        expected_type: Type[Any],
    ) -> NamedTuple:
        """
        Helper function which converts an FStruct into it's named tuple.

        Args:
            fstruct: The FStruct to convert.
            field: The name of the field this struct was extracted from, used for error messages.
            expected_type: The type this field was expected to be.
        Returns:
            The named tuple representation of the given FStruct.
        """
        # Only being strict about the typing of fstructs, since we need to parse them
        # The sdk can handle other invalid types
        if not issubclass(expected_type, tuple):
            raise TypeError(
                f"Got a struct '{struct.PathName(fstruct.structType)}' to field '{field_error}',"
                f" expected '{expected_type.__name__}'!"
            )
        if fstruct.structType != expected_type._unreal:  # type: ignore
            raise TypeError(
                f"Got struct of incompatible type '{struct.PathName(fstruct.structType)}' to"  # type: ignore
                f" field '{field_error}', expected '{struct.PathName(expected_type._unreal)}'!"
            )

        return expected_type(fstruct)  # type: ignore

    def convert_arg(arg: Any, field_error: str) -> Any:
        """
        Helper function to handle FArray, FStruct and FScriptInterface arguments.

        Recursively converts and FArray into an array.
        Converts an FStruct arg into a named tuple.
        Changes an FScriptInterface into the ObjectPointer of that FScriptInterface

        Args:
            arg: The Argument to handle.
            field_error: The name of the field this struct was extracted from, used for error
                         messages.
        Returns:
            The new argument.
        """
        if isinstance(arg, unrealsdk.FArray):
            return [convert_arg(a, f"{field_error}[{idx}]") for idx, a in enumerate(arg)]
        if isinstance(arg, unrealsdk.FStruct):
            return convert_fstruct(arg, field_error, _all_structs[_get_struct_name(arg.structType)])
        if isinstance(arg, unrealsdk.FScriptInterface):
            return arg.ObjectPointer
        return arg

    @wraps(old_new)
    def new(cls: Type[NamedTuple], *args: Any, **kwargs: Any) -> NamedTuple:
        # If we have a single fstruct arg of our type, expand it into it's fields
        if len(args) == 1 and len(kwargs) == 0 and isinstance(args[0], unrealsdk.FStruct):
            try:
                if args[0].structType == struct:
                    args = [getattr(args[0], field) for field in fields]  # type: ignore
            except AttributeError as ex:
                unrealsdk.Log(ex)

        # Expand any nested fstructs
        args = [
            convert_arg(val, fields[idx])
            for idx, val in enumerate(args)
        ]
        kwargs = {
            key: (
                convert_arg(val, key)
                if key in fields else
                # If we have an invalid keyword arg, let the base __new__ deal with it
                val
            )
            for key, val in kwargs.items()
        }

        return old_new(cls, *args, **kwargs)  # type: ignore

    tup.__new__ = new  # type: ignore

    _all_structs[name] = tup


for _struct in unrealsdk.FindAll("ScriptStruct", True):
    _define_struct(_struct)


globals().update(_all_structs)
__all__ = list(_all_structs.keys())


if TYPE_CHECKING:
    def __getattr__(name: str) -> NamedTuple:
        raise NotImplementedError


# Provide an entry in the mods list just so users can see that this is loaded
class _Structs(SDKMod):
    Name: str = "Structs"
    Author: str = "apple1417"
    Description: str = (
        "Provides functionality for other mods, but does not do anything by itself."
    )
    Version: str = __version__

    Types: ModTypes = ModTypes.Library
    Priority: ModPriorities = ModPriorities.Library

    Status: str = "<font color=\"#00FF00\">Loaded</font>"
    SettingsInputs: Dict[str, str] = {}


RegisterMod(_Structs())
