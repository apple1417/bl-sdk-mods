import html
import json
import os
from typing import ClassVar, Dict, List, Optional

from Mods.ModMenu import Options
from Mods.UserFeedback import OptionBox, OptionBoxButton, ShowHUDMessage, TextInputBox

from .Cheats import ABCCheat, ABCCycleableCheat


class Preset:
    Name: str
    IsBeingConfigured: bool
    CheatList: List[ABCCheat]

    _NewSettings: Dict[str, str]
    _OldSettings: Dict[str, str]

    _SelectedCheat: Optional[ABCCheat]
    _ConfigureBox: OptionBox
    _SaveBox: OptionBox
    _CheatConfigureBoxes: Dict[str, OptionBox]

    _SaveButton: ClassVar[OptionBoxButton] = OptionBoxButton("Save")
    _DiscardButton: ClassVar[OptionBoxButton] = OptionBoxButton("Discard")
    _DontRunButton: ClassVar[OptionBoxButton] = OptionBoxButton("Ignore")
    _RunButton: ClassVar[OptionBoxButton] = OptionBoxButton("Run")
    _IgnoreButton: ClassVar[OptionBoxButton] = OptionBoxButton(
        "Ignore",
        "Do not change this cheat's state."
    )

    def __init__(self, Name: str, Settings: Dict[str, str], CheatList: List[ABCCheat]) -> None:
        self.Name = Name
        self.IsBeingConfigured = False
        self.CheatList = CheatList

        self._NewSettings = Settings
        self._OldSettings = dict(Settings)
        self._SelectedCheat = None

        self._SaveBox = OptionBox(
            Title=f"Save '{self.Name}'",
            Caption="Do you want to save your changes?",
            Tooltip=OptionBox.CreateTooltipString(EscMessage="Back"),
            Buttons=(
                self._SaveButton,
                self._DiscardButton,
            ),
        )
        self._SaveBox.OnPress = self._FinishConfiguring  # type: ignore
        self._SaveBox.OnCancel = lambda: self._ConfigureBox.Show()  # type: ignore

        self._CheatConfigureBoxes = {}
        cheat_buttons: List[OptionBoxButton] = []
        for cheat in self.CheatList:
            tip: str
            box: OptionBox
            if not isinstance(cheat, ABCCycleableCheat):
                tip = "Currently: Ignore"
                if cheat.Name in self._NewSettings:
                    tip = "Currently: Run"

                box = OptionBox(
                    Title=f"Configure '{cheat.Name}'",
                    Caption=(
                        "Select if this cheat should be run or ignored when you press this preset's"
                        " keybind."
                    ),
                    Tooltip=OptionBox.CreateTooltipString(EscMessage="Back"),
                    Buttons=(
                        self._RunButton,
                        self._DontRunButton,
                    ),
                )
            else:
                tip = "Currently: Ignore"
                if cheat.Name in self._NewSettings:
                    tip = f"Currently: {self._NewSettings[cheat.Name]}"

                cheat_options: List[OptionBoxButton] = []
                for option in cheat.AllValues:
                    cheat_options.append(OptionBoxButton(option))
                cheat_options.append(self._IgnoreButton)

                box = OptionBox(
                    Title=f"Configure '{cheat.Name}'",
                    Caption=(
                        "Select the value that this cheat should be set to when you press this"
                        " preset's keybind."
                    ),
                    Tooltip=OptionBox.CreateTooltipString(EscMessage="Back"),
                    Buttons=cheat_options,
                )

            box.OnPress = self._ChangeCheatValue  # type: ignore
            box.OnCancel = lambda: self._ConfigureBox.Show()  # type: ignore

            button = OptionBoxButton(cheat.Name, tip)
            self._CheatConfigureBoxes[cheat.Name] = box
            cheat_buttons.append(button)

        self._ConfigureBox = OptionBox(
            Title=f"Configure '{self.Name}'",
            Caption="Choose a specific cheat to configure.",
            Tooltip=OptionBox.CreateTooltipString(EscMessage="Back"),
            Buttons=cheat_buttons,
        )
        self._ConfigureBox.OnPress = self._SelectSpecificCheat  # type: ignore
        self._ConfigureBox.OnCancel = lambda: self._SaveBox.Show()  # type: ignore

    def UpdateName(self, Name: str) -> None:
        self.Name = Name
        self._SaveBox.Title = f"Save '{self.Name}'"
        self._SaveBox.Update()
        self._ConfigureBox.Title = f"Configure '{self.Name}'"
        self._ConfigureBox.Update()

    # Callback that should be overwritten
    def OnFinishConfiguring(self) -> None:
        raise NotImplementedError

    def GetSettings(self) -> Dict[str, str]:
        if self.IsBeingConfigured:
            return dict(self._OldSettings)

        return dict(self._NewSettings)

    def ApplySettings(self) -> None:
        settings = self.GetSettings()
        message = ""
        for cheat in self.CheatList:
            if cheat.Name in settings:
                if isinstance(cheat, ABCCycleableCheat):
                    cheat.CurrentValue = settings[cheat.Name]
                    cheat.OnCycle()
                    message += f"{cheat.Name}: {cheat.CurrentValue}\n"
                else:
                    cheat.OnPress()
                    message += f"Executed '{cheat.Name}'\n"

        ShowHUDMessage(self.Name, message[:-1], 5)

    def StartConfiguring(self) -> None:
        if self.IsBeingConfigured:
            raise RuntimeError("Tried to re-configure a preset that is currently being configured")
        self.IsBeingConfigured = True

        for button in self._ConfigureBox.Buttons:
            new_tip = "Currently: Ignore"
            if button.Name in self._NewSettings:
                new_tip = f"Currently: {self._NewSettings[button.Name]}"
            button.Tip = new_tip

        self._ConfigureBox.Show()

    def _FinishConfiguring(self, button: OptionBoxButton) -> None:
        if button == self._SaveButton:
            self._OldSettings = dict(self._NewSettings)
        elif button == self._DiscardButton:
            self._NewSettings = dict(self._OldSettings)

        self.IsBeingConfigured = False
        self.OnFinishConfiguring()

    def _SelectSpecificCheat(self, button: OptionBoxButton) -> None:
        for cheat in self.CheatList:
            if cheat.Name == button.Name:
                self._SelectedCheat = cheat
                break
        else:
            raise RuntimeError("Could not find cheat associated with the button just pressed")
        self._CheatConfigureBoxes[button.Name].Show()

    def _ChangeCheatValue(self, button: OptionBoxButton) -> None:
        if self._SelectedCheat is None:
            raise RuntimeError("Selected cheat is None")

        current_cheat_button: OptionBoxButton
        for cheat_button in self._ConfigureBox.Buttons:
            if cheat_button.Name == self._SelectedCheat.Name:
                current_cheat_button = cheat_button
                break
        else:
            raise RuntimeError("Could not find the button associated with the cheat just edited")

        new_tip = f"Currently: {button.Name}"

        if button in (self._IgnoreButton, self._DontRunButton):
            if self._SelectedCheat.Name in self._NewSettings:
                del self._NewSettings[self._SelectedCheat.Name]
            new_tip = "Currently: Ignore"
        else:
            self._NewSettings[self._SelectedCheat.Name] = button.Name

        current_cheat_button.Tip = new_tip

        self._SelectedCheat = None
        self._ConfigureBox.Update()
        self._ConfigureBox.Show()


