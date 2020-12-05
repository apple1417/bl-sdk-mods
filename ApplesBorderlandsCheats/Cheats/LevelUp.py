import unrealsdk

from Mods.UserFeedback import ShowHUDMessage

from . import ABCCheat


class LevelUp(ABCCheat):
    Name = "Level Up"
    KeybindName = "Level Up"

    def OnPress(self) -> None:
        PC = unrealsdk.GetEngine().GamePlayers[0].Actor
        if PC.IsResourcePoolValid((
            PC.ExpPool.PoolManager,
            PC.ExpPool.PoolIndexInManager,
            PC.ExpPool.PoolGUID,
            PC.ExpPool.Data
        )):
            PC.ExpPool.Data.SetCurrentValue(0)
        PC.OnExpLevelChange(True, False)
        PC.ExpEarn(PC.GetExpPointsRequiredForLevel(PC.PlayerReplicationInfo.ExpLevel + 1), 0)
        PC.ExpPool.Data.ApplyExpPointsToExpLevel(True)


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
