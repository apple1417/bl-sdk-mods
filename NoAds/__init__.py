import unrealsdk
import os
from typing import ClassVar, Dict, List


class NoAds(unrealsdk.BL2MOD):
    Name: ClassVar[str] = "No Ads"
    Author: ClassVar[str] = "apple1417"
    Description: ClassVar[str] = (
        "Prevents ads from showing.\n"
        "Includes both the obnoxious BL3 ads as well as the small MoTD DLC ads."
    )
    Types: ClassVar[List[unrealsdk.ModTypes]] = [unrealsdk.ModTypes.Utility]
    Version: ClassVar[str] = "1.2"

    # For some reason not defining these makes changing them overwrite *ALL* mods' values
    Status: str = "Disabled"
    SettingsInputs: Dict[str, str] = {"Enter": "Enable"}

    ENABLED_FILE: ClassVar[str] = os.path.join(os.path.dirname(os.path.realpath(__file__)), "ENABLED")

    def __init__(self) -> None:
        # Hopefully I can remove this in a future SDK update
        self.Author += "\nVersion: " + str(self.Version)  # type: ignore

        if os.path.exists(self.ENABLED_FILE):
            self.Status = "Enabled"
            self.SettingsInputs["Enter"] = "Disable"
            self.Enable()

    def Enable(self) -> None:
        def BlockCall(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            return False

        unrealsdk.RegisterHook("WillowGame.FrontendGFxMovie.ShowMOTD", "AdBlock", BlockCall)
        unrealsdk.RegisterHook("WillowGame.WillowPlayerController.CanAcessOakUpsell", "AdBlock", BlockCall)

        open(self.ENABLED_FILE, "a").close()

    def Disable(self) -> None:
        try:
            os.remove(self.ENABLED_FILE)
        except FileNotFoundError:
            pass

        unrealsdk.RemoveHook("WillowGame.FrontendGFxMovie.ShowMOTD", "AdBlock")
        unrealsdk.RemoveHook("WillowGame.WillowPlayerController.CanAcessOakUpsell", "AdBlock")


unrealsdk.RegisterMod(NoAds())
