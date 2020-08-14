import unrealsdk
import math as maths
from typing import ClassVar

from . import JSON, QueuedCrowdControlEffect
from Mods import AsyncUtil


class Jump(QueuedCrowdControlEffect):
    Name: ClassVar[str] = "Jump Forwards"
    Description: ClassVar[str] = (
        "Makes you jump forwards."
    )

    Interval: ClassVar[int] = 15

    MIN_VELOCITY: ClassVar[int] = 550

    def OnRun(self, msg: JSON) -> None:
        def Internal() -> None:
            self.ShowRedemption(msg)
            PC = unrealsdk.GetEngine().GamePlayers[0].Actor

            wanted_vel = max(self.MIN_VELOCITY, maths.sqrt(PC.Pawn.Velocity.X ** 2 + PC.Pawn.Velocity.Y ** 2))
            conversion = maths.pi / 0x7fff

            PC.Pawn.DoJump(PC.bUpdating)

            PC.Pawn.Velocity = (
                maths.cos(PC.Rotation.Yaw * conversion) * wanted_vel,
                maths.sin(PC.Rotation.Yaw * conversion) * wanted_vel,
                PC.Pawn.Velocity.Z  # This now includes jumping velocity
            )

        # There's a bit of a delay after unpausing before this works right
        AsyncUtil.RunIn(0.2, Internal)
