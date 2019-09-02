import bl2sdk
import json
import random
from os import path
from typing import List
from typing import Dict


class EnemyLevelRandomizer(bl2sdk.BL2MOD):
    Name: str = "ELR"
    Author: str = "apple1417"
    Description: str = (
        "<font size='24' color='#FFDEAD'>Enemy Level Randomizer</font>\n"
        "Randomizes the level of enemies a bit more.\n"
        "\n"
        "Probably a bad idea."
    )
    Types: List[bl2sdk.ModTypes] = [bl2sdk.ModTypes.Gameplay]
    Version = "1.0"

    OPTIONS_PATH: str = path.join(path.dirname(path.realpath(__file__)), "options.json")
    Options: Dict[str, int] = {}

    def __init__(self) -> None:
        # Hopefully I can remove this in a future SDK update
        self.Author += "\nVersion: " + str(self.Version)

        self.rand: random.Random = random.Random()

        self.minSlider: bl2sdk.Options.SliderOption = bl2sdk.Options.SliderOption(
            Description="The minimum below the intended level that an enemy can be",
            Caption="Min Level Difference",
            StartingValue=15,
            MinValue=0,
            MaxValue=255,
            Increment=1
        )
        self.maxSlider: bl2sdk.Options.SliderOption = bl2sdk.Options.SliderOption(
            Description="The maximum above the intended level that an enemy can be",
            Caption="Max Level Difference",
            StartingValue=15,
            MinValue=0,
            MaxValue=255,
            Increment=1
        )
        self.offsetSlider: bl2sdk.Options.SliderOption = bl2sdk.Options.SliderOption(
            Description="An offset applied to the intended level before randomizing it",
            Caption="Level Offset",
            StartingValue=0,
            MinValue=-255,
            MaxValue=255,
            Increment=1
        )

        if path.exists(self.OPTIONS_PATH):
            with open(self.OPTIONS_PATH) as file:
                self.Options = json.load(file)
                if "min" in self.Options:
                    self.minSlider.CurrentValue = self.Options["min"]
                if "max" in self.Options:
                    self.maxSlider.CurrentValue = self.Options["max"]
                if "offset" in self.Options:
                    self.offsetSlider.CurrentValue = self.Options["offset"]

    class LoggingLevel:
        NONE = 0
        CALLS = 1
        FULL = 2
    LOGGING = LoggingLevel.NONE

    def debugLogging(self, caller: bl2sdk.UObject, function: bl2sdk.UFunction, params: bl2sdk.FStruct) -> None:
        if self.LOGGING == self.LoggingLevel.CALLS:
            bl2sdk.Log("[ELR] " + str(function).split(".")[-1])
        elif self.LOGGING == self.LoggingLevel.FULL:
            bl2sdk.Log("[ELR] " + str(caller))
            bl2sdk.Log("[ELR] " + str(function))
            bl2sdk.Log("[ELR] " + str(params))

    def Enable(self) -> None:
        def SetGameStage(caller: bl2sdk.UObject, function: bl2sdk.UFunction, params: bl2sdk.FStruct) -> bool:
            self.debugLogging(caller, function, params)

            # This might do weird things if we let it through, visibly you'll stay at your level but
            #  idk if there are any side effects
            if str(caller).startswith("WillowPlayerPawn"):
                return True

            default: int = params.NewGameStage + self.offsetSlider.CurrentValue
            min_val: int = max(0, default - self.minSlider.CurrentValue)
            max_val: int = min(255, default + self.maxSlider.CurrentValue)
            val: int = self.rand.randrange(min_val, max_val + 1)

            if self.LOGGING == self.LoggingLevel.FULL:
                bl2sdk.Log(f"[ELR]: Setting level to {val}")

            bl2sdk.DoInjectedCallNext()
            caller.SetGameStage(val)

            return False

        bl2sdk.RegisterHook("WillowGame.WillowPawn.SetGameStage", "EnemyLevelRandomizer", SetGameStage)

        self.RegisterGameConfigOption(self.minSlider)
        self.RegisterGameConfigOption(self.maxSlider)
        self.RegisterGameConfigOption(self.offsetSlider)

    def Disable(self) -> None:
        bl2sdk.RemoveHook("WillowGame.WillowPawn.SetGameStage", "EnemyLevelRandomizer")

        self.UnregisterGameConfigOption(self.minSlider)
        self.UnregisterGameConfigOption(self.maxSlider)
        self.UnregisterGameConfigOption(self.offsetSlider)

    def ModOptionChanged(self, option: bl2sdk.Options, newValue: int) -> None:
        if option == self.minSlider:
            self.Options["min"] = int(newValue)
        elif option == self.maxSlider:
            self.Options["max"] = int(newValue)
        elif option == self.offsetSlider:
            self.Options["offset"] = int(newValue)
        else:
            return

        with open(self.OPTIONS_PATH, "w") as file:
            json.dump(self.Options, file, indent=4)


instance = EnemyLevelRandomizer()
if __name__ == "__main__":
    bl2sdk.Log("[ELR] Manually loaded")
    for mod in bl2sdk.Mods:
        if mod.Name == instance.Name:
            mod.Disable()
            bl2sdk.Mods.remove(mod)
            bl2sdk.Log("[ELR] Disabled and removed last instance")
            break
    else:
        bl2sdk.Log("[ELR] Could not find previous instance")
    bl2sdk.Log("[ELR] Auto-enabling")
    instance.Status = "Enabled"
    instance.SettingsInputs = {"Enter": "Disable"}
    instance.Enable()
bl2sdk.Mods.append(instance)
