import unrealsdk

from Mods.ModMenu import EnabledSaveType, Mods, ModTypes, Options, RegisterMod, SDKMod


class TrueDamageLogger(SDKMod):
    Name: str = "True Damage Logger"
    Author: str = "apple1417"
    Description: str = (
        "Prints the actual amount of damage you deal to console, bypassing visual damage cap."
    )
    Version: str = "1.3"

    Types: ModTypes = ModTypes.Utility
    SaveEnabledState: EnabledSaveType = EnabledSaveType.LoadWithSettings

    MinDamageSlider: Options.Slider

    def __init__(self) -> None:
        self.MinDamageSlider = Options.Slider(
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
                pt_num = PC.GetCurrentPlaythrough() + 1
                for pt in actor.BalanceDefinitionState.BalanceDefinition.PlayThroughs:
                    if pt.PlayThrough > pt_num:
                        continue
                    if pt.DisplayName is None or len(pt.DisplayName) == 0:
                        continue
                    name = pt.DisplayName

            unrealsdk.Log(f"Dealt {damage} damage to level {actor.GetExpLevel()} {name}")

            return True

        unrealsdk.RegisterHook("WillowGame.WillowDamageTypeDefinition.DisplayRecentDamageForPlayer", self.Name, DisplayRecentDamageForPlayer)

    def Disable(self) -> None:
        unrealsdk.RemoveHook("WillowGame.WillowDamageTypeDefinition.DisplayRecentDamageForPlayer", self.Name)


instance = TrueDamageLogger()
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
