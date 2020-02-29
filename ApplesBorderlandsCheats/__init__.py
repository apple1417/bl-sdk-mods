import unrealsdk
from Mods.SaveManager import storeModSettings  # type: ignore
from Mods.KeybindManager import KeybindBinding  # type: ignore

import html
from os import path
from typing import ClassVar, Dict, List

# Some setup to let this run just as well if you re-exec the file as when it was intially imported
if __name__ == "__main__":
    import importlib
    import sys
    unrealsdk.Log("[ABC] Reloading other modules")
    importlib.reload(sys.modules["Mods.ApplesBorderlandsCheats.Cheats"])
    importlib.reload(sys.modules["Mods.ApplesBorderlandsCheats.Presets"])

    # __file__ isn't set when you call this through a pyexec, so we have to do something real silly
    # If we cause an exception then the traceback will contain the file name, which we can regex out
    import re
    import traceback
    try:
        fake += 1  # type: ignore
    except NameError:
        match = re.search(r"File \"(.*?)\", line", traceback.format_exc())
        if match is not None:
            __file__ = match.group(1)
    unrealsdk.Log(f"[ABC] File path: {__file__}")

# It complains that these aren't at the top of the file but we might need to reload them first
from Mods.ApplesBorderlandsCheats.Cheats import ABCOptions  # noqa
from Mods.ApplesBorderlandsCheats.Presets import PresetManager  # noqa


class ApplesBorderlandsCheats(unrealsdk.BL2MOD):
    Name: ClassVar[str] = "Apple's Borderlands Cheats"
    Author: ClassVar[str] = "apple1417"
    Description: ClassVar[str] = (
        "Adds keybinds performing various cheaty things"
    )
    Types: ClassVar[List[unrealsdk.ModTypes]] = [unrealsdk.ModTypes.Utility]
    Version: ClassVar[str] = "1.3"

    PRESET_PATH: ClassVar[str] = path.join(path.dirname(path.realpath(__file__)), "Presets.json")

    CheatOptions: ClassVar[ABCOptions] = ABCOptions()
    CheatPresetManager: PresetManager = PresetManager(PRESET_PATH)

    SettingsInputs: Dict[str, str]
    Keybinds: List[List[str]]

    def __init__(self) -> None:
        # Hopefully I can remove this in a future SDK update
        self.Author += "\nVersion: " + str(self.Version)  # type: ignore

        self.SettingsInputs = {
            "Enter": "Enable",
            "P": "Configure Presets",
            "R": "Reset Keybinds"
        }

        # This is a kind of hacky way for the preset manager to interface with the keybinds system
        # It's because the keybinds system is badly made and requires the main mod instance to
        #  register all binds itself, just so that it can use the single callback on that instance
        # It would be much better if you could provide a custom callback per keybind - even if
        #  you're not using something like my preset system, with any decent amount of binds you're
        #  going to split up the callbacks anyway, it just gets too messy all being in one function
        # Hooks already work in this way too so it'd only help standardize code more

        # Output from the preset manager is html-escaped, the keybind menu doesn't use html, so this
        #  stuff all has to convert it
        def AddPresetKeybind(name: str) -> None:
            self.Keybinds.append([html.unescape(name), "None"])
            storeModSettings()

        def RenamePresetKeybind(oldName: str, newName: str) -> None:
            for bind in self.Keybinds:
                if bind[0] == html.unescape(oldName):
                    bind[0] = html.unescape(newName)
            storeModSettings()

        def RemovePresetKeybind(name: str) -> None:
            for bind in self.Keybinds:
                if bind[0] == html.unescape(name):
                    self.Keybinds.remove(bind)
            storeModSettings()

        self.CheatPresetManager.AddKeybind = AddPresetKeybind  # type: ignore
        self.CheatPresetManager.RenameKeybind = RenamePresetKeybind  # type: ignore
        self.CheatPresetManager.RemoveKeybind = RemovePresetKeybind  # type: ignore

        self.Keybinds = []
        for cheat in self.CheatOptions.All:
            self.Keybinds.append([cheat.KeybindName, "None"])

        for preset in self.CheatPresetManager.PresetList:
            self.Keybinds.append([html.unescape(preset.Name), "None"])

        storeModSettings()

    def SettingsInputPressed(self, name: str) -> None:
        if name == "Enable":
            self.Status = "Enabled"
            self.SettingsInputs["Enter"] = "Disable"
            self.Enable()
        elif name == "Disable":
            self.Status = "Disabled"
            self.SettingsInputs["Enter"] = "Enable"
            self.Disable()
        elif name == "Configure Presets":
            self.CheatPresetManager.StartConfiguring()
        elif name == "Reset Keybinds":
            for bind in self.Keybinds:
                bind[1] = "None"
            storeModSettings()

    def GameInputPressed(self, input: KeybindBinding) -> None:
        for cheat in self.CheatOptions.All:
            if input.Name == cheat.KeybindName:
                cheat.OnPress()
        for preset in self.CheatPresetManager.PresetList:
            if input.Name == preset.Name:
                preset.ApplySettings(self.CheatOptions)

    def Enable(self) -> None:
        for hook, funcList in self.CheatOptions.Hooks.items():
            for i in range(len(funcList)):
                unrealsdk.RegisterHook(hook, f"ApplesBorderlandsCheats_{i}", funcList[i])

    def Disable(self) -> None:
        for hook, funcList in self.CheatOptions.Hooks.items():
            for i in range(len(funcList)):
                unrealsdk.RemoveHook(hook, f"ApplesBorderlandsCheats_{i}")


instance = ApplesBorderlandsCheats()
if __name__ != "__main__":
    unrealsdk.RegisterMod(instance)
else:
    unrealsdk.Log(f"[{instance.Name}] Manually loaded")
    for i in range(len(unrealsdk.Mods)):
        mod = unrealsdk.Mods[i]
        if unrealsdk.Mods[i].Name == instance.Name:
            unrealsdk.Mods[i].Disable()

            unrealsdk.RegisterMod(instance)
            unrealsdk.Mods.remove(instance)
            unrealsdk.Mods[i] = instance
            unrealsdk.Log(f"[{instance.Name}] Disabled and removed last instance")
            break
    else:
        unrealsdk.Log(f"[{instance.Name}] Could not find previous instance")
        unrealsdk.RegisterMod(instance)

    unrealsdk.Log(f"[{instance.Name}] Auto-enabling")
    instance.Status = "Enabled"
    instance.SettingsInputs["Enter"] = "Disable"
    instance.Enable()
