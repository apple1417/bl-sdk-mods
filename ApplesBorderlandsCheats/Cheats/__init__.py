import unrealsdk
import importlib
import inspect
import os
import sys
from abc import ABC, abstractmethod
from functools import cmp_to_key
from typing import Callable, ClassVar, Dict, List, Tuple
from types import ModuleType

from Mods.UserFeedback import ShowHUDMessage
from Mods.ModMenu import Options

SDKHook = Callable[[unrealsdk.UObject, unrealsdk.UFunction, unrealsdk.FStruct], bool]


class ABCCheat(ABC):
    """
    Base class to be inherited from by all cheats.

    Attributes:
        Name: The name of the cheat, mostly used in the presets menu.
        KeybindName: The name of the cheat's keybind.
        CheatOptions:
            A list of options to configure the cheat with. Use of this should generally be avoided,
             in favour of extra cycleable cheat values.
    """
    Name: ClassVar[str]
    KeybindName: ClassVar[str]

    CheatOptions: List[Options.Base] = []

    @abstractmethod
    def OnPress(self) -> None:
        """ Callback method for when the cheat's keybind is pressed. """
        raise NotImplementedError

    def GetHooks(self) -> Dict[str, SDKHook]:
        """
        Gets the hooks the cheat needs to function. These should be bound to your particular
         instance - the hook's behavior should only change if the attributes on the instance it was
         created on are changed.

        Returns:
            A dict mapping unrealscript function names to their hook functions.
        """
        return {}


class ABCCycleableCheat(ABCCheat):
    """
    Base class for cheats with multiple options that the keybind should cycle through.

    Values will be cycled through in the order they are defined.

    Attributes:
        Name: The name of the cheat, mostly used in the presets menu.
        KeybindName: The name of the cheat's keybind.

        AllValues: A tuple of strings listing the various options to cycle through.
        CurrentValue: The value of the option that is currently selected.
    """
    AllValues: ClassVar[Tuple[str, ...]]
    CurrentValue: str = ""

    def __init__(self) -> None:
        if self.CurrentValue == "":
            self.CurrentValue = self.AllValues[0]
        elif self.CurrentValue not in self.AllValues:
            raise ValueError(f"Inital value \"{self.CurrentValue}\" is not in the list of all values.")

    def OnPress(self) -> None:
        idx = (self.AllValues.index(self.CurrentValue) + 1) % len(self.AllValues)
        self.CurrentValue = self.AllValues[idx]

        ShowHUDMessage(self.Name, f"{self.Name}: {self.CurrentValue}")
        self.OnCycle()

    def OnCycle(self) -> None:
        """ Callback method for when the cheat's is cycled. Called after the value is changed. """
        pass


class ABCToggleableCheat(ABCCycleableCheat):
    """
    Base class for cheats that the keybind should just toggle on or off.

    Attributes:
        Name: The name of the cheat, mostly used in the presets menu.
        KeybindName: The name of the cheat's keybind.

        CurrentValue: The value of the option that is currently selected.

        OFF: A predefined string holding the value for when the cheat is off.
        ON: A predefined string holding the value for when the cheat is on.
        AllValues: A predefined tuple of the ON and OFF strings.
        IsOn: A bool value that is True if the cheat is currently on.
    """
    OFF: ClassVar[str] = "Off"
    ON: ClassVar[str] = "On"
    AllValues = (OFF, ON)

    @property
    def IsOn(self) -> bool:
        return self.CurrentValue == self.ON

    @IsOn.setter
    def IsOn(self, val: bool) -> None:
        self.CurrentValue = self.ON if val else self.OFF


ALL_CHEATS: List[ABCCheat] = []
ALL_HOOKS: Dict[str, List[SDKHook]] = {}
ALL_OPTIONS: List[Options.Base] = []


_CURRENT_MODULE = "Mods.ApplesBorderlandsCheats.Cheats"
_dir = os.path.dirname(__file__)
for file in os.listdir(_dir):
    if not os.path.isfile(os.path.join(_dir, file)):
        continue
    if file == "__init__.py":
        continue
    name, suffix = os.path.splitext(file)
    if suffix != ".py":
        continue

    cheat_module: ModuleType
    if f"{_CURRENT_MODULE}.{name}" in sys.modules:
        cheat_module = sys.modules[f"{_CURRENT_MODULE}.{name}"]
        importlib.reload(cheat_module)
    else:
        cheat_module = importlib.import_module(f".{name}", _CURRENT_MODULE)

    for name, cls in inspect.getmembers(cheat_module, inspect.isclass):
        # Filter out classes imported from other modules - incase of inheritence
        if inspect.getmodule(cls) != cheat_module:
            continue
        # I can't use `issubclass()` because these are loaded from different files
        for c in inspect.getmro(cls)[1:]:
            if c.__name__ == ABCCheat.__name__:
                cheat_instance = cls()
                ALL_CHEATS.append(cheat_instance)
                ALL_OPTIONS += cheat_instance.CheatOptions
                for hook, function in cheat_instance.GetHooks().items():
                    if hook in ALL_HOOKS:
                        ALL_HOOKS[hook].append(function)
                    else:
                        ALL_HOOKS[hook] = [function]
                break


# Custom sort, put cycleable cheats first, then toggleable, then bare, sort by name in each group
def _compare_cheats(a: ABCCheat, b: ABCCheat) -> int:
    if isinstance(a, ABCCheat) and not isinstance(a, ABCCycleableCheat):
        if isinstance(b, ABCCheat) and not isinstance(b, ABCCycleableCheat):
            # If A and B are both base cheats, go off of the name
            return -1 if a.Name < b.Name else 1
        else:
            # If A is a base cheat and B is not, B must come first
            return 1
    elif isinstance(a, ABCCycleableCheat) and not isinstance(a, ABCToggleableCheat):
        if isinstance(b, ABCCycleableCheat) and not isinstance(b, ABCToggleableCheat):
            # If A and B are both cycleable cheats, go off of the name
            return -1 if a.Name < b.Name else 1
        else:
            # If A is a cycleable cheat and B is not, A must come first
            return -1
    elif isinstance(a, ABCToggleableCheat):
        if isinstance(b, ABCToggleableCheat):
            # If A and B are both toggleable cheats, go off of the name
            return -1 if a.Name < b.Name else 1
        elif isinstance(b, ABCCycleableCheat):
            # If A is toggleable and B is cycleable, B comes first
            return 1
        else:
            # If A is toggleable and B is a base cheat, A comes first
            return -1


ALL_CHEATS.sort(key=cmp_to_key(_compare_cheats))
