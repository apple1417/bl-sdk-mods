import unrealsdk
from typing import ClassVar

from Mods import AsyncUtil
from Mods.UserFeedback import ShowChatMessage

from . import JSON, DurationCrowdControlEffect


class ManualReloads(DurationCrowdControlEffect):
    Name: ClassVar[str] = "Hide HUD"
    Description: ClassVar[str] = (
        "Hides the HUD for 15s."
    )

    Duration: ClassVar[int] = 15
    Interval: ClassVar[int] = 15

    def OnStart(self, msg: JSON) -> None:
        user = "Unknown user"
        try:
            user = msg["data"]["redemption"]["user"]["login"]
        except KeyError:
            pass
        # Can't exactly show this on the hud, we'll let other messages stay hidden though :)
        ShowChatMessage("Crowd Control:", f"{user} redeemed '{self.Name}'", ShowTimestamp=False)

        unrealsdk.GetEngine().GamePlayers[0].Actor.HideHUD()

        def BlockCall(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            return False

        # Pausing/unpausing will make it show again so got to block that
        unrealsdk.RunHook("WillowGame.WillowHUDGFxMovie.Start", "CCHideHUD", BlockCall)

    def OnEnd(self) -> None:
        ShowChatMessage("Crowd Control:", f"{self.Name} wore off.", ShowTimestamp=False)

        unrealsdk.RemoveHook("WillowGame.WillowHUDGFxMovie.Start", "CCHideHUD")
        # Seems the hook sticks around a tick or something, this doesn't work unless I delay it
        AsyncUtil.RunIn(0.05, unrealsdk.GetEngine().GamePlayers[0].Actor.DisplayHUD)
