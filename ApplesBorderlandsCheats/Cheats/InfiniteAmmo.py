import unrealsdk
from typing import ClassVar, Dict

from . import ABCCycleableCheat, SDKHook


class InfiniteAmmo(ABCCycleableCheat):
    Name = "Infinite Ammo"
    KeybindName = "Cycle Infinite Ammo"

    OFF: ClassVar[str] = "Off"
    RELOADS: ClassVar[str] = "Free Reloads"
    FULL: ClassVar[str] = "Full"
    AllValues = (OFF, RELOADS, FULL)

    def GetHooks(self) -> Dict[str, SDKHook]:
        # For weapons
        def ConsumeAmmo(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            pc = unrealsdk.GetEngine().GamePlayers[0].Actor
            if pc is None or pc.Pawn is None:
                return True
            if caller not in (pc.Pawn.Weapon, pc.Pawn.OffHandWeapon):
                return True

            if self.CurrentValue == InfiniteAmmo.FULL:
                caller.RefillClip()
            return self.CurrentValue == InfiniteAmmo.OFF

        # For grenades
        def ConsumeProjectileResource(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            if caller != unrealsdk.GetEngine().GamePlayers[0].Actor:
                return True
            return self.CurrentValue == InfiniteAmmo.OFF

        return {
            "WillowGame.WillowWeapon.ConsumeAmmo": ConsumeAmmo,
            "WillowGame.WillowPlayerController.ConsumeProjectileResource": ConsumeProjectileResource,
        }
