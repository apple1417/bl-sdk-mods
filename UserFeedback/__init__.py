import bl2sdk
from typing import List, Optional, Sequence


def ShowTrainingMessage(Title: str, Message: str, Duration: float = 2) -> None:
    """
    Displays a small training message on the left side of the screen, like those used for the
     respawn cost messages.

    Note that this may fail if the user is in a menu.

    Args:
        Title: The title of the training message.
        Message: The message to be shown in the main body of the training message.
        Duration:
            How long the training message should be shown for (in seconds). This does not include
             the time it takes for the appear and disappear animations. Defaults to 2.
    """

    _RawShowTrainingMessage(Title, Message, Duration, False, 0)


def ShowPausedTrainingMessage(Title: str, Message: str, MinDuration: float = 0) -> None:
    """
    Pauses the game and displays a training message in the center of the screen, like those used for
     the special edition items message.

    Note that this may fail if the user is in a menu.

    Args:
        Title: The title of the training message.
        Message: The message to be shown in the main body of the training message.
        MinDuration:
            How long the training message should be shown (in seconds) before you are alowed to exit
             out of it. Defaults to 0.
    """

    _RawShowTrainingMessage(Title, Message, 1, True, MinDuration)


# This function actually does the work for the previous two wrappers
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


class DialogBoxButton:
    """
    A simple dataclass representing a button.

    Attributes:
        Name: The name that the button should have.
        Tip: A string that is added to the dialog box caption when hovering over this button.
    """
    Name: str
    Tip: str

    def __init__(self, Name: str, Tip: str = ""):
        self.Name = Name
        self.Tip = Tip

    def __repr__(self) -> str:
        return f"DialogBoxButton(Name='{self.Name}', Tip='{self.Tip}')"


class _Page:
    """
    Class representing a single 'page' dialog box. You should probably use DialogBox over this.

    This behaves almost the exact same way as DialogBox. The main differences are that it's limited
     to no more than 5 buttons, that you don't need to call Update() when you change attributes,
     and that it uses a DefaultButtonIndex field rather than having a special show method.

    You should only really use this class if you want to create your own logic for multiple pages.
    """
    Title: str
    Caption: str
    Tooltip: str
    Buttons: Sequence[DialogBoxButton]
    DefaultButtonIndex: int
    PreventCanceling: bool

    _Dialog: Optional[bl2sdk.UObject]

    def __init__(
        self, *,
        Title: str,
        Caption: str = "",
        # Default tooltip the game uses
        Tooltip: str = "<StringAliasMap:GFx_Accept> Select     <StringAliasMap:GFx_Cancel> Cancel",
        Buttons: Sequence[DialogBoxButton],
        DefaultButtonIndex: int = 0,
        PreventCanceling: bool = False,
    ) -> None:
        # Check we actually have a sequence of buttons - everything else can use a builtin converter
        try:
            for b in Buttons:
                if not isinstance(b, DialogBoxButton):
                    raise TypeError
        except TypeError as e:
            raise ValueError(
                f"'{Buttons}' is not a sequence of Buttons"
            ).with_traceback(e.__traceback__)
        if 1 > len(Buttons) > 5:
            raise ValueError("A single dialog box must have 1-5 buttons")
        if 0 > int(DefaultButtonIndex) <= len(Buttons):
            raise IndexError("Default button index out of range")

        self.Title = str(Title)
        self.Caption = str(Caption)
        self.Tooltip = str(Tooltip)
        self.Buttons = Buttons
        self.DefaultButtonIndex = int(DefaultButtonIndex)
        self.PreventCanceling = bool(PreventCanceling)

        self._Dialog = None

    def Show(self) -> None:
        self._Dialog = bl2sdk.GetEngine().GamePlayers[0].Actor.GFxUIManager.ShowDialog()

        self._Dialog.SetText(self.Title, self.Caption)
        self._Dialog.bNoCancel = self.PreventCanceling
        self._Dialog.SetTooltips(self.Tooltip)

        # We give each button a custom tag so that you can add two with the same name
        for idx in range(len(self.Buttons)):
            self._Dialog.AppendButton(f"Button{idx}", self.Buttons[idx].Name, self.Buttons[idx].Tip)

        self._Dialog.SetDefaultButton(f"Button{self.DefaultButtonIndex}", True)
        self._Dialog.ApplyLayout()

        # One of these two functions is called when you exit the dialog
        # We run callbacks after removing hooks so that you can immediately show a new dialog box
        def Accepted(caller: bl2sdk.UObject, function: bl2sdk.UFunction, params: bl2sdk.FStruct) -> bool:
            bl2sdk.RemoveHook("WillowGame.WillowGFxDialogBox.Accepted", "CustomDialogBox")
            bl2sdk.RemoveHook("WillowGame.WillowGFxDialogBox.Cancelled", "CustomDialogBox")
            self.OnPress(self.Buttons[int(caller.CurrentSelection)])
            self._Dialog = None
            return True

        def Cancelled(caller: bl2sdk.UObject, function: bl2sdk.UFunction, params: bl2sdk.FStruct) -> bool:
            bl2sdk.RemoveHook("WillowGame.WillowGFxDialogBox.Accepted", "CustomDialogBox")
            bl2sdk.RemoveHook("WillowGame.WillowGFxDialogBox.Cancelled", "CustomDialogBox")
            self.OnCancel()
            self._Dialog = None
            return True

        bl2sdk.RegisterHook("WillowGame.WillowGFxDialogBox.Accepted", "CustomDialogBox", Accepted)
        bl2sdk.RegisterHook("WillowGame.WillowGFxDialogBox.Cancelled", "CustomDialogBox", Cancelled)

    def OnPress(self, button: DialogBoxButton) -> None:
        pass

    def OnCancel(self) -> None:
        pass


