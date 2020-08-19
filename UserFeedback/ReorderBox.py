from typing import MutableSequence

from .OptionBox import OptionBox, OptionBoxButton, OptionScrollType


class ReorderBox(OptionBox):
    """
    Class representing a dialog box with multiple buttons that may be reordered. Based off of the
     same component as an `OptionBox`, with heavy modification.

    Attributes:
        Title: The title text to display at the top of the option box.
        Caption: The text to display in the main body of the option box.
        Tooltip: The text to display in the footer of the option box.
        Buttons:
            A mutable sequence of `OptionBoxButton`s that the user should reorder. This may contain
             duplicates. This will be modified in place.
        Priority:
            A byte representing the priority of the option box in reference to the game's other
             `GfxMovie`s. Higher values display above lower ones.
    Inherited, unused attributes:
        PreventCanceling: Forced to False.
        ScrollType: Forced to `OptionScrollType.BIDIRECTIONAL_HOVER`.
    """

    @staticmethod
    def CreateTooltipString(
        EnterMessage: str = "Select",
        EscMessage: str = "Exit",
        ReorderMessage: str = "Move"
    ) -> str:
        """
        Creates a tooltip string in a similar format as the game, with your own prompts.

        Args:
            EnterMessage: The message to display after the enter prompt. Defaults to "Select".
            EscMessage: The message to display after the escape prompt. Defaults to "Cancel".
            ReorderMessage: The message to display after the up/down prompt. Defaults to "Move".
        Returns:
            A string in in a similar format as the game's tooltips, but with your own prompts.
        """
        return (
            f"<StringAliasMap:GFx_Accept> {EnterMessage}"
            "     "
            f"[Up / Down] {ReorderMessage}"
            "     "
            f"<StringAliasMap:GFx_Cancel> {EscMessage}"
        )

    Buttons: MutableSequence[OptionBoxButton]

    def __init__(
        self, *,
        Title: str,
        Caption: str = "",
        Tooltip: str = "<StringAliasMap:GFx_Accept> Select    [Up / Down] Move     <StringAliasMap:GFx_Cancel> Exit",
        Buttons: MutableSequence[OptionBoxButton],
        Priority: int = 254
    ) -> None:
        """
        Creates a Reorder Box.

        Args:
            Title: The title text to display at the top of the option box.
            Caption:
                The text to display in the main body of the option box. Defaults to the empty
                 string.
            Tooltip:
                The text to display in the footer of the option box. Defaults to the game's default
                 tooltip, which explains the keybinds.
            Buttons:
                A mutable sequence of buttons that the user should reorder. This may contain
                 duplicates.
            Priority:
                A byte representing the priority of the option box in reference to the game's other
                 `GfxMovie`s. Higher values display above lower ones. Defaults to 254, the same as
                 the game's default.
            Raises:
                TypeError: If not passed a sequence of `OptionBoxButton`s.
                ValueError: If not passed at least two buttons.
        """
        super().__init__(
            Title=Title,
            Caption=Caption,
            Tooltip=Tooltip,
            Buttons=Buttons,
            PreventCanceling=False,
            Priority=Priority
        )

        self._IsCurrentlyMoving = False

    _IsCurrentlyMoving: bool

    def IsCurrentlyMoving(self) -> bool:
        """
        Gets if the user is currently moving a button.

        Note that if this is the case, the button being moved has it's `Name` field modified,
         prefixing it with "-- " and suffixing it with " --"

        Returns:
            True if the user is currently moving a button, false otherwise.
        """
        return self._IsCurrentlyMoving

    # Really just redefining this for a different docstring
    def GetSelectedButton(self) -> OptionBoxButton:
        """
        Gets the button the user has current got selected.

        Note that if a button is currently being moved (and thus this function would return it) then
         it's `Name` field will be modified - prefixed with "-- " and suffixed with " --"

        Returns:
            The button the user has currently got selected
        Raises:
            RuntimeError: If the option box is not currently showing
        """
        return self._Pages[self._CurrentPageIndex].GetSelectedButton()

    def OnCancel(self) -> None:
        """
        Callback function intended to be overwritten. Called when the user "cancels" out of the
         option box menu - i.e. when they exit it.
        """
        pass

    def OnSelect(self, button: OptionBoxButton) -> None:
        """
        Callback function intended to be overwritten. Called when the user starts moving a button,
         though before the `Name` field is modified.

        Args:
            button: The button that was selected.
        """
        pass

    def OnPlace(self, button: OptionBoxButton) -> None:
        """
        Callback function intended to be overwritten. Called when the user places a button into
         it's new stop, after the `Name` field is restored.

        Args:
            button: The button that was selected.
        """
        pass

    def _InternalOnPress(self, button: OptionBoxButton) -> None:
        if self._IsCurrentlyMoving:
            button.Name = button.Name[3:-3]
            self.OnPlace(button)
        else:
            self.OnSelect(button)
            button.Name = f"-- {button.Name} --"
        self._IsCurrentlyMoving = not self._IsCurrentlyMoving

        self.Show(button)

    def _InternalOnInput(self, key: str, event: int) -> None:
        if event == 0:
            current_index = self.Buttons.index(self.GetSelectedButton())
            new_index = current_index
            if key in self._UP_KEYS:
                new_index = max(current_index - 1, 0)
            elif key in self._DOWN_KEYS:
                new_index = min(current_index + 1, len(self.Buttons) - 1)

            elif key == "PageUp":
                if len(self._Pages) <= 1 or self._CurrentPageIndex == 0:
                    new_index = 0
                else:
                    # This is a neat bit of maths that works out perfectly
                    # Because we're moving upwards we only need to be careful about the extra button in
                    #  the first group - which we can ignore by pretending this is one-indexed
                    new_index = self._CurrentPageIndex * 3
            elif key == "PageDown":
                if len(self._Pages) <= 1 or self._CurrentPageIndex == len(self._Pages) - 1:
                    new_index = len(self.Buttons) - 1
                else:
                    # Same sort of concept as above, messier formula
                    new_index = 3 * (self._CurrentPageIndex + 1) + 1
            elif key == "Home":
                if self._CurrentPageIndex == 0:
                    new_index = 0
                else:
                    new_index = self._CurrentPageIndex * 3 + 1
            elif key == "End":
                if self._CurrentPageIndex == len(self._Pages) - 1:
                    new_index = len(self.Buttons) - 1
                else:
                    new_index = 3 * (self._CurrentPageIndex + 1)

            if new_index != current_index:
                self.Hide()

                if self._IsCurrentlyMoving:
                    self.Buttons.insert(new_index, self.Buttons.pop(current_index))
                    self.Update()

                old_page = self._CurrentPageIndex
                self.Show(self.Buttons[new_index])
                if self._CurrentPageIndex != old_page:
                    self.OnPageChange()

        self.OnInput(key, event)

    # Inherited, unused functions/attributes
    def OnPress(self, button: OptionBoxButton) -> None:
        """
        This callback is inherited from `OptionsBox`, but ***is not*** used.
        Overwrite `OnSelect` or `OnPlace` instead.
        """
        raise NotImplementedError

    @property  # type: ignore # https://github.com/python/mypy/issues/4125
    def PreventCanceling(self) -> bool:  # type: ignore
        return False

    @PreventCanceling.setter
    def PreventCanceling(self, val: bool) -> None:
        pass

    @property  # type: ignore
    def ScrollType(self) -> OptionScrollType:  # type: ignore
        return OptionScrollType.BIDIRECTIONAL_HOVER

    @ScrollType.setter
    def ScrollType(self, val: OptionScrollType) -> None:
        pass
