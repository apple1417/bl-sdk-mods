import unrealsdk
from typing import List

from Mods.ModMenu import EnabledSaveType, Mods, ModTypes, Options, RegisterMod, SDKMod


class OfflineHelpers(SDKMod):
    Name: str = "Offline Helpers"
    Author: str = "apple1417"
    Description: str = (
        "Adds several small features useful when playing offline.\n"
        "\n"
        "Note that some changes will only apply when you restart the game."
    )
    Version: str = "1.3"

    Types: ModTypes = ModTypes.Utility
    SaveEnabledState: EnabledSaveType = EnabledSaveType.LoadWithSettings

    ForceOption: Options.Boolean
    WarningOption: Options.Boolean
    Options: List[Options.Base]

    def __init__(self) -> None:
        self.ForceOption = Options.Boolean(
            "Force Offline Mode (ADVANCED)", (
                "Forces your game to never connect to SHiFT. Note you will need to manually edit"
                " offline blcmm files to use them with this - check the Readme / Mod Database"
                " description."
            ),
            False
        )
        self.WarningOption = Options.Boolean(
            "Hide Offline Warning",
            "Automatically hides the offline mode warning.",
            True
        )
        self.Options = [self.WarningOption, self.ForceOption]

    def Enable(self) -> None:
        def AddChatMessage(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            if unrealsdk.GetEngine().SparkInterface.ObjectPointer.IsSparkEnabled():
                return True

            time = caller.GetTimestampString(unrealsdk.FindAll("WillowSaveGameManager")[-1].TimeFormat)
            caller.AddChatMessageInternal(params.PRI.PlayerName + time, params.msg)
            return False

        def DisplayOkBoxTextFromSpark(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            if not self.WarningOption.CurrentValue:
                return True
            if params.Section == "dlgCouldNotConnectSHiFT":
                caller.Close()
                return False
            return True

        def DoSparkAuthentication(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            if self.ForceOption.CurrentValue:
                caller.ShouldStartSparkInitialization = False
            return True

        unrealsdk.RunHook("WillowGame.TextChatGFxMovie.AddChatMessage", self.Name, AddChatMessage)
        unrealsdk.RunHook("WillowGame.WillowGFxDialogBox.DisplayOkBoxTextFromSpark", self.Name, DisplayOkBoxTextFromSpark)
        unrealsdk.RunHook("WillowGame.WillowGFxMoviePressStart.DoSparkAuthentication", self.Name, DoSparkAuthentication)

    def Disable(self) -> None:
        unrealsdk.RemoveHook("WillowGame.TextChatGFxMovie.AddChatMessage", self.Name)
        unrealsdk.RemoveHook("WillowGame.WillowGFxDialogBox.DisplayOkBoxTextFromSpark", self.Name)
        unrealsdk.RemoveHook("WillowGame.WillowGFxMoviePressStart.DoSparkAuthentication", self.Name)


instance = OfflineHelpers()
if __name__ == "__main__":
    unrealsdk.Log(f"[{instance.Name}] Manually loaded")
    for mod in Mods:
        if mod.Name == instance.Name:
            if mod.IsEnabled:
                mod.Disable()
            Mods.remove(mod)
            unrealsdk.Log(f"[{instance.Name}] Removed last instance")

            # Fixes inspect.getfile()
            instance.__class__.__module__ = mod.__class__.__module__
            break
RegisterMod(instance)
