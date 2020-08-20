import unrealsdk
import random
from typing import List

from Mods.ModMenu import EnabledSaveType, Options, Mods, ModTypes, RegisterMod, SDKMod


class EnemyLevelRandomizer(SDKMod):
    Name: str = "Enemy Level Randomizer"
    Author: str = "apple1417"
    Description: str = (
        "Randomizes the level of enemies a bit more.\n"
        "\n"
        "Probably a bad idea."
    )
    Version: str = "1.4"

    Types: ModTypes = ModTypes.Gameplay
    SaveEnabledState: EnabledSaveType = EnabledSaveType.LoadWithSettings

    MinSlider: Options.Slider
    MaxSlider: Options.Slider
    OffsetSlider: Options.Slider

    Options: List[Options.Base]

    def __init__(self) -> None:
        self.OffsetSlider = Options.Slider(
            Caption="Level Offset",
            Description=(
                "A constant offset applied to the intended enemy levels, before any randomization."
            ),
            StartingValue=0,
            MinValue=-50,
            MaxValue=50,
            Increment=1
        )
        self.MinSlider = Options.Slider(
            Caption="Max Decrease",
            Description=(
                "The maximum amount an enemy's level can be randomly decreased."
                " Note that a level cannot be decreased below 0."
            ),
            StartingValue=5,
            MinValue=0,
            MaxValue=50,
            Increment=1
        )
        self.MaxSlider = Options.Slider(
            Caption="Max Increase",
            Description="The maximum amount an enemy's level can be randomly increased.",
            StartingValue=5,
            MinValue=0,
            MaxValue=50,
            Increment=1
        )

        self.Options = [self.OffsetSlider, self.MinSlider, self.MaxSlider]

    def Enable(self) -> None:
        def SetGameStage(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            # This might do weird things if we let it through, visibly you'll stay at your level but
            #  idk if there are any side effects
            if str(caller).startswith("WillowPlayerPawn"):
                return True

            default = max(0, params.NewGameStage + self.OffsetSlider.CurrentValue)
            min_val = max(0, default - self.MinSlider.CurrentValue)
            max_val = max(0, default + self.MaxSlider.CurrentValue)
            val = random.randrange(min_val, max_val + 1)

            unrealsdk.DoInjectedCallNext()
            caller.SetGameStage(val)
            return False

        unrealsdk.RegisterHook("WillowGame.WillowPawn.SetGameStage", self.Name, SetGameStage)

    def Disable(self) -> None:
        unrealsdk.RemoveHook("WillowGame.WillowPawn.SetGameStage", self.Name)


instance = EnemyLevelRandomizer()
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
