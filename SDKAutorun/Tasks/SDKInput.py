import unrealsdk
import traceback
from typing import Any, ClassVar, Dict, cast

from Mods.ModMenu import GetOrderedModList
from Mods.UserFeedback import OptionBox, OptionBoxButton, TextInputBox, TrainingBox

from . import JSON, BaseTask


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
        mod_button = OptionBoxButton("Mod", f"Currently: '{self.ModName}'")
        input_button = OptionBoxButton("Input", f"Currently: '{self.Input}'")
        custom_button = OptionBoxButton("- Custom Mod Name -")
        mod_buttons = [OptionBoxButton(mod.Name) for mod in GetOrderedModList()] + [custom_button]

        main_box = OptionBox(
            Title="Configure SDK Mod Input",
            Caption="Select which part you want to configure.",
            Buttons=(mod_button, input_button)
        )

        mod_box = OptionBox(
            Title="Select SDK Mod",
            Caption="Select which mod to send inputs to.",
            Buttons=mod_buttons
        )

        custom_box = TextInputBox("Custom Mod Name", self.ModName)

        input_box = TrainingBox("Set Input", "Press any key to set the input.")

        def OnMainPress(button: OptionBoxButton) -> None:
            if button == mod_button:
                mod_box.Show()
            elif button == input_button:
                input_box.Show()

        def OnModPick(button: OptionBoxButton) -> None:
            if button == custom_button:
                custom_box.Show()
            else:
                self.ModName = button.Name
                mod_button.Tip = f"Currently: '{self.ModName}'"
                main_box.Show(mod_button)

        def OnCustomSubmit(msg: str) -> None:
            if len(msg) != 0:
                self.ModName = msg
                mod_button.Tip = f"Currently: '{self.ModName}'"
                main_box.Show(mod_button)
            else:
                mod_box.Show(custom_button)

        def OnInput(key: str, event: int) -> None:
            if event != 1:
                return
            self.Input = key
            input_button.Tip = f"Currently: '{self.Input}''"
            if input_box.IsShowing():
                input_box.Hide()
            main_box.Show(input_button)

        main_box.OnPress = OnMainPress  # type: ignore
        main_box.OnCancel = self.OnFinishConfiguration  # type: ignore
        mod_box.OnPress = OnModPick  # type:ignore
        mod_box.OnCancel = lambda: mod_button.Show()  # type: ignore
        custom_box.OnSubmit = OnCustomSubmit  # type: ignore
        input_box.OnInput = OnInput  # type: ignore

        main_box.Show()

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
