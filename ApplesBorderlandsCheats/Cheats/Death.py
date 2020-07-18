import unrealsdk

from . import ABCCheat


class Suicide(ABCCheat):
    Name = "Suicide"
    KeybindName = "Suicide"

    def OnPress(self) -> None:
        unrealsdk.GetEngine().GamePlayers[0].Actor.CausePlayerDeath(True)


class ReviveSelf(ABCCheat):
    Name = "Revive Self"
    KeybindName = "Revive Self"

    def OnPress(self) -> None:
        Pawn = unrealsdk.GetEngine().GamePlayers[0].Actor.Pawn

        # Only activate if in FFYL
        if Pawn.bIsInjured and not Pawn.bIsDead:
            Pawn.GoFromInjuredToHealthy()
            Pawn.ClientOnRevived()
