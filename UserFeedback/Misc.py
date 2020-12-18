import unrealsdk
from datetime import datetime
from typing import Optional


def ShowHUDMessage(Title: str, Message: str, Duration: float = 2, MenuHint: int = 0) -> None:
    """
    Displays a small training message on the left side of the screen, like those used for the
     respawn cost messages.

    Note that this should not be used for critical messages. It only works while the main game HUD
     is shown, so it will silently fail if the user is in any menu. Additionally, if another message
     is shown (including ones the game creates) it will immediately be overwritten.

    Args:
        Title: The title of the training message.
        Message: The message to be shown in the main body of the training message.
        Duration: How long the training message should be shown for (in seconds). Defaults to 2.
        MenuHint:
            If to display a hint to open your menu, and what menu should be opened when you do.
             Defaults to 0, no hint. 1-5 represent the different the different menu tabs, in the
             same order as the game: Missions; Map; Inventory; Skills; BAR. Defaults to 0.
    """
    PC = unrealsdk.GetEngine().GamePlayers[0].Actor
    hud_movie = PC.GetHUDMovie()

    if hud_movie is None:
        return

    hud_movie.ClearTrainingText()
    hud_movie.AddTrainingText(
        Message,
        Title,
        Duration,
        (),
        "",
        False,
        0,
        PC.PlayerReplicationInfo,
        True,
        MenuHint
    )


def ShowChatMessage(
    User: str,
    Message: str,
    Timestamp: Optional[datetime] = None,
    ShowTimestamp: bool = True
) -> None:
    if Timestamp is None:
        Timestamp = datetime.now()  # noqa N806

    is12h = unrealsdk.FindAll("WillowSaveGameManager")[0].TimeFormat == "12"
    time_str = Timestamp.strftime(("[%H:%M:%S]", "[%I:%M:%S%p]")[is12h]).lower()

    user_str = f"{User} {time_str}" if ShowTimestamp else User

    chat_movie = unrealsdk.GetEngine().GamePlayers[0].Actor.GetTextChatMovie()
    chat_movie.AddChatMessageInternal(user_str, Message)
