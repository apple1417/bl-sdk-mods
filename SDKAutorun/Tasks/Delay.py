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
        plus_one = OptionBoxButton("+1")
        plus_tenth = OptionBoxButton("+0.1")
        minus_tenth = OptionBoxButton("-0.1")
        minus_one = OptionBoxButton("-1")
        direct_edit = OptionBoxButton("Direct Edit")

        main_box = OptionBox(
            Title="Configure Delay",
            Caption=f"Current Delay: {self.Delay:.02f}s",
            Tooltip=OptionBox.CreateTooltipString(EscMessage="Back"),
            Buttons=(plus_one, plus_tenth, minus_tenth, minus_one, direct_edit)
        )
        direct_box = TextInputBox("Configure Delay", f"{self.Delay:.02f}")

        def OnMainBoxPress(button: OptionBoxButton) -> None:
            if button == direct_edit:
                direct_box.Show()
                return

            if button == plus_one:
                self.Delay += 1
            elif button == plus_tenth:
                self.Delay += 0.1
            elif button == minus_tenth:
                self.Delay = max(self.Delay - 0.1, 0)
            elif button == minus_one:
                self.Delay = max(self.Delay - 1, 0)
            direct_box.DefaultMessage = f"{self.Delay:.02f}"
            main_box.Caption = f"Current Delay: {self.Delay:.02f}s"
            main_box.Update()
            main_box.Show(button)

        main_box.OnPress = OnMainBoxPress  # type: ignore
        main_box.OnCancel = self.OnFinishConfiguration  # type: ignore

        def WriteFloatFilter(char: str, message: str, pos: int) -> bool:
            if char in "0123456789":
                return True
            if char == ".":
                return "." not in message
            return False

        def OnDirectBoxSubmit(msg: str) -> None:
            if msg != "":
                self.Delay = round(float(msg), 2)
                main_box.Caption = f"Current Delay: {self.Delay:.02f}s"
            main_box.Update()
            main_box.Show()

        direct_box.IsAllowedToWrite = WriteFloatFilter  # type: ignore
        direct_box.OnSubmit = OnDirectBoxSubmit  # type: ignore

        main_box.Show()

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
