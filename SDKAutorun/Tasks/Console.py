import unrealsdk
from typing import ClassVar

from Mods.UserFeedback import TextInputBox

from . import JSON, BaseTask


class ConsoleTask(BaseTask):
    Name: ClassVar[str] = "Console Command"
    Description: ClassVar[str] = "Runs a console command."

    Command: str

    def __init__(self) -> None:
        self.Command = ""

    def Execute(self) -> None:
        unrealsdk.GetEngine().GamePlayers[0].Actor.ServerRCon(self.Command)
        self.OnFinishExecution()

    def ShowConfiguration(self) -> None:
        input_box = TextInputBox("Configure Console Command", self.Command)

        def OnSubmit(msg: str) -> None:
            if len(msg) != 0:
                self.Command = msg
            self.OnFinishConfiguration()

        input_box.OnSubmit = OnSubmit  # type: ignore
        input_box.Show()

    def ToJSONSerializable(self) -> JSON:
        return self.Command

    def FromJSONSerializable(self, data: JSON) -> bool:
        self.Command = str(data)
        return True

    def __str__(self) -> str:
        command_str: str
        if len(self.Command) > 40:
            command_str = self.Command[:40] + "..."
        else:
            command_str = self.Command
        return f"Console Command: '{command_str}'"
