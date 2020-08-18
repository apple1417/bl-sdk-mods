import unrealsdk
import os
from typing import ClassVar

from Mods.ModMenu import EnabledSaveType, ModTypes, RegisterMod, SDKMod


class FixHotfixes(SDKMod):
    Name: str = "Fix Hotfixes"
    Author: str = "apple1417"
    Description: str = (
        "Adds dummy objects to reorder SHiFT services, moving hotfixes back to index 6.\n"
        "\n"
        "Note that this solution is *not* stable, and will likely break if Gearbox reorders"
        " services again."
    )
    Version: str = "1.1"

    Types: ModTypes = ModTypes.Utility
    SaveEnabledState: EnabledSaveType = EnabledSaveType.LoadWithSettings

    DUMMY_AMOUNT: ClassVar[int] = 1

    def __init__(self) -> None:
        # Convert from the legacy enabled file
        enabled_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "ENABLED")
        if os.path.exists(enabled_file):
            self.SettingsInputPressed("Enable")
            os.remove(enabled_file)

    def Enable(self) -> None:
        def HandleVerificationReceived(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            PC = unrealsdk.GetEngine().GamePlayers[0].Actor
            for i in range(self.DUMMY_AMOUNT):
                obj = unrealsdk.ConstructObject(unrealsdk.FindClass("SparkServiceConfiguration"))
                PC.ServerRCon(f"set {PC.PathName(obj)} ServiceName Dummy_{i}")

            unrealsdk.RemoveHook("GearboxFramework.SparkInitializationProcess.HandleVerificationReceived", "FixHotfixes")
            return True

        unrealsdk.RegisterHook("GearboxFramework.SparkInitializationProcess.HandleVerificationReceived", "FixHotfixes", HandleVerificationReceived)

    def Disable(self) -> None:
        unrealsdk.RemoveHook("WillowGame.WillowGFxMoviePressStart.DoSparkAuthentication", "FixHotfixes")


RegisterMod(FixHotfixes())
