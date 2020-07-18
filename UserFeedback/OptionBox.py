import unrealsdk
from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional, Sequence, Tuple
from .GFxMovie import GFxMovie


@dataclass
class OptionBoxButton:
    """
    A simple dataclass representing a button for `OptionBox`s.

    Attributes:
        Name: The name that the button should have.
        Tip: A string that is added to the option box caption when hovering over this button.
    """
    Name: str
    Tip: str = ""


class OptionScrollType(Enum):
    """
    An enum for the various ways an `OptionBox` can scroll between pages.

                                 | Direction | Infinite  | Activator |  Display
    -----------------------------+-----------+-----------+-----------+-----------
    UNIDIRECTIONAL               |    Uni    |    Yes    |   Click   |   4/4/4
    BIDIRECTIONAL                |    Bi     |    No     |   Click   |   4/3/4
    BIDIRECTIONAL_INFINITE       |    Bi     |    Yes    |   Click   |   3/3/3
    UNIDIRECTIONAL_HOVER         |    Uni    |    Yes    |   Hover   |   4/4/4
    BIDIRECTIONAL_HOVER          |    Bi     |    No     |   Hover   |   4/3/4
    BIDIRECTIONAL_INFINITE_HOVER |    Bi     |    Yes    |   Hover   |   3/3/3

    Direction:  Which directions you can scroll.
    Infinite:   If you can scroll from the last page back to first.
    Activator:  What activates scrolling - clicking on the button or hovering over it.
    Display:    How many buttons are displayed on the first/midde/last page(s). The last page may
                 have less of course, and if there's only one page it may have up to 5.
    """
    UNIDIRECTIONAL = auto()
    BIDIRECTIONAL = auto()
    BIDIRECTIONAL_INFINITE = auto()
    UNIDIRECTIONAL_HOVER = auto()
    BIDIRECTIONAL_HOVER = auto()
    BIDIRECTIONAL_INFINITE_HOVER = auto()


