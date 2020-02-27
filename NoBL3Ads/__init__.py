import bl2sdk
import os
from typing import ClassVar, List

ENABLED_FILE: str = os.path.join(os.path.dirname(os.path.realpath(__file__)), "ENABLED")


class NoBL3Ads(bl2sdk.BL2MOD):
    Name: ClassVar[str] = "No BL3 Ads"
    Author: ClassVar[str] = "apple1417"
    Description: ClassVar[str] = (
        "Prevents the BL3 ads from showing."
    )
    Types: ClassVar[List[bl2sdk.ModTypes]] = [bl2sdk.ModTypes.Utility]
    Version: ClassVar[str] = "1.0"

    def __init__(self) -> None:
        # Hopefully I can remove this in a future SDK update
        self.Author += "\nVersion: " + str(self.Version)  # type: ignore

        if os.path.exists(ENABLED_FILE):
            self.Status = "Enabled"

    def Enable(self) -> None:
        open(ENABLED_FILE, "a").close()

        bl2sdk.RegisterHook("WillowGame.WillowPlayerController.CanAcessOakUpsell", "NoBL3Ads", CanAcessOakUpsell)

    def Disable(self) -> None:
        try:
            os.remove(ENABLED_FILE)
        except OSError:
            pass

        bl2sdk.RemoveHook("WillowGame.WillowPlayerController.CanAcessOakUpsell", "NoBL3Ads")


def CanAcessOakUpsell(caller: bl2sdk.UObject, function: bl2sdk.UFunction, params: bl2sdk.FStruct) -> bool:
    return False


if os.path.exists(ENABLED_FILE):
    bl2sdk.RegisterHook("WillowGame.WillowPlayerController.CanAcessOakUpsell", "NoBL3Ads", CanAcessOakUpsell)

bl2sdk.Mods.append(NoBL3Ads())
