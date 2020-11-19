import unrealsdk
from typing import ClassVar

from Mods.UserFeedback import ShowHUDMessage

from . import JSON, DurationCrowdControlEffect, IsInGame


class SuperSpeed(DurationCrowdControlEffect):
    Name: ClassVar[str] = "Super Speed"
    Description: ClassVar[str] = (
        "Greatly increases your movement speed for 15s."
        " Wears off early if you die or enter a vehicle,"
        " keeps going past when it wears off if you don't stop moving."
    )

    Duration: ClassVar[int] = 15
    Interval: ClassVar[int] = 15

    NewSpeed: ClassVar[int] = 40000

    IsRunning: bool
    GroundSpeedBaseValue: int
    AccelRate: int

    def __init__(self) -> None:
        super().__init__()
        self.IsRunning = False
        # Default values for if somehow this ends up deactivating first
        self.GroundSpeedBaseValue = 440
        self.AccelRate = 2048

    def OnStart(self, msg: JSON) -> None:
        self.ShowRedemption(msg)

        PC = unrealsdk.GetEngine().GamePlayers[0].Actor
        PC.ServerRCon(f"set {PC.PathName(PC.Pawn)} GroundSpeedBaseValue {self.NewSpeed}")
        PC.ServerRCon(f"set {PC.PathName(PC.Pawn)} AccelRate {self.NewSpeed}")

    def OnEnd(self) -> None:
        ShowHUDMessage("Crowd Control", f"{self.Name} wore off.")

        PC = unrealsdk.GetEngine().GamePlayers[0].Actor
        PC.ServerRCon(f"set {PC.PathName(PC.Pawn)} GroundSpeedBaseValue {self.GroundSpeedBaseValue}")
        PC.ServerRCon(f"set {PC.PathName(PC.Pawn)} AccelRate {self.AccelRate}")

    def Condition(self) -> bool:
        if not IsInGame():
            return False
        return not unrealsdk.GetEngine().GamePlayers[0].Actor.IsUsingVehicle(True)
