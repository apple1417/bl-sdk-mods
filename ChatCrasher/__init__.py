import unrealsdk
import os

from Mods.ModMenu import EnabledSaveType, ModTypes, RegisterMod, SDKMod


class ChatCrasher(SDKMod):
    Name: str = "Chat Crasher"
    Author: str = "apple1417"
    Description: str = (
        "Crashes the game when using chat, either by typing manually or by execing a mod file"
        " containing a say command.\n"
        "Also happens to force the game to never connect to SHiFT. :)\n"
        "\n"
        "Note that enabling/disabling this mod only applies next time you launch the game."
    )
    Version: str = "1.2"

    Types: ModTypes = ModTypes.Utility
    SaveEnabledState: EnabledSaveType = EnabledSaveType.LoadWithSettings

    def __init__(self) -> None:
        # Convert from the legacy enabled file
        enabled_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "ENABLED")
        if os.path.exists(enabled_file):
            self.SettingsInputPressed("Enable")
            os.remove(enabled_file)

    def Enable(self) -> None:
        def DoSparkAuthentication(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            caller.ShouldStartSparkInitialization = False
            return True
        unrealsdk.RegisterHook("WillowGame.WillowGFxMoviePressStart.DoSparkAuthentication", "AlwaysOffline", DoSparkAuthentication)

    def Disable(self) -> None:
        unrealsdk.RemoveHook("WillowGame.WillowGFxMoviePressStart.DoSparkAuthentication", "AlwaysOffline")


RegisterMod(ChatCrasher())
