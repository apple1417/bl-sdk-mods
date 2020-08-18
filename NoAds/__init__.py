import unrealsdk
import os

from Mods.ModMenu import EnabledSaveType, ModTypes, RegisterMod, SDKMod


class NoAds(SDKMod):
    Name: str = "No Ads"
    Author: str = "apple1417"
    Description: str = (
        "Prevents ads from showing.\n"
        "Includes both the obnoxious BL3 ads as well as the small MoTD DLC ads."
    )
    Version: str = "1.3"

    Types: ModTypes = ModTypes.Utility
    SaveEnabledState: EnabledSaveType = EnabledSaveType.LoadWithSettings

    def __init__(self) -> None:
        # Convert from the legacy enabled file
        enabled_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "ENABLED")
        if os.path.exists(enabled_file):
            self.SettingsInputPressed("Enable")
            os.remove(enabled_file)

    def Enable(self) -> None:
        def BlockCall(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            return False
        unrealsdk.RegisterHook("WillowGame.FrontendGFxMovie.ShowMOTD", self.Name, BlockCall)
        unrealsdk.RegisterHook("WillowGame.WillowPlayerController.CanAcessOakUpsell", self.Name, BlockCall)

    def Disable(self) -> None:
        unrealsdk.RemoveHook("WillowGame.FrontendGFxMovie.ShowMOTD", self.Name)
        unrealsdk.RemoveHook("WillowGame.WillowPlayerController.CanAcessOakUpsell", self.Name)


RegisterMod(NoAds())
