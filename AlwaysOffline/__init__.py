import bl2sdk
import os
from typing import ClassVar, List

ENABLED_FILE: str = os.path.join(os.path.dirname(os.path.realpath(__file__)), "ENABLED")


class AlwaysOffline(bl2sdk.BL2MOD):
    Name: ClassVar[str] = "Always Offline"
    Author: ClassVar[str] = "apple1417"
    Description: ClassVar[str] = (
        "Forces the game to never download SHiFT hotfixes, meaning you can always safely use"
        " offline text mods.\n"
        "\n"
        "Note that enabling/disabling this mod only applies next time you launch the game."
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

    def Disable(self) -> None:
        try:
            os.remove(ENABLED_FILE)
        except OSError:
            pass


def DoSparkAuthentication(caller: bl2sdk.UObject, function: bl2sdk.UFunction, params: bl2sdk.FStruct) -> bool:
    caller.ShouldStartSparkInitialization = False
    return True


if os.path.exists(ENABLED_FILE):
    bl2sdk.Log("[AlwaysOffline] Enabled, forcing offline mode")
    bl2sdk.RegisterHook("WillowGame.WillowGFxMoviePressStart.DoSparkAuthentication", "AlwaysOffline", DoSparkAuthentication)

bl2sdk.Mods.append(AlwaysOffline())
