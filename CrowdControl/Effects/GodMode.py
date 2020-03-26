import unrealsdk
from typing import ClassVar

from . import DurationCrowdControlEffect, JSON, QueuedCrowdControlEffect
from Mods import AsyncUtil
from Mods.UserFeedback import ShowHUDMessage


class GodMode(DurationCrowdControlEffect):
    Name: ClassVar[str] = "God Mode"
    Description: ClassVar[str] = (
        "Makes all players invincible."
    )

    Duration: ClassVar[int] = 15
    Interval: ClassVar[int] = 15

    def OnStart(self, msg: JSON) -> None:
        self.ShowRedemption(msg)

        def BlockCall(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            return False

        unrealsdk.RunHook("WillowGame.WillowPlayerPawn.TakeDamage", "CCGodMode", BlockCall)

    def OnEnd(self) -> None:
        ShowHUDMessage("Crowd Control", f"{self.Name} wore off.")
        unrealsdk.RemoveHook("WillowGame.WillowPlayerPawn.TakeDamage", "CCGodMode")


class FakeGodMode(QueuedCrowdControlEffect):
    Name: ClassVar[str] = "Fake God Mode"
    Description: ClassVar[str] = (
        "Displays a message as if it's going to activate God Mode, but does nothing."
    )

    FakeName: ClassVar[str] = "God Mode"

    def OnRun(self, msg: JSON) -> None:
        # Replicate `self.ShowRedemption()` but using the fake name
        def Internal() -> None:
            user = "Unknown user"
            try:
                user = msg["data"]["redemption"]["user"]["login"]
            except KeyError:
                pass
            ShowHUDMessage(
                "Crowd Control",
                f"{user} redeemed '{self.FakeName}'"
            )
        AsyncUtil.RunIn(0.1, Internal)
