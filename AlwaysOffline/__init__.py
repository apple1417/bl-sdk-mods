import unrealsdk
import os
from typing import ClassVar, Dict, List


class AlwaysOffline(unrealsdk.BL2MOD):
    Name: ClassVar[str] = "Always Offline"
    Author: ClassVar[str] = "apple1417"
    Description: ClassVar[str] = (
        "Forces the game to never download SHiFT hotfixes, meaning you can always safely use"
        " offline text mods.\n"
        "\n"
        "Note that enabling/disabling this mod only applies next time you launch the game."
    )
    Types: ClassVar[List[unrealsdk.ModTypes]] = [unrealsdk.ModTypes.Utility]
    Version: ClassVar[str] = "1.1"

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
        def DoSparkAuthentication(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            caller.ShouldStartSparkInitialization = False
            return True

        unrealsdk.RegisterHook("WillowGame.WillowGFxMoviePressStart.DoSparkAuthentication", "AlwaysOffline", DoSparkAuthentication)

        open(self.ENABLED_FILE, "a").close()

    def Disable(self) -> None:
        try:
            os.remove(self.ENABLED_FILE)
        except FileNotFoundError:
            pass

        unrealsdk.RemoveHook("WillowGame.WillowGFxMoviePressStart.DoSparkAuthentication", "AlwaysOffline")


unrealsdk.Mods.append(AlwaysOffline())
