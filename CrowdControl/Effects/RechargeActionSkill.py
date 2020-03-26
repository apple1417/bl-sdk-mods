import unrealsdk
from typing import ClassVar, cast

from . import IsInGame, JSON, QueuedCrowdControlEffect


class RechargeActionSkill(QueuedCrowdControlEffect):
    Name: ClassVar[str] = "Recharge Action Skill"
    Description: ClassVar[str] = (
        "Instantly recharges your action skill next time it goes on cooldown."
    )

    Interval: ClassVar[int] = 1

    def OnRedeem(self, msg: JSON) -> None:
        super().OnRedeem(msg)
        self.ShowRedemption(msg)

    def OnRun(self, msg: JSON) -> None:
        unrealsdk.GetEngine().GamePlayers[0].Actor.ResetSkillCooldown()

    def Condition(self) -> bool:
        if not IsInGame():
            return False
        PC = unrealsdk.GetEngine().GamePlayers[0].Actor
        if PC is None:
            return False
        return cast(bool, PC.IsActionSkillOnCooldown())
