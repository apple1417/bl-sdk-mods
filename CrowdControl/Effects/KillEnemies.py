import unrealsdk
from typing import ClassVar

from . import JSON, QueuedCrowdControlEffect


class KillEnemies(QueuedCrowdControlEffect):
    Name: ClassVar[str] = "Kill Enemies"
    Description: ClassVar[str] = (
        "Sets all non-player health pools to zero."
        " This normally means it kills all enemies, but in some cases it may kill friendlies too."
        " Does not affect objects with health such as barrels."
    )

    Interval: ClassVar[int] = 15

    def OnRun(self, msg: JSON) -> None:
        self.ShowRedemption(msg)
        playerPools = []
        # Unintuitively, `unrealsdk.GetEngine().GamePlayers` does not hold remote players
        for pawn in unrealsdk.FindAll("WillowPlayerPawn"):
            if pawn.HealthPool.Data is not None:
                playerPools.append(pawn.HealthPool.Data)
        for pool in unrealsdk.FindAll("HealthResourcePool"):
            if pool in playerPools:
                continue
            pool.CurrentValue = 0
