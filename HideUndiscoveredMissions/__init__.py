import unrealsdk

from Mods.ModMenu import EnabledSaveType, Mods, ModTypes, RegisterMod, SDKMod


class HideUndiscoveredMissions(SDKMod):
    Name: str = "Hide Undiscovered Missions"
    Author: str = "apple1417"
    Description: str = (
        "Hides undiscoved missions in the mission log."
    )
    Version: str = "1.2"

    Types: ModTypes = ModTypes.Utility
    SaveEnabledState: EnabledSaveType = EnabledSaveType.LoadWithSettings

    def Enable(self) -> None:
        def PostBeginPlay(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            unrealsdk.DoInjectedCallNext()
            caller.PostBeginPlay()

            caller.bShowUndiscoveredMissions = False
            return False

        unrealsdk.RegisterHook("WillowGame.WillowPlayerController.PostBeginPlay", self.Name, PostBeginPlay)
        unrealsdk.GetEngine().GamePlayers[0].Actor.bShowUndiscoveredMissions = False

    def Disable(self) -> None:
        unrealsdk.RemoveHook("WillowGame.WillowPlayerController.PostBeginPlay", self.Name)
        unrealsdk.GetEngine().GamePlayers[0].Actor.bShowUndiscoveredMissions = True


instance = HideUndiscoveredMissions()
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
