from typing import ClassVar

from . import BaseTask, JSON
from Mods import AsyncUtil
from Mods.UserFeedback import OptionBox, OptionBoxButton, TextInputBox


class DelayTask(BaseTask):
    Name: ClassVar[str] = "Delay"
    Description: ClassVar[str] = "Waits a customizable delay before continuing."

    Delay: float

    def __init__(self) -> None:
        self.Delay = 1.0

    def Execute(self) -> None:
        AsyncUtil.RunIn(self.Delay, self.OnFinishExecution)

    def ShowConfiguration(self) -> None:
        plusOne = OptionBoxButton("+1")
        plusTenth = OptionBoxButton("+0.1")
        minusTenth = OptionBoxButton("-0.1")
        minusOne = OptionBoxButton("-1")
        directEdit = OptionBoxButton("Direct Edit")

        mainBox = OptionBox(
            Title="Configure Delay",
            Caption=f"Current Delay: {self.Delay:.02f}s",
            Tooltip=OptionBox.CreateTooltipString(EscMessage="Back"),
            Buttons=(plusOne, plusTenth, minusTenth, minusOne, directEdit)
        )
        directBox = TextInputBox("Configure Delay", f"{self.Delay:.02f}")

        def OnMainBoxPress(button: OptionBoxButton) -> None:
            if button == directEdit:
                directBox.Show()
                return

            if button == plusOne:
                self.Delay += 1
            elif button == plusTenth:
                self.Delay += 0.1
            elif button == minusTenth:
                self.Delay = max(self.Delay - 0.1, 0)
            elif button == minusOne:
                self.Delay = max(self.Delay - 1, 0)
            directBox.DefaultMessage = f"{self.Delay:.02f}"
            mainBox.Caption = f"Current Delay: {self.Delay:.02f}s"
            mainBox.Update()
            mainBox.Show(button)

        mainBox.OnPress = OnMainBoxPress  # type: ignore
        mainBox.OnCancel = self.OnFinishConfiguration  # type: ignore

        def WriteFloatFilter(char: str, message: str, pos: int) -> bool:
            if char in "0123456789":
                return True
            if char == ".":
                return "." not in message
            return False

        def OnDirectBoxSubmit(msg: str) -> None:
            if msg != "":
                self.Delay = round(float(msg), 2)
                mainBox.Caption = f"Current Delay: {self.Delay:.02f}s"
            mainBox.Update()
            mainBox.Show()

        directBox.IsAllowedToWrite = WriteFloatFilter  # type: ignore
        directBox.OnSubmit = OnDirectBoxSubmit  # type: ignore

        mainBox.Show()

    def ToJSONSerializable(self) -> JSON:
        return self.Delay

    def FromJSONSerializable(self, data: JSON) -> bool:
        try:
            self.Delay = round(float(data), 2)  # type: ignore
        except ValueError:
            return False
        if self.Delay < 0:
            self.Delay = 0
            return False
        return True

    def __str__(self) -> str:
        return f"Delay: {self.Delay:.02f}s"
