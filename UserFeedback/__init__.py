import unrealsdk
from typing import ClassVar, Dict, List

# Export everything from the other files
from .GFxMovie import GFxMovie as GFxMovie
from .Misc import ShowChatMessage as ShowChatMessage
from .Misc import ShowHUDMessage as ShowHUDMessage
from .OptionBox import OptionBox as OptionBox
from .OptionBox import OptionBoxButton as OptionBoxButton
from .OptionBox import OptionScrollType as OptionScrollType
from .ReorderBox import ReorderBox as ReorderBox
from .TextInputBox import TextInputBox as TextInputBox
from .TrainingBox import TrainingBox as TrainingBox

VersionMajor: int = 1
VersionMinor: int = 4

# Just to satisfy pyflakes' unused imports warning - can't seem to get it to ignore this file
if False:
    GFxMovie()
    ShowChatMessage()
    ShowHUDMessage()
    OptionBox()
    OptionBoxButton()
    OptionScrollType()
    ReorderBox()
    TextInputBox()
    TrainingBox()


# Provide an entry in the mods list just so users can see that this is loaded
class _UserFeedback(unrealsdk.BL2MOD):
    Name: ClassVar[str] = "UserFeedback"
    Author: ClassVar[str] = "apple1417"
    Description: ClassVar[str] = (
        "Provides functionality for other mods, but does not do anything by itself."
    )
    Types: ClassVar[List[unrealsdk.ModTypes]] = [unrealsdk.ModTypes.Utility]
    Version: ClassVar[str] = f"{VersionMajor}.{VersionMinor}"

    Status: str
    SettingsInputs: Dict[str, str]

    def __init__(self) -> None:
        self.Author += "\nVersion: " + str(self.Version)  # type: ignore

        self.Status = "Enabled"
        self.SettingsInputs = {}


# Only register the mod on main menu, just to try keep it at the end of the list
def _OnMainMenu(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
    instance = _UserFeedback()
    unrealsdk.RegisterMod(instance)
    if __name__ == "__main__":
        for i in range(len(unrealsdk.Mods)):
            if unrealsdk.Mods[i].Name == instance.Name:
                unrealsdk.Mods.remove(instance)
                unrealsdk.Mods[i] = instance
                break
    unrealsdk.RemoveHook("WillowGame.FrontendGFxMovie.Start", "UserFeedback")
    return True


unrealsdk.RegisterHook("WillowGame.FrontendGFxMovie.Start", "UserFeedback", _OnMainMenu)
