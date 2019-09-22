import bl2sdk
from typing import Callable, Optional, Sequence
from typing import NamedTuple


def ShowTrainingMessage(Title: str, Message: str, Duration: float = 2) -> None:
    """
    Displays a small feedback message on the left side of the screen, like those used for the
     respawn cost messages.

    Note that this may fail if the user is in a menu.

    Parameters
    ----------
    Title: str
        The title of the feedback message.
    Message: str
        The message to be shown in the main body of the feedback message.
    Duration: float
        How long the feedback message should be shown for (in seconds). This does not include the
          time it takes for the appear and disappear animations. Defaults to 2.
    """

    _RawShowTrainingMessage(Title, Message, Duration, False, 0)

def ShowPausedTrainingMessage(Title: str, Message: str, MinDuration: float = 0) -> None:
    """
    Pauses the game and displays a feedback message in the center of the screen, like those used for
     the special edition items message.

    Note that this may fail if the user is in a menu.

    Parameters
    ----------
    Title: str
        The title of the feedback message.
    Message: str
        The message to be shown in the main body of the feedback message.
    MinDuration: float
        How long the feedback message should be shown (in seconds) before you are alowed to exit out
         of it. Defaults to 0.
    """

    _RawShowTrainingMessage(Title, Message, 1, True, MinDuration)

""" This function actually does the work for the previous two wrappers """
def _RawShowTrainingMessage(
    Title: str,
    Message: str,
    Duration: float,
    PausesGame: bool,
    PauseContinueDelay: float
) -> None:
    PC = bl2sdk.GetEngine().GamePlayers[0].Actor
    HUDMovie = PC.GetHUDMovie()

    if HUDMovie is None:
        return

    HUDMovie.ClearTrainingText()
    HUDMovie.AddTrainingText(
        Message,
        Title,
        Duration,
        (),
        "",
        PausesGame,
        PauseContinueDelay,
        PC.PlayerReplicationInfo,
        True
    )



class DialogBoxButton(NamedTuple):
    """
    A simple dataclass used with Dialog Boxes.

    Fields
    ------
    Name: str
        The name that the button should have.
    Tip: str
        A string that is added to the dialog box caption when hovering over this button.
    """

    Name: str
    Tip: str


def ShowDialogBox(*,
    Title: str,
    Buttons: Sequence[DialogBoxButton],
    DefaultButtonIndex: int = 0,
    Callback: Optional[Callable[[Optional[DialogBoxButton]], None]] = None,
    Caption: str = "",
    PreventCanceling: bool = False,
    Tooltip: Optional[str] = None,
) -> None:
    """
    Shows a dialog box with multiple possible options for the user to select from, like those used
     to select playthrough or to confirm quitting.
    This does not pause the game.

    Parameters
    ----------
    Title: str
        The title of the dialog box.
    Buttons: Sequence[DialogBoxButton]
        A list of DialogBoxButtons that this dialog should display. You must provide at least one
         button and at most five.
    DefaultButtonIndex: int
        The index of the button that should initially be selected. Defaults to 0.
    Callback: Optional[Callable[[Optional[DialogBoxButton]], None]]
        An optional function that is called on the DialogBoxButton that the user pressed. If the
         user canceled out of the menu it will be called on `None`.
    Caption: str
        The caption to be shown in the main body of the dialog box.
    PreventCanceling: bool
        If the user should be allowed to cancel out of the dialog box without selecteding anything.
        Defaults to `False`
    Tooltip: Optional[str]
        The tooltip to display at the bottom of the dialog box. If not defined it will be left as
         the game's default tooltip ('[Enter] Select  [Escape] Cancel' in English).
    """

    # Check we have valid input
    for b in Buttons:
        if not isinstance(b, DialogBoxButton):
            raise TypeError(f"Dialog box was not passed sequence of DialogBoxButtons")
    if len(Buttons) == 0 or len(Buttons) > 5:
        raise ValueError("A dialog box must have 1-5 buttons")
    if 0 > DefaultButtonIndex <= len(Buttons):
        raise IndexError("Default button index out of range")

    # A default dialog box that you can't exit out of will open after this call
    # This is why we have to do all the input checking beforehand
    dialog: bl2sdk.UObject = bl2sdk.GetEngine().GamePlayers[0].Actor.GFxUIManager.ShowDialog()

    # Now we can customize the dialog box
    dialog.SetText(Title, Caption)
    dialog.bNoCancel = PreventCanceling

    # There is a default tooltip, so we'll only overwrite it if actually provided one
    if Tooltip is not None:
        dialog.SetTooltips(Tooltip)

    # We give each button a custom tag so that you can add two with the same name
    for idx in range(len(Buttons)):
        dialog.AppendButton(f"Button{idx}", Buttons[idx].Name, Buttons[idx].Tip)

    dialog.SetDefaultButton(f"Button{DefaultButtonIndex}", True)
    dialog.ApplyLayout();

    # One of these two functions is called when you exit the dialog
    def Accepted(caller: bl2sdk.UObject, function: bl2sdk.UFunction, params: bl2sdk.FStruct) -> bool:
        if Callback is not None:
            Callback(Buttons[dialog.CurrentSelection])
        bl2sdk.RemoveHook("WillowGame.WillowGFxDialogBox.Accepted", "CustomDialogBox")
        bl2sdk.RemoveHook("WillowGame.WillowGFxDialogBox.Cancelled", "CustomDialogBox")
        return True

    def Cancelled(caller: bl2sdk.UObject, function: bl2sdk.UFunction, params: bl2sdk.FStruct) -> bool:
        if Callback is not None:
            Callback(None)
        bl2sdk.RemoveHook("WillowGame.WillowGFxDialogBox.Accepted", "CustomDialogBox")
        bl2sdk.RemoveHook("WillowGame.WillowGFxDialogBox.Cancelled", "CustomDialogBox")
        return True

    bl2sdk.RegisterHook("WillowGame.WillowGFxDialogBox.Accepted", "CustomDialogBox", Accepted)
    bl2sdk.RegisterHook("WillowGame.WillowGFxDialogBox.Cancelled", "CustomDialogBox", Cancelled)
