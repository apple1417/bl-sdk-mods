import unrealsdk
import random
from typing import ClassVar

from Mods import AsyncUtil

from . import JSON, QueuedCrowdControlEffect


class DropWeapon(QueuedCrowdControlEffect):
    Name: ClassVar[str] = "Drop Weapon"
    Description: ClassVar[str] = (
        "Drops your currently equipped weapon."
    )

    Interval: ClassVar[int] = 15

    DISPLAY_DELAY: ClassVar[float] = 1.5

    def OnRun(self, msg: JSON) -> None:
        unrealsdk.GetEngine().GamePlayers[0].Actor.ServerThrowPawnActiveWeapon()
        AsyncUtil.RunIn(self.DISPLAY_DELAY, lambda: self.ShowRedemption(msg))


class DropAll(QueuedCrowdControlEffect):
    Name: ClassVar[str] = "Drop All Weapons"
    Description: ClassVar[str] = (
        "Drops all your currently equipped weapons."
    )

    Interval: ClassVar[int] = 15

    DISPLAY_DELAY: ClassVar[float] = 0.5
    DROP_DELAY: ClassVar[float] = 1.5
    DROP_VARIATION: ClassVar[float] = 1

    def OnRun(self, msg: JSON) -> None:
        time: float = 0
        for i in range(4):
            time += max(0, random.uniform(
                self.DROP_DELAY - self.DROP_VARIATION,
                self.DROP_DELAY - self.DROP_VARIATION
            ))
            AsyncUtil.RunIn(
                time,
                unrealsdk.GetEngine().GamePlayers[0].Actor.ServerThrowPawnActiveWeapon
            )
            if i == 1:
                AsyncUtil.RunIn(time + self.DISPLAY_DELAY, lambda: self.ShowRedemption(msg))