class DialogBox:
    """
    Class representing a dialog box with multiple options to chose from, like those used to select
     playthrough or confirm quitting.

    If you provide more buttons than a single box can handle it will automatically create multiple
     pages with a button to cycle between them.

    See https://i.imgur.com/E5TOicS.png for examples of what the various sections of the dialog box
     are called.

    Attributes:
        Title: The title text to display at the top of the dialog box.
        Caption: The text to display in the main body of the dialog box.
        Tooltip: The text to display in the footer of the dialog box.
        Buttons: A sequence of buttons that the user should pick from.
        PreventCanceling:
            If the user should be prevented from pressing ESC to cancel out of the dialog
             without selecting anything.
    """

    @staticmethod
    def CreateTooltipString(EnterMessage: str = "Select", EscMessage: str = "Cancel") -> str:
        """
        Creates a tooltip string in the same format the game uses, but with custom messages.

        Args:
            EnterMessage: The message to display after the enter prompt. Defaults to "Select".
            EscMessage: The message to display after the escape prompt. Defaults to "Cancel".
        Returns:
            A string in the same format as the game's tooltips, but with your custom prompts.
        """
        return (
            f"<StringAliasMap:GFx_Accept> {EnterMessage}"
            "     "
            f"<StringAliasMap:GFx_Cancel> {EscMessage}"
        )

    Title: str
    Caption: str
    Tooltip: str
    Buttons: Sequence[DialogBoxButton]
    PreventCanceling: bool

    def __init__(
        self, *,
        Title: str,
        Caption: str = "",
        # Default tooltip the game uses
        Tooltip: str = "<StringAliasMap:GFx_Accept> Select     <StringAliasMap:GFx_Cancel> Cancel",
        Buttons: Sequence[DialogBoxButton],
        PreventCanceling: bool = False,
    ) -> None:
        """
        Creates a Dialog Box.

        Args:
            Title: The title text to display at the top of the dialog box.
            Caption:
                The text to display in the main body of the dialog box. Defaults to the empty
                 string.
            Tooltip:
                The text to display in the footer of the dialog box. Defaults to the game's default
                 tooltip, which explains the keybinds.
            Buttons:
                A sequence of DialogBoxButtons that the user should pick from. These will
                 automatically be split into pages.
            PreventCanceling:
                If the user should be prevented from pressing ESC to cancel out of the dialog
                 without selecting anything. Defaults to false.
        Raises:
            IndexError:
                If the DefaultButtonIndex does not corospond with an index of the Buttons sequence.
            TypeError: If not passed a valid sequence of DialogBoxButtons.
            ValueError: If not passed at least one button.
        """
        self.Title = Title
        self.Caption = Caption
        self.Tooltip = Tooltip
        self.Buttons = Buttons
        self.PreventCanceling = PreventCanceling

        self._CurrentPageIndex = 0

        self.Update()

    _Pages: List[_Page]
    _CurrentPageIndex: int
    _NextPageButton: DialogBoxButton

    def Update(self) -> None:
        """
        Updates all pages to use the values currently stored in the instance's attributes.

        Must be called whenever you update the attributes, otherwise the displayed boxes will
         continue to use the old values.

        Buttons are somewhat an exception to this - you may change their attributes without calling
         this, but you must call it if you change the button list.

        Raises:
            IndexError:
                If the DefaultButtonIndex does not corospond with an index of the Buttons sequence.
            ValueError: If Buttons is not a sequence of at least one button.
        """

        # Check we actually have a sequence of buttons - everything else can use a builtin converter
        try:
            for b in self.Buttons:
                if not isinstance(b, DialogBoxButton):
                    raise TypeError
        except TypeError as e:
            raise ValueError(
                f"'{self.Buttons}' is not a sequence of Buttons"
            ).with_traceback(e.__traceback__)
        if 1 > len(self.Buttons) > 5:
            raise ValueError("A single dialog box must have 1-5 buttons")

        self._NextPageButton = DialogBoxButton(
            "Next Page",
            f"Cycle through {int(len(self.Buttons) / 4) + 1} pages of options."
        )

        self._Pages = []

        buttonGroups: List[List[DialogBoxButton]]
        if len(self.Buttons) <= 5:
            # If we have 5 buttons or less then really this should just act like a single dialog box
            buttonGroups = [list(self.Buttons)]
        else:
            # With more we split them into pages of 4 options and the next page button
            buttonGroups = [list(self.Buttons[i:i + 4]) + [self._NextPageButton]
                            for i in range(0, len(self.Buttons), 4)]

        def AdvancePage(button: DialogBoxButton) -> None:
            if button == self._NextPageButton:
                self._CurrentPageIndex = (self._CurrentPageIndex + 1) % len(self._Pages)
                self.OnPageChange()
                self.Show()
            else:
                self.OnPress(button)

        for group in buttonGroups:
            box = _Page(
                Title=str(self.Title),
                Caption=str(self.Caption),
                Tooltip=str(self.Tooltip),
                Buttons=group,
                PreventCanceling=bool(self.PreventCanceling),
            )
            box.OnPress = AdvancePage  # type: ignore
            box.OnCancel = lambda: self.OnCancel()  # type: ignore

            self._Pages.append(box)

    def Show(self) -> None:
        """
        Displays the dialog box on the current page. This does not pause the game.

        If the user scrolls through a few pages before exiting the dialog box then calling this
         function again will re-show the page they exited on.
        """
        self._Pages[self._CurrentPageIndex].Show()

    def ShowButton(self, button: DialogBoxButton) -> None:
        """
        Displays the dialog box with the provided button selected. This does not pause the game.

        Args:
            button: The button you want to be selected
        Raises:
            ValueError:
                If the provided button is not currently in one of the stored pages. This may happen
                 if you forgot to call UpdatePages().
        """
        for page in self._Pages:
            if button in page.Buttons:
                self._CurrentPageIndex = self._Pages.index(page)
                page.DefaultButtonIndex = page.Buttons.index(button)
                break
        else:
            raise ValueError(f"Provided button {button} is not on any of the current pages!")

        self.Show()
        self._Pages[self._CurrentPageIndex].DefaultButtonIndex = 0

    def OnPageChange(self) -> None:
        """ Callback function intended to be overwritten. Called when the user changes pages. """
        pass

    def OnPress(self, button: DialogBoxButton) -> None:
        """
        Callback function intended to be overwritten. Called when the user presses a button.

        Args:
            button: The button that the user pressed.
        """
        pass

    def OnCancel(self) -> None:
        """
          Callback function intended to be overwritten. Called when the user cancels out of the
           dialog box menu.
        """
        pass
