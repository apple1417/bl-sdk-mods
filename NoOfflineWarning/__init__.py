import unrealsdk
import os
from typing import ClassVar, Dict, List


class NoOfflineWarning(unrealsdk.BL2MOD):
    Name: ClassVar[str] = "No Offline Warning"
    Author: ClassVar[str] = "apple1417"
    Description: ClassVar[str] = (
        "Automatically closes the spammy dialog warning you that SHiFT is offline."
    )
    Types: ClassVar[List[unrealsdk.ModTypes]] = [unrealsdk.ModTypes.Utility]
    Version: ClassVar[str] = "1.0"

    # For some reason not defining these makes changing them overwrite *ALL* mods' values
    Status: str = "Disabled"
    SettingsInputs: Dict[str, str] = {"Enter": "Enable"}

    ENABLED_FILE: str = os.path.join(os.path.dirname(os.path.realpath(__file__)), "ENABLED")

    def __init__(self) -> None:
        # Hopefully I can remove this in a future SDK update
        self.Author += "\nVersion: " + str(self.Version)  # type: ignore

        if os.path.exists(self.ENABLED_FILE):
            self.Status = "Enabled"
            self.SettingsInputs["Enter"] = "Disable"
            self.Enable()

    def Enable(self) -> None:
        def DisplayOkBoxTextFromSpark(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            if params.Section == "dlgCouldNotConnectSHiFT":
                caller.Close()
                return False
            return True

        unrealsdk.RegisterHook("WillowGame.WillowGFxDialogBox.DisplayOkBoxTextFromSpark", "NoOfflineWarning", DisplayOkBoxTextFromSpark)

        open(self.ENABLED_FILE, "a").close()

    def Disable(self) -> None:
        try:
            os.remove(self.ENABLED_FILE)
        except FileNotFoundError:
            pass

        unrealsdk.RemoveHook("WillowGame.WillowGFxDialogBox.DisplayOkBoxTextFromSpark", "NoOfflineWarning")


unrealsdk.Mods.append(NoOfflineWarning())
