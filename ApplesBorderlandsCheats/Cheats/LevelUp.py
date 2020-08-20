import unrealsdk

from . import ABCCheat
from Mods.UserFeedback import ShowHUDMessage


class LevelUp(ABCCheat):
    Name = "Level Up"
    KeybindName = "Level Up"

    def OnPress(self) -> None:
        unrealsdk.GetEngine().GamePlayers[0].Actor.ExpLevelUp(True)


class OPLevel(ABCCheat):
    Name = "Add OP Level"
    KeybindName = "Add OP Level"

    def OnPress(self) -> None:
        pc = unrealsdk.GetEngine().GamePlayers[0].Actor
        pri = pc.PlayerReplicationInfo
        if pri.NumOverpowerLevelsUnlocked == pc.GetMaximumPossibleOverpowerModifier():
            ShowHUDMessage(
                self.Name,
                "You are already at the maximum OP level"
            )
        else:
            pri.NumOverpowerLevelsUnlocked += 1
            ShowHUDMessage(
                self.Name,
                f"You have now unlocked OP {pri.NumOverpowerLevelsUnlocked}"
            )
