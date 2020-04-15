import unrealsdk
import os
from typing import ClassVar, Dict, List


class FixHotfixes(unrealsdk.BL2MOD):
    Name: ClassVar[str] = "Fix Hotfixes"
    Author: ClassVar[str] = "apple1417"
    Description: ClassVar[str] = (
        "Allows you to use \"online\" text mod hotfixes, by adding dummy objects to reorder SHiFT"
        " services.\n"
        "\n"
        "Note that this solution is *not* stable, and will likely break if Gearbox reorders"
        " services again."
    )
    Types: ClassVar[List[unrealsdk.ModTypes]] = [unrealsdk.ModTypes.Utility]
    Version: ClassVar[str] = "1.0"

    # For some reason not defining these makes changing them overwrite *ALL* mods' values
    Status: str = "Disabled"
    SettingsInputs: Dict[str, str] = {"Enter": "Enable"}

    ENABLED_FILE: str = os.path.join(os.path.dirname(os.path.realpath(__file__)), "ENABLED")

    DUMMY_AMOUNT: ClassVar[int] = 1

    def __init__(self) -> None:
        # Hopefully I can remove this in a future SDK update
        self.Author += "\nVersion: " + str(self.Version)  # type: ignore

        if os.path.exists(self.ENABLED_FILE):
            self.Status = "Enabled"
            self.SettingsInputs["Enter"] = "Disable"
            self.Enable()

    def Enable(self) -> None:
        def HandleVerificationReceived(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            base = unrealsdk.FindAll("SparkServiceConfiguration")[-1]
            for i in range(self.DUMMY_AMOUNT):
                obj = unrealsdk.ConstructObject(Class=base.Class, Outer=base.Outer)
                obj.ServiceName = "Dummy"

            unrealsdk.RemoveHook("GearboxFramework.SparkInitializationProcess.HandleVerificationReceived", "FixHotfixes")
            return True

        unrealsdk.RegisterHook("GearboxFramework.SparkInitializationProcess.HandleVerificationReceived", "FixHotfixes", HandleVerificationReceived)

        open(self.ENABLED_FILE, "a").close()

    def Disable(self) -> None:
        try:
            os.remove(self.ENABLED_FILE)
        except FileNotFoundError:
            pass

        unrealsdk.RemoveHook("WillowGame.WillowGFxMoviePressStart.DoSparkAuthentication", "FixHotfixes")


unrealsdk.Mods.append(FixHotfixes())
