import unrealsdk
from typing import ClassVar

from . import DurationCrowdControlEffect, JSON
from Mods.UserFeedback import ShowHUDMessage


class ManualReloads(DurationCrowdControlEffect):
    Name: ClassVar[str] = "Manual Reloads"
    Description: ClassVar[str] = (
        "Turns off automatic reloads."
    )

    Duration: ClassVar[int] = 15
    Interval: ClassVar[int] = 15

    def OnStart(self, msg: JSON) -> None:
        self.ShowRedemption(msg)

        def BlockCall(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            return False

        unrealsdk.RunHook("WillowGame.WillowWeapon.ShouldAutoReloadWhileFiring", "CCManualReloads", BlockCall)

    def OnEnd(self) -> None:
        ShowHUDMessage("Crowd Control", f"{self.Name} wore off.")
        unrealsdk.RemoveHook("WillowGame.WillowWeapon.ShouldAutoReloadWhileFiring", "CCManualReloads")