class PresetManager:
    Option: Options.Hidden
    PresetList: List[Preset]
    CheatList: List[ABCCheat]

    _NewPreset: ClassVar[OptionBoxButton] = OptionBoxButton("Create New Preset")
    _OpenPresetFile: ClassVar[OptionBoxButton] = OptionBoxButton(
        "Open Settings File", (
            "Useful for reordering or sharing presets."
            " The game will have to be restarted for changes to apply."
        )
    )
    _EditPreset: ClassVar[OptionBoxButton] = OptionBoxButton("Configure")
    _RenamePreset: ClassVar[OptionBoxButton] = OptionBoxButton("Rename")
    _DeletePreset: ClassVar[OptionBoxButton] = OptionBoxButton("Delete")
    _Yes: ClassVar[OptionBoxButton] = OptionBoxButton("Yes")
    _No: ClassVar[OptionBoxButton] = OptionBoxButton("No")

    _ConfigureBox: OptionBox
    _ButtonPresetMap: Dict[str, Preset]

    _CurrentPreset: Optional[Preset]
    _PresetActionBox: OptionBox
    _ConfirmDeleteBox: OptionBox

    _RenameBox: TextInputBox

    def __init__(self, Option: Options.Hidden, CheatList: List[ABCCheat]):
        self.Option = Option
        self.CheatList = CheatList

        # Move legacy presets into the option
        legacy_path = os.path.join(os.path.dirname(__file__), "Presets.json")
        try:
            loaded_data = []
            with open(legacy_path) as file:
                loaded_data = json.load(file)
            os.remove(legacy_path)
            self.Option.CurrentValue = loaded_data
        except (FileNotFoundError, json.JSONDecodeError):
            pass

        self.LoadPresets()

        self._ConfigureBox = OptionBox(
            Title="Configure Presets",
            Caption="Select the preset you want to configure",
            Tooltip=OptionBox.CreateTooltipString(EscMessage="Exit"),
            Buttons=(
                self._NewPreset,
                self._OpenPresetFile,
            ),
        )
        self._ConfigureBox.OnPress = self._SelectSpecificPreset  # type: ignore
        self._UpdateConfigureBox()

        self._CurrentPreset = None

        # These two dialog boxes are mostly the constant, we'll just update their title as needed
        self._PresetActionBox = OptionBox(
            Title="Selected 'PRESET NAME'",
            Caption="Select the action to perform on this preset",
            Tooltip=OptionBox.CreateTooltipString(EscMessage="Back"),
            Buttons=(
                self._EditPreset,
                self._RenamePreset,
                self._DeletePreset
            ),
        )
        self._PresetActionBox.OnPress = self._SelectPresetAction  # type: ignore
        self._PresetActionBox.OnCancel = self.StartConfiguring  # type: ignore

        self._ConfirmDeleteBox = OptionBox(
            Title="Delete 'PRESET NAME'",
            Caption="Are you sure you want to delete this preset?",
            Tooltip=OptionBox.CreateTooltipString(EscMessage="Back"),
            Buttons=(
                self._No,
                self._Yes
            ),
        )
        self._ConfirmDeleteBox.OnPress = self._OnConfirmDelete  # type: ignore
        self._ConfirmDeleteBox.OnCancel = lambda: self._OnConfirmDelete(None)  # type: ignore

        self._RenameBox = TextInputBox("Rename 'PRESET NAME'")
        self._RenameBox.OnSubmit = self._OnPresetRename  # type: ignore

    def LoadPresets(self) -> None:
        self.PresetList = []
        for idx, current_dict in enumerate(self.Option.CurrentValue):
            name: str = f"Preset {idx}"
            settings: Dict[str, str] = {}

            if "Name" in current_dict:
                name = html.escape(str(current_dict["Name"]))

            if "Settings" in current_dict and isinstance(current_dict["Settings"], dict):
                settings = current_dict["Settings"]
                # Sanity-check the data
                for cheat in self.CheatList:
                    if cheat.Name in settings:
                        value = settings[cheat.Name]
                        # We don't really care what this value is for regular cheats, but better to
                        #  keep it consistent
                        if not isinstance(cheat, ABCCycleableCheat):
                            value = "Run"
                        settings[cheat.Name] = value

            current_preset = Preset(name, settings, self.CheatList)
            current_preset.OnFinishConfiguring = self._OnFinishConfiguringPreset  # type: ignore
            self.PresetList.append(current_preset)

        # If there are no valid presets then still add the first one
        if len(self.PresetList) == 0:
            new_preset = Preset("Preset 1", {}, self.CheatList)
            new_preset.OnFinishConfiguring = self._OnFinishConfiguringPreset  # type: ignore
            self.PresetList.append(new_preset)

    def SavePresets(self) -> None:
        data = []
        for preset in self.PresetList:
            data.append({
                "Name": html.unescape(preset.Name),
                "Settings": preset.GetSettings()
            })

        self.Option.CurrentValue = data
        self.SaveOptions()

    def StartConfiguring(self) -> None:
        self._UpdateConfigureBox()
        self._ConfigureBox.Show()

    # The next four functions should be overwritten by the main mod
    def AddKeybind(self, Name: str) -> None:
        raise NotImplementedError

    def RenameKeybind(self, OldName: str, NewName: str) -> None:
        raise NotImplementedError

    def RemoveKeybind(self, Name: str) -> None:
        raise NotImplementedError

    def SaveOptions(self) -> None:
        raise NotImplementedError

    def _OnFinishConfiguringPreset(self) -> None:
        self.SavePresets()
        self.StartConfiguring()

    def _UpdateConfigureBox(self) -> None:
        button_list = []
        self._ButtonPresetMap = {}
        for preset in self.PresetList:
            button = OptionBoxButton(html.unescape(preset.Name))
            button_list.append(button)
            self._ButtonPresetMap[button.Name] = preset

        button_list += [
            self._NewPreset,
            self._OpenPresetFile,
        ]

        self._ConfigureBox.Buttons = button_list
        self._ConfigureBox.Update()

    def _SelectSpecificPreset(self, button: OptionBoxButton) -> None:
        if button == self._NewPreset:
            # Get a new default name that's at least the size of the list + 1, or the largest
            #  existing default name + 1
            # This makes renaming or deleting cheats still add a somewhat logical name
            max_val = len(self.PresetList)
            for preset in self.PresetList:
                val: int
                try:
                    val = int(preset.Name.split(" ")[-1])
                except ValueError:
                    continue
                if val > max_val:
                    max_val = val
            name = f"Preset {max_val + 1}"

            new_preset = Preset(name, {}, self.CheatList)
            new_preset.OnFinishConfiguring = self._OnFinishConfiguringPreset  # type: ignore
            self.PresetList.append(new_preset)

            self.AddKeybind(name)

            self.SavePresets()
        elif button == self._OpenPresetFile:
            settings_path = os.path.join(os.path.dirname(__file__), "settings.json")
            os.startfile(settings_path)

        if button.Name in self._ButtonPresetMap:
            self._CurrentPreset = self._ButtonPresetMap[button.Name]
            self._PresetActionBox.Title = f"Selected '{self._CurrentPreset.Name}'"
            self._PresetActionBox.Update()
            self._PresetActionBox.Show()
            return

        self.StartConfiguring()

    def _SelectPresetAction(self, button: OptionBoxButton) -> None:
        if self._CurrentPreset is None:
            raise RuntimeError("Current Preset is None")
        if button == self._EditPreset:
            self._CurrentPreset.StartConfiguring()
            self._CurrentPreset = None
        elif button == self._RenamePreset:
            self._RenameBox.Title = f"Rename '{self._CurrentPreset.Name}'"
            self._RenameBox.DefaultMessage = self._CurrentPreset.Name
            self._RenameBox.Show()
        elif button == self._DeletePreset:
            self._ConfirmDeleteBox.Title = f"Delete '{self._CurrentPreset.Name}'"
            self._ConfirmDeleteBox.Update()
            self._ConfirmDeleteBox.Show()

    def _OnPresetRename(self, msg: str) -> None:
        if self._CurrentPreset is None:
            raise RuntimeError("Current Preset is None")

        if len(msg) > 0:
            self.RenameKeybind(self._CurrentPreset.Name, msg)

            self._ButtonPresetMap[msg] = self._ButtonPresetMap[self._CurrentPreset.Name]
            del self._ButtonPresetMap[self._CurrentPreset.Name]

            self._CurrentPreset.UpdateName(msg)
            self.SavePresets()
            self._UpdateConfigureBox()

        self._PresetActionBox.Title = f"Selected '{self._CurrentPreset.Name}'"
        self._PresetActionBox.Update()
        self._PresetActionBox.Show(self._RenamePreset)

    def _OnConfirmDelete(self, button: Optional[OptionBoxButton]) -> None:
        if self._CurrentPreset is None:
            raise RuntimeError("Current Preset is None")
        if button == self._Yes:
            self.PresetList.remove(self._CurrentPreset)
            self.RemoveKeybind(self._CurrentPreset.Name)
            self._CurrentPreset = None
            self.SavePresets()
            self.StartConfiguring()
        else:
            self._PresetActionBox.Show()
