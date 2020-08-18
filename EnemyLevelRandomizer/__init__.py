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
    Version: str = "1.3"

    Types: ModTypes = ModTypes.Gameplay
    SaveEnabledState: EnabledSaveType = EnabledSaveType.LoadWithSettings

    MinSlider: Options.Slider
    MaxSlider: Options.Slider
    OffsetSlider: Options.Slider

    Options: List[Options.Base]

    def __init__(self) -> None:
        self.MinSlider = Options.Slider(
            Description="The minimum below the intended level that an enemy can be",
            Caption="Min Level Difference",
            StartingValue=15,
            MinValue=0,
            MaxValue=255,
            Increment=1
        )
        self.MaxSlider = Options.Slider(
            Description="The maximum above the intended level that an enemy can be",
            Caption="Max Level Difference",
            StartingValue=15,
            MinValue=0,
            MaxValue=255,
            Increment=1
        )
        self.OffsetSlider = Options.Slider(
            Description="An offset applied to the intended level before randomizing it",
            Caption="Level Offset",
            StartingValue=0,
            MinValue=-255,
            MaxValue=255,
            Increment=1
        )

        self.Options = [self.MinSlider, self.MaxSlider, self.OffsetSlider]

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
