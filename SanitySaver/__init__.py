import unrealsdk
import importlib
from typing import Dict

from Mods.ModMenu import EnabledSaveType, Mods, ModTypes, Options, RegisterMod, SDKMod

from .helpers import obj_cache
from .hooks import AllHooks
from .save_manager import update_compression


class SanitySaver(SDKMod):
    Name: str = "Sanity Saver"
    Author: str = "apple1417"
    Description: str = (
        "Disables sanity check, and also saves items which don't serialize, which would have parts"
        " deleted even with it off."
    )
    Version: str = "1.1"

    Types: ModTypes = ModTypes.Utility
    SaveEnabledState: EnabledSaveType = EnabledSaveType.LoadWithSettings

    SettingsInputs: Dict[str, str] = {
        "Enter": "Enable",
        "C": "Clear Cache"
    }

    CompressOption: Options.Hidden[bool]

    def __init__(self) -> None:
        self.CompressOption = Options.Hidden("CompressSaves", StartingValue=True)
        self.Options = [self.CompressOption]

    def Enable(self) -> None:
        update_compression(self.CompressOption.CurrentValue)
        for func, hook in AllHooks.items():
            unrealsdk.RunHook(func, self.Name, hook)

    def Disable(self) -> None:
        for func in AllHooks.keys():
            unrealsdk.RemoveHook(func, self.Name)

    def SettingsInputPressed(self, action: str) -> None:
        if action == "Clear Part Cache":
            obj_cache.clear()
        else:
            super().SettingsInputPressed(action)


instance = SanitySaver()
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
RegisterMod(instance)


def _add_incompat_hook(mod_module: str, mod_class: str) -> None:
    try:
        module = importlib.import_module("Mods." + mod_module)
        mod = getattr(module, mod_class)
    except (AttributeError, ImportError):
        return

    old_enable = mod.Enable

    def new_enable(self: SDKMod) -> None:
        if instance.IsEnabled:
            instance.Disable()
        if "Enter" in instance.SettingsInputs:
            del instance.SettingsInputs["Enter"]
        instance.Status = f"<font color=\"#FFFF00\">Incompatible with {mod.Name}</font>"
        old_enable(self)

    mod.Enable = new_enable


_add_incompat_hook("Constructor", "Main")
_add_incompat_hook("Exodus", "Exodus")
