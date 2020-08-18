import unrealsdk
import os

from Mods.ModMenu import EnabledSaveType, ModTypes, RegisterMod, SDKMod


class NoOfflineWarning(SDKMod):
    Name: str = "No Offline Warning"
    Author: str = "apple1417"
    Description: str = (
        "Automatically closes the spammy dialog warning you that SHiFT is offline."
    )
    Version: str = "1.1"

    Types: ModTypes = ModTypes.Utility
    SaveEnabledState: EnabledSaveType = EnabledSaveType.LoadWithSettings

    def __init__(self) -> None:
        # Convert from the legacy enabled file
        enabled_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "ENABLED")
        if os.path.exists(enabled_file):
            self.SettingsInputPressed("Enable")
            os.remove(enabled_file)

    def Enable(self) -> None:
        def DisplayOkBoxTextFromSpark(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            if params.Section == "dlgCouldNotConnectSHiFT":
                caller.Close()
                return False
            return True

        unrealsdk.RegisterHook("WillowGame.WillowGFxDialogBox.DisplayOkBoxTextFromSpark", self.Name, DisplayOkBoxTextFromSpark)

    def Disable(self) -> None:
        unrealsdk.RemoveHook("WillowGame.WillowGFxDialogBox.DisplayOkBoxTextFromSpark", self.Name)


RegisterMod(NoOfflineWarning())
