import unrealsdk
from typing import ClassVar

from . import BaseTask, JSON
from Mods.UserFeedback import TextInputBox


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
        inputBox = TextInputBox("Configure Console Command", self.Command)

        def OnSubmit(msg: str) -> None:
            if len(msg) != 0:
                self.Command = msg
            self.OnFinishConfiguration()

        inputBox.OnSubmit = OnSubmit  # type: ignore
        inputBox.Show()

    def ToJSONSerializable(self) -> JSON:
        return self.Command

    def FromJSONSerializable(self, data: JSON) -> bool:
        self.Command = str(data)
        return True

    def __str__(self) -> str:
        commandStr: str
        if len(self.Command) > 40:
            commandStr = self.Command[:40] + "..."
        else:
            commandStr = self.Command
        return f"Console Command: '{commandStr}'"
