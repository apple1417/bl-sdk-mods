import bl2sdk
from typing import List


class HideUndiscoveredMissions(bl2sdk.BL2MOD):
    Name: str = "Hide Undiscovered Missions"
    Author: str = "apple1417"
    Description: str = (
        "Hides undiscoved missions in the mission log."
    )
    Types: List[bl2sdk.ModTypes] = [bl2sdk.ModTypes.Utility]
    Version = "1.0"

    def __init__(self) -> None:
        # Hopefully I can remove this in a future SDK update
        self.Author += "\nVersion: " + str(self.Version)

    def Enable(self) -> None:
        def PostBeginPlay(caller: bl2sdk.UObject, function: bl2sdk.UFunction, params: bl2sdk.FStruct) -> bool:
            # Re-run the function so we can modify it after it's done
            bl2sdk.DoInjectedCallNext()
            caller.PostBeginPlay()

            caller.bShowUndiscoveredMissions = False
            return False

        bl2sdk.RegisterHook("WillowGame.WillowPlayerController.PostBeginPlay", "HideUndiscoveredMissions", PostBeginPlay)
        bl2sdk.GetEngine().GamePlayers[0].Actor.bShowUndiscoveredMissions = False

    def Disable(self) -> None:
        bl2sdk.RemoveHook("WillowGame.WillowPlayerController.PostBeginPlay", "HideUndiscoveredMissions")
        bl2sdk.GetEngine().GamePlayers[0].Actor.bShowUndiscoveredMissions = True


bl2sdk.Mods.append(HideUndiscoveredMissions())
