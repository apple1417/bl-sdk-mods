import json
import html
from os import startfile
from typing import ClassVar, Dict, List, Optional, Tuple, Union

from .Cheats import ABCCheat
from .Cheats import ABCCycleableCheat
from .Cheats import ABCOptions
from UserFeedback import OptionBox
from UserFeedback import OptionBoxButton
from UserFeedback import ShowHUDMessage
from UserFeedback import TextInputBox

_AllCheats: Tuple[ABCCheat, ...] = ABCOptions().All


class Preset:
    Name: str
    IsBeingConfigured: bool

    _NewSettings: Dict[str, str]
    _OldSettings: Dict[str, str]

    _SelectedCheat: Optional[ABCCheat]
    _ConfigureBox: OptionBox
    _SaveBox: OptionBox
    _CheatConfigureBoxes: Dict[OptionBoxButton, OptionBox]

    _SaveButton: ClassVar[OptionBoxButton] = OptionBoxButton("Save")
    _DiscardButton: ClassVar[OptionBoxButton] = OptionBoxButton("Discard")
    _DontRunButton: ClassVar[OptionBoxButton] = OptionBoxButton("Ignore")
    _RunButton: ClassVar[OptionBoxButton] = OptionBoxButton("Run")
    _IgnoreButton: ClassVar[OptionBoxButton] = OptionBoxButton(
        "Ignore",
        "Do not change this cheat's state."
    )

    def __init__(self, Name: str, Settings: Dict[str, str]) -> None:
        self.Name = Name
        self.IsBeingConfigured = False

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
        cheatButtons: List[OptionBoxButton] = []
        for cheat in _AllCheats:
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

                cheatOptions: List[OptionBoxButton] = []
                for option in cheat.Order:
                    cheatOptions.append(OptionBoxButton(option))
                cheatOptions.append(self._IgnoreButton)

                box = OptionBox(
                    Title=f"Configure '{cheat.Name}'",
                    Caption=(
                        "Select the value that this cheat should be set to when you press this"
                        " preset's keybind."
                    ),
                    Tooltip=OptionBox.CreateTooltipString(EscMessage="Back"),
                    Buttons=cheatOptions,
                )

            box.OnPress = self._ChangeCheatValue  # type: ignore
            box.OnCancel = lambda: self._ConfigureBox.Show()  # type: ignore

            button = OptionBoxButton(cheat.Name, tip)
            self._CheatConfigureBoxes[button] = box
            cheatButtons.append(button)

        self._ConfigureBox = OptionBox(
            Title=f"Configure '{self.Name}'",
            Caption="Choose a specific cheat to configure.",
            Tooltip=OptionBox.CreateTooltipString(EscMessage="Back"),
            Buttons=cheatButtons,
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

    def ApplySettings(self, options: ABCOptions) -> None:
        settings = self.GetSettings()
        message = ""
        for cheat in options.All:
            if cheat.Name in settings:
                if isinstance(cheat, ABCCycleableCheat):
                    cheat.value = settings[cheat.Name]
                    cheat.OnCycle()
                    message += f"{cheat.Name}: {cheat.value}\n"
                else:
                    cheat.OnPress()
                    message += f"Executed '{cheat.Name}'\n"

        ShowHUDMessage(self.Name, message[:-1], 5)

    def StartConfiguring(self) -> None:
        if self.IsBeingConfigured:
            raise RuntimeError("Tried to re-configure a preset that is currently being configured")
        self.IsBeingConfigured = True
        self._ConfigureBox.Show()

    def _FinishConfiguring(self, button: OptionBoxButton) -> None:
        if button == self._SaveButton:
            self._OldSettings = dict(self._NewSettings)
        elif button == self._DiscardButton:
            self._NewSettings = dict(self._OldSettings)

        for page in self._ConfigureBox.Buttons:
            tip = "Currently: Ignore"
            if button.Name in self._NewSettings:
                tip = f"Currently: {self._NewSettings[button.Name]}"
            button.Tip = tip
        self._ConfigureBox.Update()

        self.IsBeingConfigured = False
        self.OnFinishConfiguring()

    def _SelectSpecificCheat(self, button: OptionBoxButton) -> None:
        for cheat in _AllCheats:
            if cheat.Name == button.Name:
                self._SelectedCheat = cheat
                break
        else:
            raise RuntimeError("Could not find cheat associated with the button just pressed")
        self._CheatConfigureBoxes[button].Show()

    def _ChangeCheatValue(self, button: OptionBoxButton) -> None:
        if self._SelectedCheat is None:
            raise RuntimeError("Selected cheat is None")

        currentCheatButton: OptionBoxButton
        for cheatButton in self._ConfigureBox.Buttons:
            if cheatButton.Name == self._SelectedCheat.Name:
                currentCheatButton = cheatButton
                break
        else:
            raise RuntimeError("Could not find the button associated with the cheat just edited")

        newTip = f"Currently: {button.Name}"

        if button == self._IgnoreButton or button == self._DontRunButton:
            if self._SelectedCheat.Name in self._NewSettings:
                del self._NewSettings[self._SelectedCheat.Name]
            newTip = "Currently: Ignore"
        else:
            self._NewSettings[self._SelectedCheat.Name] = button.Name

        currentCheatButton.Tip = newTip

        self._SelectedCheat = None
        self._ConfigureBox.Update()
        self._ConfigureBox.Show()


class PresetManager:
    FileName: str
    PresetList: List[Preset]

    _NewPreset: ClassVar[OptionBoxButton] = OptionBoxButton("Create New Preset")
    _OpenPresetFile: ClassVar[OptionBoxButton] = OptionBoxButton(
        "Open Preset File",
        "Useful for reordering or sharing presets."
    )
    _EditPreset: ClassVar[OptionBoxButton] = OptionBoxButton("Configure")
    _RenamePreset: ClassVar[OptionBoxButton] = OptionBoxButton("Rename")
    _DeletePreset: ClassVar[OptionBoxButton] = OptionBoxButton("Delete")
    _Yes: ClassVar[OptionBoxButton] = OptionBoxButton("Yes")
    _No: ClassVar[OptionBoxButton] = OptionBoxButton("No")

    _ConfigureBox: OptionBox
    _ButtonPresetMap: Dict[OptionBoxButton, Preset]

    _CurrentPreset: Optional[Preset]
    _PresetActionBox: OptionBox
    _ConfirmDeleteBox: OptionBox

    _RenameBox: TextInputBox

    def __init__(self, FileName: str):
        self.FileName = FileName

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
        self.LoadPresets()
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
        loadedData: List[Dict[str, Union[str, Dict[str, str]]]] = []
        try:
            with open(self.FileName) as file:
                loadedData = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

        self.PresetList = []
        for i in range(len(loadedData)):
            currentDict = loadedData[i]
            name: str = f"Preset {i}"
            settings: Dict[str, str] = {}

            if "Name" in currentDict:
                name = html.escape(str(currentDict["Name"]))

            if "Settings" in currentDict and isinstance(currentDict["Settings"], dict):
                settings = currentDict["Settings"]
                # Sanity-check the data
                for cheat in _AllCheats:
                    if cheat.Name in settings:
                        value = settings[cheat.Name]
                        # We don't really care what this value is for regular cheats, but better to
                        #  keep it consistent
                        if not isinstance(cheat, ABCCycleableCheat):
                            value = "Run"
                        settings[cheat.Name] = value

            currentPreset = Preset(name, settings)
            currentPreset.OnFinishConfiguring = self._OnFinishConfiguringPreset  # type: ignore
            self.PresetList.append(currentPreset)

        # If there are no valid presets then still add the first one
        if len(self.PresetList) == 0:
            newPreset = Preset("Preset 1", {})
            newPreset.OnFinishConfiguring = self._OnFinishConfiguringPreset  # type: ignore
            self.PresetList.append(newPreset)

        # Save the sanity-checked info
        self.SavePresets()
        self.ReloadAllKeybinds()

    def SavePresets(self) -> None:
        data = []
        for preset in self.PresetList:
            data.append({
                "Name": html.unescape(preset.Name),
                "Settings": preset.GetSettings()
            })

        with open(self.FileName, "w") as file:
            json.dump(data, file, indent=2)

    def StartConfiguring(self) -> None:
        self.LoadPresets()
        self._UpdateConfigureBox()
        self._ConfigureBox.Show()

    # The next four functions should be overwritten by the main mod
    def AddKeybind(self, Name: str) -> None:
        raise NotImplementedError

    def RenameKeybind(self, OldName: str, NewName: str) -> None:
        raise NotImplementedError

    def RemoveKeybind(self, Name: str) -> None:
        raise NotImplementedError

    # Only passing cause we call this as part of the constructer
    def ReloadAllKeybinds(self) -> None:
        pass

    def _OnFinishConfiguringPreset(self) -> None:
        self.SavePresets()
        self.StartConfiguring()

    def _UpdateConfigureBox(self) -> None:
        buttonList = []
        self._ButtonPresetMap = {}
        for preset in self.PresetList:
            button = OptionBoxButton(html.unescape(preset.Name))
            buttonList.append(button)
            self._ButtonPresetMap[button] = preset

        buttonList += [
            self._NewPreset,
            self._OpenPresetFile,
        ]

        self._ConfigureBox.Buttons = buttonList
        self._ConfigureBox.Update()

    def _SelectSpecificPreset(self, button: OptionBoxButton) -> None:
        if button == self._NewPreset:
            # Get a new default name that's at least the size of the list + 1, or the largest
            #  existing default name + 1
            # This makes renaming or deleting cheats still add a somewhat logical name
            maxVal = len(self.PresetList)
            for preset in self.PresetList:
                val: int
                try:
                    val = int(preset.Name.split(" ")[-1])
                except ValueError:
                    continue
                if val > maxVal:
                    maxVal = val
            name = f"Preset {maxVal + 1}"

            newPreset = Preset(name, {})
            newPreset.OnFinishConfiguring = self._OnFinishConfiguringPreset  # type: ignore
            self.PresetList.append(newPreset)

            self.AddKeybind(name)

            self.SavePresets()
        elif button == self._OpenPresetFile:
            startfile(self.FileName)

        if button in self._ButtonPresetMap:
            self._CurrentPreset = self._ButtonPresetMap[button]
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

            self._CurrentPreset.UpdateName(msg)
            self.SavePresets()
            self._UpdateConfigureBox()

        self._PresetActionBox.Title = f"Selected '{self._CurrentPreset.Name}'"
        self._PresetActionBox.Update()
        self._PresetActionBox.ShowButton(self._RenamePreset)

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
