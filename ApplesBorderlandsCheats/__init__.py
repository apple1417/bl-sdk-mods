import unrealsdk
import html
from typing import Dict, List

from Mods.ModMenu import (EnabledSaveType, InputEvent, Keybind, LoadModSettings, Mods, ModTypes,
                          Options, SaveModSettings, SDKMod)

try:
    from Mods import UserFeedback
    if UserFeedback.VersionMajor < 1:
        raise RuntimeError("UserFeedback version is too old, need at least v1.3!")
    if UserFeedback.VersionMajor == 1 and UserFeedback.VersionMinor < 3:
        raise RuntimeError("UserFeedback version is too old, need at least v1.3!")
# UF 1.0 didn't have version fields, hence the `NameError`
except (ImportError, RuntimeError, NameError) as ex:
    import webbrowser
    url = "https://apple1417.github.io/bl2/didntread/?m=Apple%27s%20Borderlands%20Cheats&uf=v1.3"
    if isinstance(ex, (RuntimeError, NameError)):
        url += "&update"
    webbrowser.open(url)
    raise ex


# Some setup to let this run just as well if you re-exec the file as when it was intially imported
if __name__ == "__main__":
    import importlib
    import sys
    importlib.reload(sys.modules["Mods.ApplesBorderlandsCheats.Cheats"])
    importlib.reload(sys.modules["Mods.ApplesBorderlandsCheats.Presets"])

    # See https://github.com/bl-sdk/PythonSDK/issues/68
    try:
        raise NotImplementedError
    except NotImplementedError:
        __file__ = sys.exc_info()[-1].tb_frame.f_code.co_filename  # type: ignore


from .Cheats import ALL_CHEATS, ALL_HOOKS, ALL_OPTIONS
from .Presets import PresetManager


class ApplesBorderlandsCheats(SDKMod):
    Name: str = "Apple's Borderlands Cheats"
    Author: str = "apple1417"
    Description: str = (
        "Adds keybinds performing various cheaty things"
    )
    Version: str = "1.12"

    Types: ModTypes = ModTypes.Utility
    SaveEnabledState: EnabledSaveType = EnabledSaveType.LoadWithSettings

    SettingsInputs: Dict[str, str] = {
        "Enter": "Enable",
        "P": "Configure Presets"
    }
    Keybinds: List[Keybind] = []  # Just here to cast sequence to list

    CheatPresetManager: PresetManager

    _is_enabled: bool = False
    _initalized: bool = False

    # Overwriting IsEnabled to not save settings until the mod's initalized
    @property
    def IsEnabled(self) -> bool:
        return self._is_enabled

    @IsEnabled.setter
    def IsEnabled(self, val: bool) -> None:
        self._is_enabled = val
        if self._initalized:
            SaveModSettings(self)

    def __init__(self) -> None:
        preset_option = Options.Hidden("Presets", StartingValue=[])
        self.Options = [preset_option] + ALL_OPTIONS  # type: ignore

        # Load settings once for the set of presets
        LoadModSettings(self)

        self.CheatPresetManager = PresetManager(preset_option, ALL_CHEATS)

        # This is a kind of hacky way for the preset manager to interface with the keybinds system
        # Output from the preset manager is html-escaped, the keybind menu doesn't use html, so this
        #  stuff all has to convert it
        def AddPresetKeybind(name: str) -> None:
            self.Keybinds.append(Keybind(html.unescape(name)))
            SaveModSettings(self)

        def RenamePresetKeybind(oldName: str, newName: str) -> None:
            for bind in self.Keybinds:
                if bind.Name == html.unescape(oldName):
                    bind.Name = html.unescape(newName)
            SaveModSettings(self)

        def RemovePresetKeybind(name: str) -> None:
            for bind in self.Keybinds:
                if bind.Name == html.unescape(name):
                    self.Keybinds.remove(bind)
            SaveModSettings(self)

        self.CheatPresetManager.AddKeybind = AddPresetKeybind  # type: ignore
        self.CheatPresetManager.RenameKeybind = RenamePresetKeybind  # type: ignore
        self.CheatPresetManager.RemoveKeybind = RemovePresetKeybind  # type: ignore
        self.CheatPresetManager.SaveOptions = lambda: SaveModSettings(self)  # type: ignore

        self.Keybinds = []
        for cheat in ALL_CHEATS:
            self.Keybinds.append(Keybind(cheat.KeybindName))

        for preset in self.CheatPresetManager.PresetList:
            self.Keybinds.append(Keybind(html.unescape(preset.Name)))

        # Load settings again to fill in the keybinds
        LoadModSettings(self)
        self._initalized = True

    def SettingsInputPressed(self, action: str) -> None:
        if action == "Configure Presets":
            self.CheatPresetManager.StartConfiguring()
        else:
            super().SettingsInputPressed(action)

    def GameInputPressed(self, bind: Keybind, event: InputEvent) -> None:
        if event != InputEvent.Pressed:
            return

        for cheat in ALL_CHEATS:
            if bind.Name == cheat.KeybindName:
                cheat.OnPress()
        for preset in self.CheatPresetManager.PresetList:
            if bind.Name == preset.Name:
                preset.ApplySettings()

    def Enable(self) -> None:
        for hook, func_list in ALL_HOOKS.items():
            for i, func in enumerate(func_list):
                unrealsdk.RunHook(hook, f"{self.Name}{i}", func)

    def Disable(self) -> None:
        for hook, func_list in ALL_HOOKS.items():
            for i, func in enumerate(func_list):
                unrealsdk.RemoveHook(hook, f"{self.Name}{i}")


instance = ApplesBorderlandsCheats()
if __name__ == "__main__":
    unrealsdk.Log(f"[{instance.Name}] Manually loaded")
    for mod in Mods:
        if mod.Name == instance.Name:
            if mod.IsEnabled:
                mod.Disable()
            Mods.remove(mod)
            unrealsdk.Log(f"[{instance.Name}] Removed last instance")

            # Fixes inspect.getfile()
            instance.__class__.__module__ = mod.__class__.__module__
            break
Mods.append(instance)
