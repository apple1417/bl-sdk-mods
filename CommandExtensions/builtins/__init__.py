import unrealsdk
import importlib
import os
import re
import shlex
from typing import List, Optional, Tuple

__all__: Tuple[str, ...] = (
    "is_obj_instance",
    "obj_name_splitter",
    "parse_object",
    "re_object_name",
)

"""
Regex matching an object name.

Group Name | Contents
:----------|:---------
`class`    | The object's class name, if specified.
`fullname` | The object's full path.
`outer`    | The full path to the outer object, if there is one.
`name`     | The object's name.
"""
re_obj_name = re.compile(
    r"^((?P<class>[\w?+!,'\"\\\-]+?)')?(?P<fullname>((?P<outer>[\w.:?+!,'\"\\\-]+)[.:])?(?P<name>[\w?+!,'\"\\\-]+))(?(class)'|)$",
    flags=re.I
)


def obj_name_splitter(args: str) -> List[str]:
    """
    Custom argument splitter that returns object names as single tokens.

    Note that this makes the splitting less versatile - quoting is completely gone for example.

    Args:
        args: A string of arguments
    Returns:
        A list of individual arguments split out from the input string.
    """
    lex = shlex.shlex(args)
    lex.wordchars += ".:?+!,'\"\\-"
    lex.quotes = ""
    lex.whitespace_split = True
    return list(lex)


def parse_object(name: str) -> Optional[unrealsdk.UObject]:
    """
    Given an object name, returns the object.

    If it's unable to parse or find the object, logs an error to console and returns None.

    Args:
        name: The object name to look for
    Returns:
        The parsed object, or None on error.
    """
    match = re_obj_name.match(name)
    if match is None:
        unrealsdk.Log(f"Unable to parse object name {name}")
        return None

    class_ = match.group("class") or "Object"
    fullname = match.group("fullname")
    obj = unrealsdk.FindObject(class_, fullname)
    if obj is None:
        unrealsdk.Log(f"Unable to find object {name}")
        return None
    return obj


def is_obj_instance(obj: unrealsdk.UObject, cls: str) -> bool:
    """
    Checks if an object is an instance of a given class - including base classes.

    Args:
        obj: The object to check.
        cls: The name of the class to look for.
    """
    current = obj.Class
    while current is not None:
        if current.Name == cls:
            return True
        current = current.SuperField
    return False


# Import all files in this directory - we want the side effects (which register everything)
_dir = os.path.dirname(__file__)
for file in os.listdir(_dir):
    if not os.path.isfile(os.path.join(_dir, file)):
        continue
    if file == "__init__.py":
        continue
    name, suffix = os.path.splitext(file)
    if suffix != ".py":
        continue

    importlib.import_module("." + name, __name__)
del _dir, file
