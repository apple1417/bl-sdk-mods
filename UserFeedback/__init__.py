from typing import Dict

from Mods.ModMenu import ModPriorities, ModTypes, RegisterMod, SDKMod

# Export everything from the other files
from .GFxMovie import GFxMovie as GFxMovie  # noqa F401
from .Misc import ShowChatMessage as ShowChatMessage  # noqa F401
from .Misc import ShowHUDMessage as ShowHUDMessage  # noqa F401
from .OptionBox import OptionBox as OptionBox  # noqa F401
from .OptionBox import OptionBoxButton as OptionBoxButton  # noqa F401
from .OptionBox import OptionScrollType as OptionScrollType  # noqa F401
from .ReorderBox import ReorderBox as ReorderBox  # noqa F401
from .TextInputBox import TextInputBox as TextInputBox  # noqa F401
from .TrainingBox import TrainingBox as TrainingBox  # noqa F401

VersionMajor: int = 1
VersionMinor: int = 5


# Provide an entry in the mods list just so users can see that this is loaded
class _UserFeedback(SDKMod):
    Name: str = "UserFeedback"
    Author: str = "apple1417"
    Description: str = (
        "Provides functionality for other mods, but does not do anything by itself."
    )
    Version: str = f"{VersionMajor}.{VersionMinor}"

    Types: ModTypes = ModTypes.Library
    Priority = ModPriorities.Library

    Status: str = "<font color=\"#00FF00\">Loaded</font>"
    SettingsInputs: Dict[str, str] = {}


RegisterMod(_UserFeedback())
