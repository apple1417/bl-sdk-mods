import unrealsdk
from typing import ClassVar, cast

from . import JSON, IsInGame, QueuedCrowdControlEffect


class RefillClip(QueuedCrowdControlEffect):
    Name: ClassVar[str] = "Refill Clip"
    Description: ClassVar[str] = (
        "Refills your weapon clip next time it reaches 0, without reloading."
    )

    Interval: ClassVar[int] = 1

    def OnRedeem(self, msg: JSON) -> None:
        super().OnRedeem(msg)
        self.ShowRedemption(msg)

    def OnRun(self, msg: JSON) -> None:
        unrealsdk.GetEngine().GamePlayers[0].Actor.Pawn.Weapon.RefillClip()

    def Condition(self) -> bool:
        if not IsInGame():
            return False
        pawn = unrealsdk.GetEngine().GamePlayers[0].Actor.Pawn
        if pawn is None:
            return False
        weapon = pawn.Weapon
        if weapon is None:
            return False
        return cast(bool, weapon.ReloadCnt <= 0)
