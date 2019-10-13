import bl2sdk
from typing import List, Optional, Sequence
from .GFxMovie import GFxMovie


class OptionBoxButton:
    """
    A simple dataclass representing a button.

    Attributes:
        Name: The name that the button should have.
        Tip: A string that is added to the option box caption when hovering over this button.
    """
    Name: str
    Tip: str

    def __init__(self, Name: str, Tip: str = ""):
        self.Name = Name
        self.Tip = Tip

    def __repr__(self) -> str:
        return f"OptionBoxButton(Name='{self.Name}', Tip='{self.Tip}')"


class _Page(GFxMovie):
    """
    Class representing a single 'page' option box. You should probably use OptionBox over this.

    This behaves almost the exact same way as OptionBox. The main differences are that it's limited
     to no more than 5 buttons, that you don't need to call Update() when you change attributes,
     and that it uses a DefaultButtonIndex field rather than having a special show method.

    You should only really use this class if you want to create your own logic for multiple pages.
    """
    Title: str
    Caption: str
    Tooltip: str
    Buttons: Sequence[OptionBoxButton]
    DefaultButtonIndex: int
    PreventCanceling: bool
    Priority: int

    _OptionBox: Optional[bl2sdk.UObject]

    def __init__(
        self, *,
        Title: str,
        Caption: str = "",
        # Default tooltip the game uses
        Tooltip: str = "<StringAliasMap:GFx_Accept> Select     <StringAliasMap:GFx_Cancel> Cancel",
        Buttons: Sequence[OptionBoxButton],
        DefaultButtonIndex: int = 0,
        PreventCanceling: bool = False,
        Priority: int = 254
    ) -> None:
        # Check we actually have a sequence of buttons - everything else can use a builtin converter
        try:
            for b in Buttons:
                if not isinstance(b, OptionBoxButton):
                    raise TypeError
        except TypeError as e:
            raise ValueError(
                f"'{Buttons}' is not a sequence of Buttons"
            ).with_traceback(e.__traceback__)
        if 1 > len(Buttons) > 5:
            raise ValueError("A single option box must have 1-5 buttons")
        if 0 > int(DefaultButtonIndex) <= len(Buttons):
            raise IndexError("Default button index out of range")

        self.Title = str(Title)
        self.Caption = str(Caption)
        self.Tooltip = str(Tooltip)
        self.Buttons = Buttons
        self.DefaultButtonIndex = int(DefaultButtonIndex)
        self.PreventCanceling = bool(PreventCanceling)
        self.Priority = int(Priority)

        self._OptionBox = None

    def Show(self) -> None:
        self._OptionBox = bl2sdk.GetEngine().GamePlayers[0].Actor.GFxUIManager.ShowDialog()

        self._OptionBox.SetText(self.Title, self.Caption)
        self._OptionBox.bNoCancel = self.PreventCanceling
        self._OptionBox.SetTooltips(self.Tooltip)
        self._OptionBox.SetPriority(self.Priority)

        # We give each button a custom tag so that you can add two with the same name
        for idx in range(len(self.Buttons)):
            self._OptionBox.AppendButton(f"Button{idx}", self.Buttons[idx].Name, self.Buttons[idx].Tip)

        self._OptionBox.SetDefaultButton(f"Button{self.DefaultButtonIndex}", True)
        self._OptionBox.ApplyLayout()

        # One of these two functions is called when you exit the box
        # We run callbacks after removing hooks so that you can immediately re-show it if you want
        def Accepted(caller: bl2sdk.UObject, function: bl2sdk.UFunction, params: bl2sdk.FStruct) -> bool:
            if caller == self._OptionBox:
                bl2sdk.RemoveHook("WillowGame.WillowGFxDialogBox.Accepted", "CustomOptionBox")
                bl2sdk.RemoveHook("WillowGame.WillowGFxDialogBox.Cancelled", "CustomOptionBox")
                bl2sdk.RemoveHook("WillowGame.WillowGFxDialogBox.HandleInputKey", "CustomOptionBox")
                self._OptionBox = None
                self.OnPress(self.Buttons[int(caller.CurrentSelection)])
            return True

        def Cancelled(caller: bl2sdk.UObject, function: bl2sdk.UFunction, params: bl2sdk.FStruct) -> bool:
            if caller == self._OptionBox:
                bl2sdk.RemoveHook("WillowGame.WillowGFxDialogBox.Accepted", "CustomOptionBox")
                bl2sdk.RemoveHook("WillowGame.WillowGFxDialogBox.Cancelled", "CustomOptionBox")
                bl2sdk.RemoveHook("WillowGame.WillowGFxDialogBox.HandleInputKey", "CustomOptionBox")
                self._OptionBox = None
                self.OnCancel()
            return True

        def HandleInputKey(caller: bl2sdk.UObject, function: bl2sdk.UFunction, params: bl2sdk.FStruct) -> bool:
            if caller == self._OptionBox:
                self.OnInput(params.ukey, params.uevent)
            return True

        bl2sdk.RegisterHook("WillowGame.WillowGFxDialogBox.Accepted", "CustomOptionBox", Accepted)
        bl2sdk.RegisterHook("WillowGame.WillowGFxDialogBox.Cancelled", "CustomOptionBox", Cancelled)
        bl2sdk.RegisterHook("WillowGame.WillowGFxDialogBox.HandleInputKey", "CustomOptionBox", HandleInputKey)

    def IsShowing(self) -> bool:
        return self._OptionBox is not None

    def Hide(self) -> None:
        bl2sdk.RemoveHook("WillowGame.WillowGFxDialogBox.Accepted", "CustomOptionBox")
        bl2sdk.RemoveHook("WillowGame.WillowGFxDialogBox.Cancelled", "CustomOptionBox")
        bl2sdk.RemoveHook("WillowGame.WillowGFxDialogBox.HandleInputKey", "CustomOptionBox")

        # If it's already closed just give a warning`
        if self._OptionBox is None:
            bl2sdk.Log(
                "[UserFeedback] Warning: tried to hide a option box page that was already closed"
            )
            return

        # This convinces it to instantly GC itself somehow. It'd get collected next cycle if we
        #  ignored it anyway, but might as well get rid of it now.
        self._OptionBox.Cancelled(0)

        self._OptionBox.Close()
        self._OptionBox = None

    def GetSelectedButton(self) -> OptionBoxButton:
        if self._OptionBox is None:
            raise RuntimeError(
                "Tried to get selected button of an option box that is not currently showing"
            )
        return self.Buttons[int(self._OptionBox.CurrentSelection)]

    def OnPress(self, button: OptionBoxButton) -> None:
        pass

    def OnCancel(self) -> None:
        pass


