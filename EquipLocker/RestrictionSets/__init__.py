import unrealsdk
import importlib
import inspect
import os
import sys
from abc import ABC, abstractmethod
from types import ModuleType
from typing import ClassVar, List, Tuple

from Mods.ModMenu import Options


class BaseRestrictionSet(ABC):
    """
    Base class to be inherited from by all restriction sets.

    Attributes:
        Name: The name to use as a header in the options menu.
        Description: The description to use when hoving over this set's header in the options menu.

        UsedOptions: A list of options used to configure the restrictions.

        AllowChoices: A predefined tuple to use as the `Choices` value in boolean options.
    """
    Name: ClassVar[str]
    Description: ClassVar[str]

    UsedOptions: List[Options.Base]

    AllowChoices: ClassVar[Tuple[str, str]] = ("Not Allowed", "Allowed")

    @abstractmethod
    def CanItemBeEquipped(self, item: unrealsdk.UObject) -> bool:
        """ Takes a `WillowInventory`, returns if it can be equipped under current restrictions. """
        raise NotImplementedError


ALL_RESTRICTION_SETS: List[BaseRestrictionSet] = []

_CURRENT_MODULE = "Mods.EquipLocker.RestrictionSets"
_dir = os.path.dirname(__file__)
for file in os.listdir(_dir):
    if not os.path.isfile(os.path.join(_dir, file)):
        continue
    if file == "__init__.py":
        continue
    name, suffix = os.path.splitext(file)
    if suffix != ".py":
        continue

    task: ModuleType
    if f"{_CURRENT_MODULE}.{name}" in sys.modules:
        task = sys.modules[f"{_CURRENT_MODULE}.{name}"]
        importlib.reload(task)
    else:
        task = importlib.import_module(f".{name}", _CURRENT_MODULE)
    # Check all classes in the file - technically you can define more than one
    for _, cls in inspect.getmembers(task, inspect.isclass):
        # Filter out classes imported from other modules
        if inspect.getmodule(cls) != task:
            continue
        # I can't use `issubclass()` because these are loaded from different files
        for c in inspect.getmro(cls)[1:]:
            if c.__name__ == BaseRestrictionSet.__name__:
                ALL_RESTRICTION_SETS.append(cls())
                break
