import unrealsdk
from typing import ClassVar, List


class RoundsPerMinute(unrealsdk.BL2MOD):
    Name: ClassVar[str] = "Rounds Per Minute"
    Author: ClassVar[str] = "apple1417"
    Description: ClassVar[str] = (
        "Makes item cards display rounds per minute rather than second."
    )
    Types: ClassVar[List[unrealsdk.ModTypes]] = [unrealsdk.ModTypes.Utility]
    Version: ClassVar[str] = "1.1"

    def __init__(self) -> None:
        # Hopefully I can remove this in a future SDK update
        self.Author += "\nVersion: " + str(self.Version)  # type: ignore

    def Enable(self) -> None:
        def SetTopStat(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            if params.LabelText == "Fire Rate":
                newRate = f"{float(params.ValueText) * 60:.1f}"
                aux = "" if params.AuxText is None else params.AuxText

                unrealsdk.DoInjectedCallNext()
                caller.SetTopStat(
                    params.StatIndex,
                    params.LabelText,
                    newRate,
                    params.CompareArrow,
                    aux,
                    params.IconName
                )
                return False

            return True

        unrealsdk.RegisterHook("WillowGame.ItemCardGFxObject.SetTopStat", "RoundsPerMinute", SetTopStat)

    def Disable(self) -> None:
        unrealsdk.RemoveHook("WillowGame.ItemCardGFxObject.SetTopStat", "RoundsPerMinute")


instance = RoundsPerMinute()
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
