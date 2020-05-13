import unrealsdk
import traceback
from typing import Any, cast, ClassVar, Dict

from . import BaseTask, JSON
from Mods.UserFeedback import OptionBox, OptionBoxButton, TextInputBox, TrainingBox


# This and SDKEnable work similarly and could *probably* be subclasses, but there are just enough
#  differences that I think it's better to keep them seperate
class SDKInput(BaseTask):
    Name: ClassVar[str] = "SDK Mod Input"
    Description: ClassVar[str] = "Sends a customizable input to an SDK mod."

    ModName: str
    Input: str

    def __init__(self) -> None:
        self.ModName = ""
        self.Input = "None"

    def Execute(self) -> None:
        for mod in unrealsdk.Mods:
            if mod.Name == self.ModName:
                if self.Input in mod.SettingsInputs:
                    try:
                        mod.SettingsInputPressed(mod.SettingsInputs[self.Input])
                    except Exception:
                        unrealsdk.Log(f"[{self.Name}] Mod '{self.ModName}' caused an exception while inputing '{self.Input}':")
                        for line in traceback.format_exc():
                            unrealsdk.Log(line)
                else:
                    unrealsdk.Log(
                        f"[{self.Name}] Mod '{self.ModName}' does not currently support the input '{self.Input}'!"
                    )
                break
        else:
            unrealsdk.Log(f"[{self.Name}] Unable to find mod '{self.ModName}'!")
        self.OnFinishExecution()

    def ShowConfiguration(self) -> None:
        modButton = OptionBoxButton("Mod", f"Currently: '{self.ModName}'")
        inputButton = OptionBoxButton("Input", f"Currently: '{self.Input}'")
        customButton = OptionBoxButton("- Custom Mod Name -")
        modButtons = [OptionBoxButton(mod.Name) for mod in unrealsdk.Mods] + [customButton]

        mainBox = OptionBox(
            Title="Configure SDK Mod Input",
            Caption="Select which part you want to configure.",
            Buttons=(modButton, inputButton)
        )

        modBox = OptionBox(
            Title="Select SDK Mod",
            Caption="Select which mod to send inputs to.",
            Buttons=modButtons
        )

        customBox = TextInputBox("Custom Mod Name", self.ModName)

        inputBox = TrainingBox("Set Input", "Press any key to set the input.")

        def OnMainPress(button: OptionBoxButton) -> None:
            if button == modButton:
                modBox.Show()
            elif button == inputButton:
                inputBox.Show()

        def OnModPick(button: OptionBoxButton) -> None:
            if button == customButton:
                customBox.Show()
            else:
                self.ModName = button.Name
                modButton.Tip = f"Currently: '{self.ModName}'"
                mainBox.Show(modButton)

        def OnCustomSubmit(msg: str) -> None:
            if len(msg) != 0:
                self.ModName = msg
                modButton.Tip = f"Currently: '{self.ModName}'"
                mainBox.Show(modButton)
            else:
                modBox.Show(customButton)

        def OnInput(key: str, event: int) -> None:
            if event != 1:
                return
            self.Input = key
            inputButton.Tip = f"Currently: '{self.Input}''"
            if inputBox.IsShowing():
                inputBox.Hide()
            mainBox.Show(inputButton)

        mainBox.OnPress = OnMainPress  # type: ignore
        mainBox.OnCancel = self.OnFinishConfiguration  # type: ignore
        modBox.OnPress = OnModPick  # type:ignore
        modBox.OnCancel = lambda: modButton.Show()  # type: ignore
        customBox.OnSubmit = OnCustomSubmit  # type: ignore
        inputBox.OnInput = OnInput  # type: ignore

        mainBox.Show()

    def ToJSONSerializable(self) -> JSON:
        return {
            "ModName": self.ModName,
            "Input": self.Input,
        }

    def FromJSONSerializable(self, data: JSON) -> bool:
        data = cast(Dict[str, Any], data)
        try:
            self.ModName = str(data["ModName"])
            self.Input = str(data["Input"])
        except KeyError:
            return False
        return True

    def __str__(self) -> str:
        return f"SDK Mod Input: '{self.ModName}', '{self.Input}'"
