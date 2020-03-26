import unrealsdk
from typing import ClassVar

from . import IsInGame, JSON, QueuedCrowdControlEffect
from Mods import AsyncUtil


class FFYL(QueuedCrowdControlEffect):
    Name: ClassVar[str] = "FFYL Players"
    Description: ClassVar[str] = (
        "Puts all players in the game into FFYL."
    )

    Interval: ClassVar[int] = 15
    TIME_BEFORE_ACTIVATE: ClassVar[float] = 2

    def OnRun(self, msg: JSON) -> None:
        self.ShowRedemption(msg)
        AsyncUtil.RunIn(self.TIME_BEFORE_ACTIVATE, lambda: AsyncUtil.RunWhen(IsInGame, self.Activate))

    def Activate(self) -> None:
        for pawn in unrealsdk.FindAll("WillowPlayerPawn"):
            if pawn.HealthPool.Data is not None:
                pawn.HealthPool.Data.CurrentValue = 0


class KillPlayers(FFYL):
    Name: ClassVar[str] = "Kill Players"
    Description: ClassVar[str] = (
        "Kills all players in the game."
    )

    def Activate(self) -> None:
        for controller in unrealsdk.FindAll("WillowPlayerController"):
            if controller.Name.startswith("Default__"):
                continue
            controller.CausePlayerDeath(True)
