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
        pawn = unrealsdk.GetEngine().GamePlayers[0].Actor.Pawn

        # Only activate if in FFYL
        if pawn.bIsInjured and not pawn.bIsDead:
            pawn.GoFromInjuredToHealthy()
            pawn.ClientOnRevived()
