import unrealsdk
from typing import ClassVar, List, Union


class TrueDamageLogger(unrealsdk.BL2MOD):
    Name: ClassVar[str] = "True Damage Logger"
    Author: ClassVar[str] = "apple1417"
    Description: ClassVar[str] = (
        "Prints the actual amount of damage you deal to console, bypassing visual damage cap."
    )
    Types: ClassVar[List[unrealsdk.ModTypes]] = [unrealsdk.ModTypes.Utility]
    Version: ClassVar[str] = "1.1"

    Options: List[Union[unrealsdk.Options.Slider, unrealsdk.Options.Spinner, unrealsdk.Options.Boolean, unrealsdk.Options.Hidden]]

    MinDamageSlider: unrealsdk.Options.Slider

    def __init__(self) -> None:
        # Hopefully I can remove this in a future SDK update
        self.Author += "\nVersion: " + str(self.Version)  # type: ignore

        self.MinDamageSlider = unrealsdk.Options.Slider(
            Description="The minimum amount of zeros a damage number has to have before it is logged to console.",
            Caption="Minimum Zeros",
            StartingValue=6,
            MinValue=0,
            MaxValue=40,
            Increment=1
        )
        self.Options = [self.MinDamageSlider]

    def Enable(self) -> None:
        def TakeDamage(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            PC = unrealsdk.GetEngine().GamePlayers[0].Actor

            if params.InstigatedBy != PC:
                return True

            if params.Damage < 10**self.MinDamageSlider.CurrentValue:
                return True

            name = caller.PathName(caller)
            if caller.AIClass is not None and caller.AIClass.DefaultDisplayName is not None:
                name = caller.AIClass.DefaultDisplayName

            if caller.BalanceDefinitionState.BalanceDefinition is not None:
                ptNum = PC.GetCurrentPlaythrough() + 1
                for pt in caller.BalanceDefinitionState.BalanceDefinition.PlayThroughs:
                    if pt.PlayThrough > ptNum:
                        continue
                    if pt.DisplayName is None or len(pt.DisplayName) == 0:
                        continue
                    name = pt.DisplayName

            unrealsdk.Log(f"Dealt {params.Damage} damage to level {caller.GetExpLevel()} {name}")

            return True

        unrealsdk.RegisterHook("WillowGame.WillowPawn.TakeDamage", "TrueDamageLogger", TakeDamage)

    def Disable(self) -> None:
        unrealsdk.RemoveHook("WillowGame.WillowPawn.TakeDamage", "TrueDamageLogger")


instance = TrueDamageLogger()
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
