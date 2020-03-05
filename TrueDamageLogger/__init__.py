import unrealsdk
from typing import ClassVar, List, Union


class TrueDamageLogger(unrealsdk.BL2MOD):
    Name: ClassVar[str] = "True Damage Logger"
    Author: ClassVar[str] = "apple1417"
    Description: ClassVar[str] = (
        "Prints the actual amount of damage you deal to console, bypassing visual damage cap."
    )
    Types: ClassVar[List[unrealsdk.ModTypes]] = [unrealsdk.ModTypes.Utility]
    Version: ClassVar[str] = "1.2"

    MinDamageSlider: unrealsdk.Options.Slider
    Options: List[Union[unrealsdk.Options.Slider, unrealsdk.Options.Spinner, unrealsdk.Options.Boolean, unrealsdk.Options.Hidden]]

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
        def DisplayRecentDamageForPlayer(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            PC = unrealsdk.GetEngine().GamePlayers[0].Actor
            if params.PC != PC:
                return True

            damage = params.DamageEventData.TotalDamageForDamageType
            if damage < 10**self.MinDamageSlider.CurrentValue:
                return True

            actor = params.DamageEventData.DamagedActor

            name = actor.PathName(actor)
            if actor.AIClass is not None and actor.AIClass.DefaultDisplayName is not None:
                name = actor.AIClass.DefaultDisplayName

            if actor.BalanceDefinitionState.BalanceDefinition is not None:
                ptNum = PC.GetCurrentPlaythrough() + 1
                for pt in actor.BalanceDefinitionState.BalanceDefinition.PlayThroughs:
                    if pt.PlayThrough > ptNum:
                        continue
                    if pt.DisplayName is None or len(pt.DisplayName) == 0:
                        continue
                    name = pt.DisplayName

            unrealsdk.Log(f"Dealt {damage} damage to level {actor.GetExpLevel()} {name}")

            return True

        unrealsdk.RegisterHook("WillowGame.WillowDamageTypeDefinition.DisplayRecentDamageForPlayer", "TrueDamageLogger", DisplayRecentDamageForPlayer)

    def Disable(self) -> None:
        unrealsdk.RemoveHook("WillowGame.WillowDamageTypeDefinition.DisplayRecentDamageForPlayer", "TrueDamageLogger")


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
