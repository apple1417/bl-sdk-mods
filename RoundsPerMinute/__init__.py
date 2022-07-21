import unrealsdk

from Mods.ModMenu import EnabledSaveType, Mods, ModTypes, RegisterMod, SDKMod


class RoundsPerMinute(SDKMod):
    Name: str = "Rounds Per Minute"
    Author: str = "apple1417"
    Description: str = (
        "Makes item cards display rounds per minute rather than second."
    )
    Version: str = "1.3"

    Types: ModTypes = ModTypes.Utility
    SaveEnabledState: EnabledSaveType = EnabledSaveType.LoadWithSettings

    def Enable(self) -> None:
        def SetTopStat(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            if params.LabelText == "Fire Rate" and "%" not in params.ValueText:
                new_rate = f"{float(params.ValueText) * 60:.1f}"
                aux = "" if params.AuxText is None else params.AuxText

                unrealsdk.DoInjectedCallNext()
                caller.SetTopStat(
                    params.StatIndex,
                    params.LabelText,
                    new_rate,
                    params.CompareArrow,
                    aux,
                    params.IconName
                )
                return False

            return True

        unrealsdk.RegisterHook("WillowGame.ItemCardGFxObject.SetTopStat", self.Name, SetTopStat)

    def Disable(self) -> None:
        unrealsdk.RemoveHook("WillowGame.ItemCardGFxObject.SetTopStat", self.Name)


instance = RoundsPerMinute()
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
