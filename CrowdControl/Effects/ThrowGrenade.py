import unrealsdk
from typing import ClassVar

from . import JSON, QueuedCrowdControlEffect


class ThrowGrenade(QueuedCrowdControlEffect):
    Name: ClassVar[str] = "Throw Grenade"
    Description: ClassVar[str] = (
        "Throws a grenade."
    )

    Interval: ClassVar[int] = 15

    def OnRun(self, msg: JSON) -> None:
        self.ShowRedemption(msg)
        PC = unrealsdk.GetEngine().GamePlayers[0].Actor

        PC.ThrowGrenade(PC.GetCurrentProjectileDefinition())
