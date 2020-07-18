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
        PC = unrealsdk.GetEngine().GamePlayers[0].Actor
        rep = PC.PlayerReplicationInfo
        if rep.NumOverpowerLevelsUnlocked == PC.GetMaximumPossibleOverpowerModifier():
            ShowHUDMessage(
                self.Name,
                "You are already at the maximum OP level"
            )
        else:
            rep.NumOverpowerLevelsUnlocked += 1
            ShowHUDMessage(
                self.Name,
                f"You have now unlocked OP {rep.NumOverpowerLevelsUnlocked}"
            )
