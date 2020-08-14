import unrealsdk
from typing import ClassVar

from . import IsInGame, JSON, QueuedCrowdControlEffect


class Revive(QueuedCrowdControlEffect):
    Name: ClassVar[str] = "Instant Revive"
    Description: ClassVar[str] = (
        "The next time you go down you will instantly be revived."
    )

    Interval: ClassVar[int] = 1

    def OnRedeem(self, msg: JSON) -> None:
        super().OnRedeem(msg)
        self.ShowRedemption(msg)

    def OnRun(self, msg: JSON) -> None:
        pawn = unrealsdk.GetEngine().GamePlayers[0].Actor.Pawn
        pawn.GoFromInjuredToHealthy()
        pawn.ClientOnRevived()

    def Condition(self) -> bool:
        if not IsInGame():
            return False
        PC = unrealsdk.GetEngine().GamePlayers[0].Actor
        if PC is None or PC.Pawn is None:
            return False
        return PC.Pawn.bIsInjured and not PC.Pawn.bIsDead
