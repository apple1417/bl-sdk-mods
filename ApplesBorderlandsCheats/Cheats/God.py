import unrealsdk
from typing import ClassVar, Dict

from . import ABCCycleableCheat, SDKHook


class GodMode(ABCCycleableCheat):
    Name = "God Mode"
    KeybindName = "Cycle God Mode"

    OFF: ClassVar[str] = "Off"
    ALLOWDAMAGE: ClassVar[str] = "1 HP"
    FULL: ClassVar[str] = "Full"
    AllValues = (OFF, ALLOWDAMAGE, FULL)

    def GetHooks(self) -> Dict[str, SDKHook]:
        # Blocking this function stops knockback for full god mode
        def TakeDamage(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            if caller != unrealsdk.GetEngine().GamePlayers[0].Actor.Pawn:
                return True

            return self.CurrentValue != GodMode.FULL

        def SetHealth(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            if caller != unrealsdk.GetEngine().GamePlayers[0].Actor.Pawn:
                return True

            if self.CurrentValue == GodMode.FULL:
                # The previous function should prevent getting here, but just in case
                return False
            elif self.CurrentValue == GodMode.ALLOWDAMAGE:
                if params.NewHealth < 1:
                    unrealsdk.DoInjectedCallNext()
                    caller.SetHealth(1)
                    return False

            return True

        return {
            "WillowGame.WillowPlayerPawn.TakeDamage": TakeDamage,
            "Engine.Pawn.SetHealth": SetHealth
        }
