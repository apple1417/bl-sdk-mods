import bl2sdk
from typing import ClassVar, List


class RoundsPerMinute(bl2sdk.BL2MOD):
    Name: ClassVar[str] = "Rounds Per Minute"
    Author: ClassVar[str] = "apple1417"
    Description: ClassVar[str] = (
        "Makes item cards display rounds per minute rather than second."
    )
    Types: ClassVar[List[bl2sdk.ModTypes]] = [bl2sdk.ModTypes.Utility]
    Version: ClassVar[str] = "1.0"

    def __init__(self) -> None:
        # Hopefully I can remove this in a future SDK update
        self.Author += "\nVersion: " + str(self.Version)  # type: ignore

    def Enable(self) -> None:
        def SetTopStat(caller: bl2sdk.UObject, function: bl2sdk.UFunction, params: bl2sdk.FStruct) -> bool:
            if params.IconName == "weaponFireRate":
                newRate = f"{float(params.ValueText) * 60:.1f}"
                aux = "" if params.AuxText is None else params.AuxText

                bl2sdk.DoInjectedCallNext()
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

        bl2sdk.RegisterHook("WillowGame.ItemCardGFxObject.SetTopStat", "RoundsPerMinute", SetTopStat)

    def Disable(self) -> None:
        bl2sdk.RemoveHook("WillowGame.ItemCardGFxObject.SetTopStat", "RoundsPerMinute")


instance = RoundsPerMinute()
if __name__ != "__main__":
    bl2sdk.Mods.append(instance)
else:
    bl2sdk.Log("[RPM] Manually loaded")
    for i in range(len(bl2sdk.Mods)):
        mod = bl2sdk.Mods[i]
        if bl2sdk.Mods[i].Name == instance.Name:
            bl2sdk.Mods[i].Disable()
            bl2sdk.Mods[i] = instance
            bl2sdk.Log("[RPM] Disabled and removed last instance")
            break
    else:
        bl2sdk.Log("[RPM] Could not find previous instance")
        bl2sdk.Mods.append(instance)

    bl2sdk.Log("[RPM] Auto-enabling")
    instance.Status = "Enabled"
    instance.SettingsInputs["Enter"] = "Disable"
    instance.Enable()
