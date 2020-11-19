import unrealsdk
import traceback
from typing import ClassVar

from Mods.ModMenu import GetOrderedModList
from Mods.UserFeedback import OptionBox, OptionBoxButton, TextInputBox

from . import JSON, BaseTask


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
                    break
                if "Enable" not in mod.SettingsInputs.values():
                    unrealsdk.Log(f"[{self.Name}] Mod '{self.ModName}' does not currently support an enable input!")
                    break

                try:
                    mod.SettingsInputPressed("Enable")
                except Exception:
                    unrealsdk.Log(f"[{self.Name}] Mod '{self.ModName}' caused an exception while trying to enable:")
                    for line in traceback.format_exc():
                        unrealsdk.Log(line)
                break
        else:
            unrealsdk.Log(f"[{self.Name}] Unable to find mod '{self.ModName}'!")
        self.OnFinishExecution()

    def ShowConfiguration(self) -> None:
        custom_button = OptionBoxButton("- Custom Mod Name -")
        mod_buttons = [OptionBoxButton(mod.Name) for mod in GetOrderedModList()] + [custom_button]

        mod_box = OptionBox(
            Title="Select SDK Mod",
            Caption="Select the mod to enable.",
            Buttons=mod_buttons
        )

        custom_box = TextInputBox("Custom Mod Name", self.ModName)

        def OnModPick(button: OptionBoxButton) -> None:
            if button == custom_button:
                custom_box.Show()
            else:
                self.ModName = button.Name
                self.OnFinishConfiguration()

        def OnCustomSubmit(msg: str) -> None:
            if len(msg) != 0:
                self.ModName = msg
                self.OnFinishConfiguration()
            else:
                mod_box.Show(custom_button)

        mod_box.OnPress = OnModPick  # type:ignore
        mod_box.OnCancel = self.OnFinishConfiguration  # type: ignore
        custom_box.OnSubmit = OnCustomSubmit  # type: ignore

        mod_box.Show()

    def ToJSONSerializable(self) -> JSON:
        return self.ModName

    def FromJSONSerializable(self, data: JSON) -> bool:
        self.ModName = str(data)
        return True

    def __str__(self) -> str:
        return f"Enable SDK Mod: '{self.ModName}'"
