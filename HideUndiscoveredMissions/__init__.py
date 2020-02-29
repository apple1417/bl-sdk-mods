import unrealsdk
from typing import ClassVar, List


class HideUndiscoveredMissions(unrealsdk.BL2MOD):
    Name: ClassVar[str] = "Hide Undiscovered Missions"
    Author: ClassVar[str] = "apple1417"
    Description: ClassVar[str] = (
        "Hides undiscoved missions in the mission log."
    )
    Types: ClassVar[List[unrealsdk.ModTypes]] = [unrealsdk.ModTypes.Utility]
    Version: ClassVar[str] = "1.1"

    def __init__(self) -> None:
        # Hopefully I can remove this in a future SDK update
        self.Author += "\nVersion: " + str(self.Version)  # type: ignore

    def Enable(self) -> None:
        def PostBeginPlay(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            # Re-run the function so we can modify it after it's done
            unrealsdk.DoInjectedCallNext()
            caller.PostBeginPlay()

            caller.bShowUndiscoveredMissions = False
            return False

        unrealsdk.RegisterHook("WillowGame.WillowPlayerController.PostBeginPlay", "HideUndiscoveredMissions", PostBeginPlay)
        unrealsdk.GetEngine().GamePlayers[0].Actor.bShowUndiscoveredMissions = False

    def Disable(self) -> None:
        unrealsdk.RemoveHook("WillowGame.WillowPlayerController.PostBeginPlay", "HideUndiscoveredMissions")
        unrealsdk.GetEngine().GamePlayers[0].Actor.bShowUndiscoveredMissions = True


instance = HideUndiscoveredMissions()
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
