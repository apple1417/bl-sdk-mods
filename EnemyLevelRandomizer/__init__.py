import unrealsdk
import random
from typing import ClassVar, List, Union


class EnemyLevelRandomizer(unrealsdk.BL2MOD):
    Name: ClassVar[str] = "ELR"
    Author: ClassVar[str] = "apple1417"
    Description: ClassVar[str] = (
        "<font size='24' color='#FFDEAD'>Enemy Level Randomizer</font>\n"
        "Randomizes the level of enemies a bit more.\n"
        "\n"
        "Probably a bad idea."
    )
    Types: ClassVar[List[unrealsdk.ModTypes]] = [unrealsdk.ModTypes.Gameplay]
    Version: ClassVar[str] = "1.2"

    Options: List[Union[unrealsdk.Options.Slider, unrealsdk.Options.Spinner, unrealsdk.Options.Boolean, unrealsdk.Options.Hidden]]

    MinSlider: unrealsdk.Options.Slider
    MaxSlider: unrealsdk.Options.Slider
    OffsetSlider: unrealsdk.Options.Slider

    def __init__(self) -> None:
        # Hopefully I can remove this in a future SDK update
        self.Author += "\nVersion: " + str(self.Version)  # type: ignore

        self.MinSlider = unrealsdk.Options.Slider(
            Description="The minimum below the intended level that an enemy can be",
            Caption="Min Level Difference",
            StartingValue=15,
            MinValue=0,
            MaxValue=255,
            Increment=1
        )
        self.MaxSlider = unrealsdk.Options.Slider(
            Description="The maximum above the intended level that an enemy can be",
            Caption="Max Level Difference",
            StartingValue=15,
            MinValue=0,
            MaxValue=255,
            Increment=1
        )
        self.OffsetSlider = unrealsdk.Options.Slider(
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

        unrealsdk.RegisterHook("WillowGame.WillowPawn.SetGameStage", "EnemyLevelRandomizer", SetGameStage)

    def Disable(self) -> None:
        unrealsdk.RemoveHook("WillowGame.WillowPawn.SetGameStage", "EnemyLevelRandomizer")


instance = EnemyLevelRandomizer()
if __name__ != "__main__":
    unrealsdk.RegisterMod(instance)
else:
    unrealsdk.Log(f"[{instance.Name}] Manually loaded")
    for i in range(len(unrealsdk.Mods)):
        mod = unrealsdk.Mods[i]
        if unrealsdk.Mods[i].Name == instance.Name:
            unrealsdk.Mods[i].Disable()

            unrealsdk.RegisterMod(instance)
            unrealsdk.Mods.remove(instance)
            unrealsdk.Mods[i] = instance
            unrealsdk.Log(f"[{instance.Name}] Disabled and removed last instance")
            break
    else:
        unrealsdk.Log(f"[{instance.Name}] Could not find previous instance")
        unrealsdk.RegisterMod(instance)

    unrealsdk.Log(f"[{instance.Name}] Auto-enabling")
    instance.Status = "Enabled"
    instance.SettingsInputs["Enter"] = "Disable"
    instance.Enable()
