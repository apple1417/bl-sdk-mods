import bl2sdk
import html
import json
import os
from typing import ClassVar, Dict, List

# Some setup to let this run just as well if you re-exec the file as when it was intially imported
if __name__ == "__main__":
    import importlib
    import sys
    bl2sdk.Log("[ABC] Reloading other modules")
    importlib.reload(sys.modules["ApplesBorderlandsCheats.Cheats"])
    importlib.reload(sys.modules["ApplesBorderlandsCheats.Presets"])

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
    bl2sdk.Log(f"[ABC] File path: {__file__}")

# It complains that these aren't at the top of the file but we might need to reload them first
from ApplesBorderlandsCheats.Cheats import ABCOptions  # noqa
from ApplesBorderlandsCheats.Presets import PresetManager  # noqa


class ApplesBorderlandsCheats(bl2sdk.BL2MOD):
    Name: ClassVar[str] = "Apple's Borderlands Cheats"
    Author: ClassVar[str] = "apple1417"
    Description: ClassVar[str] = (
        "Adds keybinds performing various cheaty things"
    )
    Types: ClassVar[List[bl2sdk.ModTypes]] = [bl2sdk.ModTypes.Utility]
    Version: ClassVar[str] = "1.2"

    BASE_PATH: ClassVar[str] = os.path.dirname(os.path.realpath(__file__))
    KEYBIND_PATH: ClassVar[str] = os.path.join(BASE_PATH, "Keybinds.json")
    PRESET_PATH: ClassVar[str] = os.path.join(BASE_PATH, "Presets.json")

    SettingsInputs: Dict[str, str] = {
        "Enter": "Enable",
        "P": "Configure Presets",
        "R": "Reset Keybinds"
    }

    def __init__(self) -> None:
        # Hopefully I can remove this in a future SDK update
        self.Author += "\nVersion: " + str(self.Version)  # type: ignore

        self.Options = ABCOptions()
        self.PresetManager = PresetManager(self.PRESET_PATH)

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
            self.Keybinds[html.unescape(name)] = "None"
            if self.Status == "Enabled":
                self.RegisterGameInput(html.unescape(name), "None")
            self.SaveKeybinds()

        def RenamePresetKeybind(oldName: str, newName: str) -> None:
            bind = self.Keybinds[html.unescape(oldName)]
            del self.Keybinds[html.unescape(oldName)]
            self.Keybinds[html.unescape(newName)] = bind
            if self.Status == "Enabled":
                self.UnregisterGameInput(html.unescape(oldName))
                self.RegisterGameInput(html.unescape(newName), bind)
            self.SaveKeybinds()

        def RemovePresetKeybind(name: str) -> None:
            del self.Keybinds[html.unescape(name)]
            if self.Status == "Enabled":
                self.UnregisterGameInput(html.unescape(name))
            self.SaveKeybinds()

        def ReloadAllKeybinds() -> None:
            if self.Status == "Enabled":
                for key in self.Keybinds:
                    self.UnregisterGameInput(key)
            self.LoadKeybinds()
            if self.Status == "Enabled":
                for name, key in self.Keybinds.items():
                    self.RegisterGameInput(name, key)

        self.PresetManager.AddKeybind = AddPresetKeybind  # type: ignore
        self.PresetManager.RenameKeybind = RenamePresetKeybind  # type: ignore
        self.PresetManager.RemoveKeybind = RemovePresetKeybind  # type: ignore
        self.PresetManager.ReloadAllKeybinds = ReloadAllKeybinds  # type: ignore
        self.LoadKeybinds()

    def LoadKeybinds(self) -> None:
        loadedBinds: Dict[str, str] = {}
        try:
            with open(self.KEYBIND_PATH) as file:
                loadedBinds = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

        # Limit to just the binds associated with valid cheats/presets
        self.Keybinds: Dict[str, str] = {}
        for cheat in self.Options.All:
            if cheat.KeybindName in loadedBinds:
                self.Keybinds[cheat.KeybindName] = loadedBinds[cheat.KeybindName]
            else:
                self.Keybinds[cheat.KeybindName] = "None"
        for preset in self.PresetManager.PresetList:
            name = html.unescape(preset.Name)
            if name in loadedBinds:
                self.Keybinds[name] = loadedBinds[name]
            else:
                self.Keybinds[name] = "None"

        self.SaveKeybinds()

    def SaveKeybinds(self) -> None:
        with open(self.KEYBIND_PATH, "w") as file:
            json.dump(self.Keybinds, file, indent=2)

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
            self.PresetManager.StartConfiguring()
        elif name == "Reset Keybinds":
            if self.Status == "Enabled":
                for name in self.Keybinds:
                    self.UnregisterGameInput(name)
                    self.RegisterGameInput(name, "None")
                    self.Keybinds[name] = "None"
            try:
                os.remove(self.KEYBIND_PATH)
            except FileNotFoundError:
                pass

    def GameInputRebound(self, name: str, key: str) -> None:
        if name not in self.Keybinds:
            return
        self.Keybinds[name] = key

        self.SaveKeybinds()

    def GameInputPressed(self, input) -> None:  # type: ignore
        for cheat in self.Options.All:
            if input.Name == cheat.KeybindName:
                cheat.OnPress()
        for preset in self.PresetManager.PresetList:
            if input.Name == preset.Name:
                preset.ApplySettings(self.Options)

    def Enable(self) -> None:
        for hook, funcList in self.Options.Hooks.items():
            for i in range(len(funcList)):
                bl2sdk.RegisterHook(hook, f"ApplesBorderlandsCheats_{i}", funcList[i])

        self.LoadKeybinds()
        for name, key in self.Keybinds.items():
            self.RegisterGameInput(name, key)

    def Disable(self) -> None:
        for hook, funcList in self.Options.Hooks.items():
            for i in range(len(funcList)):
                bl2sdk.RemoveHook(hook, f"ApplesBorderlandsCheats_{i}")

        # SDK causes errors if you try unregister a keybind that hasn't been registered
        for name in self.Keybinds:
            try:
                self.UnregisterGameInput(name)
            except KeyError:
                pass


instance = ApplesBorderlandsCheats()
if __name__ != "__main__":
    bl2sdk.Mods.append(instance)
else:
    bl2sdk.Log("[ABC] Manually loaded")
    for i in range(len(bl2sdk.Mods)):
        mod = bl2sdk.Mods[i]
        if bl2sdk.Mods[i].Name == instance.Name:
            bl2sdk.Mods[i].Disable()
            bl2sdk.Mods[i] = instance
            bl2sdk.Log("[ABC] Disabled and removed last instance")
            break
    else:
        bl2sdk.Log("[ABC] Could not find previous instance")
        bl2sdk.Mods.append(instance)

    bl2sdk.Log("[ABC] Auto-enabling")
    instance.Status = "Enabled"
    instance.SettingsInputs["Enter"] = "Disable"
    instance.Enable()