class OptionBox(GFxMovie):
    """
    Class representing an option box with multiple options to chose from, like those used to select
     playthrough or confirm quitting.

    If you provide more buttons than a single box can handle it will automatically create multiple
     pages with a button to cycle between them.

    See https://i.imgur.com/E5TOicS.png for examples of what the various sections of the option box
     are called.

    Attributes:
        Title: The title text to display at the top of the option box.
        Caption: The text to display in the main body of the option box.
        Tooltip: The text to display in the footer of the option box.
        Buttons: A sequence of buttons that the user should pick from.
        PreventCanceling:
            If the user should be prevented from pressing ESC to cancel out of the option
             without selecting anything.
        Priority:
            A byte representing the priority of the option box in reference to the game's other
             `GfxMovie`s. Higher values display above lower ones.
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
    Buttons: Sequence[OptionBoxButton]
    PreventCanceling: bool
    Priority: int

    def __init__(
        self, *,
        Title: str,
        Caption: str = "",
        # Default tooltip the game uses
        Tooltip: str = "<StringAliasMap:GFx_Accept> Select     <StringAliasMap:GFx_Cancel> Cancel",
        Buttons: Sequence[OptionBoxButton],
        PreventCanceling: bool = False,
        Priority: int = 254
    ) -> None:
        """
        Creates an Option Box.

        Args:
            Title: The title text to display at the top of the option box.
            Caption:
                The text to display in the main body of the option box. Defaults to the empty
                 string.
            Tooltip:
                The text to display in the footer of the option box. Defaults to the game's default
                 tooltip, which explains the keybinds.
            Buttons:
                A sequence of OptionBoxButtons that the user should pick from. These will
                 automatically be split into pages.
            PreventCanceling:
                If the user should be prevented from pressing ESC to cancel out of the option
                 without selecting anything. Defaults to false.
            Priority:
                A byte representing the priority of the option box in reference to the game's other
                 `GfxMovie`s. Higher values display above lower ones. Defaults to 254, the same as
                 the game's default.
        Raises:
            IndexError:
                If the DefaultButtonIndex does not corospond with an index of the Buttons sequence.
            TypeError: If not passed a valid sequence of OptionBoxButtons.
            ValueError: If not passed at least one button.
        """
        self.Title = Title
        self.Caption = Caption
        self.Tooltip = Tooltip
        self.Buttons = Buttons
        self.PreventCanceling = PreventCanceling
        self.Priority = Priority

        self._CurrentPageIndex = 0

        self.Update()

    _Pages: List[_Page]
    _CurrentPageIndex: int
    _NextPageButton: OptionBoxButton

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
                if not isinstance(b, OptionBoxButton):
                    raise TypeError
        except TypeError as e:
            raise ValueError(
                f"'{self.Buttons}' is not a sequence of Buttons"
            ).with_traceback(e.__traceback__)
        if 1 > len(self.Buttons) > 5:
            raise ValueError("A single option box must have 1-5 buttons")

        self._NextPageButton = OptionBoxButton(
            "Next Page",
            f"Cycle through {int(len(self.Buttons) / 4) + 1} pages of options."
        )

        self._Pages = []

        buttonGroups: List[List[OptionBoxButton]]
        if len(self.Buttons) <= 5:
            # If we have 5 buttons or less then really this should just act like a single option box
            buttonGroups = [list(self.Buttons)]
        else:
            # With more we split them into pages of 4 options and the next page button
            buttonGroups = [list(self.Buttons[i:i + 4]) + [self._NextPageButton]
                            for i in range(0, len(self.Buttons), 4)]

        def AdvancePage(button: OptionBoxButton) -> None:
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
                Priority=int(self.Priority)
            )
            box.OnPress = AdvancePage  # type: ignore
            # Use lambdas so that you can update these later
            box.OnInput = lambda k, e: self.OnInput(k, e)  # type: ignore
            box.OnCancel = lambda: self.OnCancel()  # type: ignore

            self._Pages.append(box)

    def Show(self) -> None:
        """
        Displays the option box on the current page.

        If the user scrolls through a few pages before exiting the option box then calling this
         function again will re-show the page they exited on.
        """
        self._Pages[self._CurrentPageIndex].Show()

    def ShowButton(self, button: OptionBoxButton) -> None:
        """
        Displays the option box with the provided button selected.

        If the same button has been included multiple times it will prioritize the first copy on the
         current page, followed by the first copy in the overall list.

        Args:
            button: The button you want to be selected
        Raises:
            ValueError:
                If the provided button is not currently in one of the stored pages. This may happen
                 if you forgot to call UpdatePages().
        """
        currentPage = self._Pages[self._CurrentPageIndex]
        if button in currentPage.Buttons:
            currentPage.DefaultButtonIndex = currentPage.Buttons.index(button)
        else:
            for page in self._Pages:
                if button in page.Buttons:
                    self._CurrentPageIndex = self._Pages.index(page)
                    page.DefaultButtonIndex = page.Buttons.index(button)
                    break
            else:
                raise ValueError(f"Provided button {button} is not on any of the current pages!")

        self.Show()
        self._Pages[self._CurrentPageIndex].DefaultButtonIndex = 0

    def IsShowing(self) -> bool:
        """
        Gets if the option box is currently being displayed.

        Returns:
            True if the option is currently being displayed, False otherwise.
        """
        return self._Pages[self._CurrentPageIndex].IsShowing()

    def Hide(self) -> None:
        """
        Hides the option box, without running any of the callbacks.

        Displays a warning but does nothing if the option box is not currently being displayed.
        """
        self._Pages[self._CurrentPageIndex].Hide()

    def GetSelectedButton(self) -> OptionBoxButton:
        """
        Gets the button the user has current got selected.

        Returns:
            The button the user has currently got selected
        Raises:
            RuntimeError: If the option box is not currently showing
        """
        return self._Pages[self._CurrentPageIndex].GetSelectedButton()

    def OnInput(self, key: str, event: int) -> None:
        """
        Callback function called any time the user inputs anything while the option box is open.

        This sample implementation makes Home/End jump to the ends of a page, and Page Up/Down
         scroll between pages.

        Args:
            key:
                The key that was pressed. See the following link for reference.
                https://api.unrealengine.com/udk/Three/KeyBinds.html#Mappable%20keys
            event:
                The input event type. See the following link for reference.
                https://docs.unrealengine.com/en-US/API/Runtime/Engine/Engine/EInputEvent/index.html
        """
        if event != 0:
            return
        if key == "PageUp":
            if len(self._Pages) <= 1:
                return
            self.Hide()
            self._CurrentPageIndex = (self._CurrentPageIndex + 1) % len(self._Pages)
            self.OnPageChange()
            self.Show()
        elif key == "PageDown":
            if len(self._Pages) <= 1:
                return
            self.Hide()
            self._CurrentPageIndex = (self._CurrentPageIndex - 1) % len(self._Pages)
            self.OnPageChange()
            self.Show()
        elif key == "Home":
            self.Hide()
            self.ShowButton(self._Pages[self._CurrentPageIndex].Buttons[0])
        elif key == "End":
            self.Hide()
            self.ShowButton(self._Pages[self._CurrentPageIndex].Buttons[-1])

    def OnPageChange(self) -> None:
        """ Callback function intended to be overwritten. Called when the user changes pages. """
        pass

    def OnPress(self, button: OptionBoxButton) -> None:
        """
        Callback function intended to be overwritten. Called when the user presses a button.

        Args:
            button: The button that the user pressed.
        """
        pass

    def OnCancel(self) -> None:
        """
          Callback function intended to be overwritten. Called when the user cancels out of the
           option box menu.
        """
        pass
