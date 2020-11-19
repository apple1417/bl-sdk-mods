from datetime import datetime
from typing import ClassVar

from Mods.UserFeedback import ShowChatMessage

from . import JSON, BaseCrowdControlEffect


class Chat(BaseCrowdControlEffect):
    Name: ClassVar[str] = "Chat"
    Description: ClassVar[str] = (
        "Sends chat messages into the game."
        " Make sure you require the user to enter text for this reward."
    )

    def OnRedeem(self, msg: JSON) -> None:
        user = "Unknown user"
        timestamp = ""
        chat_msg = ""
        try:
            user = msg["data"]["redemption"]["user"]["login"]
            chat_msg = msg["data"]["redemption"]["user_input"]
            timestamp = msg["data"]["redemption"]["redeemed_at"]
        except KeyError:
            pass

        try:
            utcoffset = datetime.now() - datetime.utcnow()
            # Twitch actually provides nanoseconds, but there's no format string for that so have to
            #  remove it to avoid "unconverted data remains" ValueErrors
            time = datetime.strptime(timestamp[:-4], "%Y-%m-%dT%H:%M:%S.%f") + utcoffset
        except ValueError:
            time = datetime.now()

        ShowChatMessage(user, chat_msg, time)