class _Page(GFxMovie):
    """
    Class representing a single 'page' option box. You should probably use OptionBox over this.

    This class behaves very similarly to OptionBox. The main differences are that it's limited to no
     more than 5 buttons (and thus doesn't have scrolling logic), you don't need to call Update()
     when you change attributes, and that it uses a DefaultButtonIndex field rather than having a
     special show method.

    You should only really use this class if you want to create your own logic for multiple pages.
    """
    Title: str
    Caption: str
    Tooltip: str
    Buttons: Sequence[OptionBoxButton]
    DefaultButtonIndex: int
    PreventCanceling: bool
    Priority: int

    _OptionBox: Optional[unrealsdk.UObject]

    def __init__(
        self, *,
        Title: str,
        Caption: str = "",
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
        if len(Buttons) < 1 or len(Buttons) > 5:
            raise ValueError("A single option box must have 1-5 buttons")
        if int(DefaultButtonIndex) < 0 or int(DefaultButtonIndex) >= len(Buttons):
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
        self._OptionBox = unrealsdk.GetEngine().GamePlayers[0].Actor.GFxUIManager.ShowDialog()

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
        def Accepted(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            if caller == self._OptionBox:
                unrealsdk.RemoveHook("WillowGame.WillowGFxDialogBox.Accepted", "CustomOptionBox")
                unrealsdk.RemoveHook("WillowGame.WillowGFxDialogBox.Cancelled", "CustomOptionBox")
                unrealsdk.RemoveHook("WillowGame.WillowGFxDialogBox.HandleInputKey", "CustomOptionBox")
                self._OptionBox = None
                self.OnPress(self.Buttons[int(caller.CurrentSelection)])
            return True

        def Cancelled(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            if caller == self._OptionBox:
                unrealsdk.RemoveHook("WillowGame.WillowGFxDialogBox.Accepted", "CustomOptionBox")
                unrealsdk.RemoveHook("WillowGame.WillowGFxDialogBox.Cancelled", "CustomOptionBox")
                unrealsdk.RemoveHook("WillowGame.WillowGFxDialogBox.HandleInputKey", "CustomOptionBox")
                self._OptionBox = None
                self.OnCancel()
            return True

        def HandleInputKey(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            if caller == self._OptionBox:
                self.OnInput(params.ukey, params.uevent)
            return True

        unrealsdk.RegisterHook("WillowGame.WillowGFxDialogBox.Accepted", "CustomOptionBox", Accepted)
        unrealsdk.RegisterHook("WillowGame.WillowGFxDialogBox.Cancelled", "CustomOptionBox", Cancelled)
        unrealsdk.RegisterHook("WillowGame.WillowGFxDialogBox.HandleInputKey", "CustomOptionBox", HandleInputKey)

    def IsShowing(self) -> bool:
        return self._OptionBox is not None

    def Hide(self) -> None:
        unrealsdk.RemoveHook("WillowGame.WillowGFxDialogBox.Accepted", "CustomOptionBox")
        unrealsdk.RemoveHook("WillowGame.WillowGFxDialogBox.Cancelled", "CustomOptionBox")
        unrealsdk.RemoveHook("WillowGame.WillowGFxDialogBox.HandleInputKey", "CustomOptionBox")

        # If it's already closed just give a warning
        if self._OptionBox is None:
            unrealsdk.Log(
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
        Buttons: A sequence of buttons that the user should pick from. This may contain duplicates.
        PreventCanceling:
            If the user should be prevented from pressing ESC to cancel out of the option
             without selecting anything.
        Priority:
            A byte representing the priority of the option box in reference to the game's other
             `GfxMovie`s. Higher values display above lower ones.
        ScrollType: How the option box scrolls between pages, if there are multiple.
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
    ScrollType: OptionScrollType

    def __init__(
        self, *,
        Title: str,
        Caption: str = "",
        Tooltip: str = "<StringAliasMap:GFx_Accept> Select    <StringAliasMap:GFx_Cancel> Cancel",
        Buttons: Sequence[OptionBoxButton],
        PreventCanceling: bool = False,
        Priority: int = 254,
        ScrollType: OptionScrollType = OptionScrollType.UNIDIRECTIONAL_HOVER
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
                 automatically be split into pages. This may contain duplicates.
            PreventCanceling:
                If the user should be prevented from pressing ESC to cancel out of the option
                 without selecting anything. Defaults to false.
            Priority:
                A byte representing the priority of the option box in reference to the game's other
                 `GfxMovie`s. Higher values display above lower ones. Defaults to 254, the same as
                 the game's default.
        Raises:
            TypeError: If not passed a sequence of `OptionBoxButton`s.
            ValueError:
                If not passed at least one button.
                If ScrollType has an invalid value not equal to anything in the enum.
        """
        self.Title = Title
        self.Caption = Caption
        self.Tooltip = Tooltip
        self.Buttons = Buttons
        self.PreventCanceling = PreventCanceling
        self.Priority = Priority
        self.ScrollType = ScrollType

        self._CurrentPageIndex = 0
        self._NextPageButton = OptionBoxButton("Next Page")
        self._PreviousPageButton = OptionBoxButton("Previous Page")

        self.Update()

    _Pages: List[_Page]
    _CurrentPageIndex: int
    _NextPageButton: OptionBoxButton
    _PreviousPageButton: OptionBoxButton

    _UP_KEYS: Tuple[str, ...] = (
        "Up", "XboxTypeS_DPad_Up", "Gamepad_LeftStick_Up"
    )
    _DOWN_KEYS: Tuple[str, ...] = (
        "Down", "XboxTypeS_DPad_Down", "Gamepad_LeftStick_Down"
    )

    def Update(self) -> None:
        """
        Updates all of the internal pages to use the values currently stored in the attributes.

        Must be called whenever you update the attributes, otherwise the displayed boxes will
         continue to use the old values.

        Buttons are somewhat an exception to this - you may change their attributes without calling
         this, but you must call it if you change the button list.

        Raises:
            TypeError: If not passed a sequence of `OptionBoxButton`s.
            ValueError:
                If Buttons is not a sequence of at least one button.
                If ScrollType has an invalid value not equal to anything in the enum.
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
        if len(self.Buttons) < 1:
            raise ValueError("An option box must have at least one button")

        self._Pages = []

        buttonGroups: List[List[OptionBoxButton]] = []
        # If we have 5 buttons or less we only have one page
        if len(self.Buttons) <= 5:
            buttonGroups.append(list(self.Buttons))

        elif self.ScrollType in (OptionScrollType.UNIDIRECTIONAL, OptionScrollType.UNIDIRECTIONAL_HOVER):
            for i in range(0, len(self.Buttons), 4):
                buttonGroups.append([*self.Buttons[i:i + 4], self._NextPageButton])

        elif self.ScrollType in (OptionScrollType.BIDIRECTIONAL, OptionScrollType.BIDIRECTIONAL_HOVER):
            buttonGroups.append([*self.Buttons[0:4], self._NextPageButton])
            for i in range(4, len(self.Buttons), 3):
                buttonGroups.append(
                    [self._PreviousPageButton, *self.Buttons[i:i + 3], self._NextPageButton]
                )
            buttonGroups[-1].pop()
            # Handle the case where a single button got put on the last page
            if len(buttonGroups[-1]) == 2:
                buttonGroups[-2][-1] = buttonGroups[-1][1]
                del buttonGroups[-1]

        elif self.ScrollType in (OptionScrollType.BIDIRECTIONAL_INFINITE, OptionScrollType.BIDIRECTIONAL_INFINITE_HOVER):
            for i in range(0, len(self.Buttons), 3):
                buttonGroups.append(
                    [self._PreviousPageButton, *self.Buttons[i:i + 3], self._NextPageButton]
                )
        else:
            raise ValueError("Invalid scroll type")

        for group in buttonGroups:
            box = _Page(
                Title=str(self.Title),
                Caption=str(self.Caption),
                Tooltip=str(self.Tooltip),
                Buttons=group,
                PreventCanceling=bool(self.PreventCanceling),
                Priority=int(self.Priority)
            )
            # Use internal callback functions partially so the actual callbacks can be updated
            #  without calling this, and partially so that we can guarentee we run some stuff before
            #  the user's callbacks
            # Plus it makes it easier for subclasses to overwrite
            box.OnPress = self._InternalOnPress  # type: ignore
            box.OnInput = self._InternalOnInput  # type: ignore
            box.OnCancel = self._InternalOnCancel  # type: ignore

            self._Pages.append(box)

    def Show(self, button: Optional[OptionBoxButton] = None) -> None:
        """
        Displays the option box on the current page.

        If the user scrolls through a few pages before exiting the option box then calling this
         function again will re-show the page they exited on.

        By default selects the first button, but optionally can select a specific button. If the
         same button has been included in the list multiple times, it will prioritize the first copy
         on the current page, followed by the first copy in the overall list.

        Args:
            button: An optional arg specifying the button that should be selected. Defaults to None.
        Raises:
            ValueError:
                If the provided button is not currently in one of the stored pages. This may happen
                 if you forgot to call Update().
        """

        currentPage = self._Pages[self._CurrentPageIndex]
        if button is None:
            currentPage.DefaultButtonIndex = 0
            # Don't select the previous page button if we use hover scrolling
            if self.ScrollType in (OptionScrollType.BIDIRECTIONAL_HOVER, OptionScrollType.BIDIRECTIONAL_INFINITE_HOVER):
                if currentPage.Buttons[0] == self._PreviousPageButton:
                    currentPage.DefaultButtonIndex = 1
        elif button in currentPage.Buttons:
            currentPage.DefaultButtonIndex = currentPage.Buttons.index(button)
        else:
            for page in self._Pages:
                if button in page.Buttons:
                    self._CurrentPageIndex = self._Pages.index(page)
                    page.DefaultButtonIndex = page.Buttons.index(button)
                    break
            else:
                raise ValueError(f"Provided button {button} is not on any of the current pages!")

        self._Pages[self._CurrentPageIndex].Show()

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

        Args:
            key:
                The key that was pressed. See the following link for reference.
                https://api.unrealengine.com/udk/Three/KeyBinds.html#Mappable%20keys
            event:
                The input event type. See the following link for reference.
                https://docs.unrealengine.com/en-US/API/Runtime/Engine/Engine/EInputEvent/index.html
        """
        pass

    def OnPageChange(self) -> None:
        """ Callback function called when the user changes pages. """
        pass

    def OnPress(self, button: OptionBoxButton) -> None:
        """
        Callback function called when the user presses a button.

        Args:
            button: The button that the user pressed.
        """
        pass

    def OnCancel(self) -> None:
        """ Callback function called when the user cancels out of the option box. """
        pass

    """ Deprecated methods/attributes """
    _DeprecationWarning_ShowButton: bool = False

    def ShowButton(self, button: OptionBoxButton) -> None:
        """
        This has been deprecated since version 1.3. Use the optional argument on `Show()` instead.

        Displays the option box with the provided button selected.

        Args:
            button: The button you want to be selected
        Raises:
            ValueError:
                If the provided button is not currently in one of the stored pages. This may happen
                 if you forgot to call Update().
        """
        if not self._DeprecationWarning_ShowButton:
            unrealsdk.Log("[UserFeedback] Use of `OptionBox.ShowButton()` is deprecated!")
            self._DeprecationWarning_ShowButton = True
        self.Show(button)

    """ Internal methods """

    # Turns out we need this scrolling logic in a few places
    def _PageUp(self) -> None:
        pageIdx = (self._CurrentPageIndex - 1) % len(self._Pages)
        buttonIdx = -1

        if len(self._Pages) == 1:
            buttonIdx = 0
        if self.ScrollType == OptionScrollType.UNIDIRECTIONAL_HOVER:
            buttonIdx = -2
        elif self.ScrollType == OptionScrollType.BIDIRECTIONAL_HOVER:
            if pageIdx != len(self._Pages) - 1:
                buttonIdx = -2
        elif self.ScrollType == OptionScrollType.BIDIRECTIONAL_INFINITE_HOVER:
            buttonIdx = -2

        if self.IsShowing():
            self.Hide()
        self._CurrentPageIndex = pageIdx
        self.Show(self._Pages[pageIdx].Buttons[buttonIdx])
        if len(self._Pages) < 1:
            self.OnPageChange()

    def _PageDown(self) -> None:
        pageIdx = (self._CurrentPageIndex + 1) % len(self._Pages)
        buttonIdx = 0

        if len(self._Pages) == 1:
            buttonIdx = -1
        elif self.ScrollType == OptionScrollType.BIDIRECTIONAL_HOVER:
            if pageIdx != 0:
                buttonIdx = 1
        elif self.ScrollType == OptionScrollType.BIDIRECTIONAL_INFINITE_HOVER:
            buttonIdx = 1

        if self.IsShowing():
            self.Hide()
        self._CurrentPageIndex = pageIdx
        self.Show(self._Pages[pageIdx].Buttons[buttonIdx])
        if len(self._Pages) < 1:
            self.OnPageChange()

    def _Home(self) -> None:
        self.Hide()

        buttonIdx = 0
        if self.ScrollType == OptionScrollType.BIDIRECTIONAL_HOVER:
            if self._CurrentPageIndex != 0:
                buttonIdx = 1
        elif self.ScrollType == OptionScrollType.BIDIRECTIONAL_INFINITE_HOVER:
            buttonIdx = 1

        self.Show(self._Pages[self._CurrentPageIndex].Buttons[buttonIdx])

    def _End(self) -> None:
        self.Hide()

        buttonIdx = -1
        if self.ScrollType == OptionScrollType.UNIDIRECTIONAL_HOVER:
            buttonIdx = -2
        elif self.ScrollType == OptionScrollType.BIDIRECTIONAL_HOVER:
            if self._CurrentPageIndex != len(self._Pages) - 1:
                buttonIdx = -2
        elif self.ScrollType == OptionScrollType.BIDIRECTIONAL_INFINITE_HOVER:
            buttonIdx = -2

        self.Show(self._Pages[self._CurrentPageIndex].Buttons[buttonIdx])

    def _InternalOnPress(self, button: OptionBoxButton) -> None:
        if button == self._NextPageButton:
            self._PageDown()
        elif button == self._PreviousPageButton:
            self._PageUp()
        else:
            self.OnPress(button)

    def _InternalOnInput(self, key: str, event: int) -> None:
        if event == 0:
            if key == "PageUp":
                if self._CurrentPageIndex == 0:
                    if self.ScrollType in (OptionScrollType.BIDIRECTIONAL, OptionScrollType.BIDIRECTIONAL_HOVER):
                        self._Home()
                    else:
                        self._PageUp()
                else:
                    self._PageUp()
            elif key == "PageDown":
                if self._CurrentPageIndex == len(self._Pages) - 1:
                    if self.ScrollType in (OptionScrollType.BIDIRECTIONAL, OptionScrollType.BIDIRECTIONAL_HOVER):
                        self._End()
                    else:
                        self._PageDown()
                else:
                    self._PageDown()
            elif key == "Home":
                self._Home()
            elif key == "End":
                self._End()
        elif event == 1:
            isHoverScroll = self.ScrollType in (
                OptionScrollType.UNIDIRECTIONAL_HOVER,
                OptionScrollType.BIDIRECTIONAL_HOVER,
                OptionScrollType.BIDIRECTIONAL_INFINITE_HOVER
            )
            selectedButton = self.GetSelectedButton()
            if key in self._UP_KEYS and isHoverScroll and selectedButton == self._PreviousPageButton:
                self._PageUp()
            elif key in self._DOWN_KEYS and isHoverScroll and selectedButton == self._NextPageButton:
                self._PageDown()

        self.OnInput(key, event)

    def _InternalOnCancel(self) -> None:
        self.OnCancel()
