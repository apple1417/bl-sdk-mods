import unrealsdk
from typing import ClassVar

from . import BaseTask, JSON
from Mods.UserFeedback import OptionBox, OptionBoxButton, TextInputBox


# This and SDKInput work similarly and could *probably* be subclasses, but there are just enough
#  differences that I think it's better to keep them seperate
class SDKEnable(BaseTask):
    Name: ClassVar[str] = "Enable SDK Mod"
    Description: ClassVar[str] = "Enables an SDK mod."

    ModName: str

    def __init__(self) -> None:
        self.ModName = ""

    def Execute(self) -> None:
        for mod in unrealsdk.Mods:
            if mod.Name == self.ModName:
                if mod.Status == "Enabled":
                    unrealsdk.Log(f"[{self.Name}] Mod '{self.ModName}' is already enabled!")
                else:
                    mod.SettingsInputPressed("Enable")
                break
        else:
            unrealsdk.Log(f"[{self.Name}] Unable to find mod '{self.ModName}'!")
        self.OnFinishExecution()

    def ShowConfiguration(self) -> None:
        customButton = OptionBoxButton("- Custom Mod Name -")
        modButtons = [OptionBoxButton(mod.Name) for mod in unrealsdk.Mods] + [customButton]

        modBox = OptionBox(
            Title="Select SDK Mod",
            Caption="Select the mod to enable.",
            Buttons=modButtons
        )

        customBox = TextInputBox("Custom Mod Name", self.ModName)

        def OnModPick(button: OptionBoxButton) -> None:
            if button == customButton:
                customBox.Show()
            else:
                self.ModName = button.Name
                self.OnFinishConfiguration()

        def OnCustomSubmit(msg: str) -> None:
            if len(msg) != 0:
                self.ModName = msg
                self.OnFinishConfiguration()
            else:
                modBox.Show(customButton)

        modBox.OnPress = OnModPick  # type:ignore
        modBox.OnCancel = self.OnFinishConfiguration  # type: ignore
        customBox.OnSubmit = OnCustomSubmit  # type: ignore

        modBox.Show()

    def ToJSONSerializable(self) -> JSON:
        return self.ModName

    def FromJSONSerializable(self, data: JSON) -> bool:
        self.ModName = str(data)
        return True

    def __str__(self) -> str:
        return f"Enable SDK Mod: '{self.ModName}'"
