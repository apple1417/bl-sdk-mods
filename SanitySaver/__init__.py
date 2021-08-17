import unrealsdk
import importlib
from typing import Any, ClassVar, Dict

from Mods.ModMenu import EnabledSaveType, Mods, ModTypes, Options, RegisterMod, SDKMod

from .compression_handler import update_compression
from .console import disable_console_commands, enable_console_commands
from .helpers import cached_obj_find
from .hooks import AllHooks, update_vendor_rerolling
from .migrations import migrate_all
from .save_manager import SAVE_VERSION


class SanitySaver(SDKMod):
    Name: str = "Sanity Saver"
    Author: str = "apple1417"
    Description: str = (
        "Disables sanity check, and also saves items which don't serialize, which would have parts"
        " deleted even with it off."
    )
    Version: str = f"{SAVE_VERSION}.2"

    Types: ModTypes = ModTypes.Utility
    SaveEnabledState: EnabledSaveType = EnabledSaveType.LoadWithSettings

    CLEAR_CACHE: ClassVar[str] = "Clear Cache"

    SettingsInputs: Dict[str, str] = {
        "Enter": "Enable",
        "C": CLEAR_CACHE
    }

    CompressOption: Options.Boolean
    VendorsOption: Options.Boolean

    def __init__(self) -> None:
        self.CompressOption = Options.Boolean(
            "Compress Saves", (
                "Compress saves so that they take up less disk space. If you frequently save edit,"
                " you may want to turn this off to make doing so easier."
            ), True
        )
        self.VendorsOption = Options.Boolean(
            "Reroll Vendors on Level Transitions", (
                "Vendors containing unserializable items will get broken if you switch levels."
                " Turning this on rerolls vendors on transitions to preventing you from finding"
                " such items."
            ), False
        )
        self.Options = [self.CompressOption, self.VendorsOption]

    def Enable(self) -> None:
        cached_obj_find.cache_clear()
        update_compression(self.CompressOption.CurrentValue)
        update_vendor_rerolling(self.VendorsOption.CurrentValue)

        migrate_all()

        enable_console_commands()
        for func, hook in AllHooks.items():
            unrealsdk.RunHook(func, self.Name, hook)

    def Disable(self) -> None:
        disable_console_commands()
        for func in AllHooks.keys():
            unrealsdk.RemoveHook(func, self.Name)

    def SettingsInputPressed(self, action: str) -> None:
        if action == self.CLEAR_CACHE:
            cached_obj_find.cache_clear()
        else:
            super().SettingsInputPressed(action)

    def ModOptionChanged(self, option: Options.Base, new_value: Any) -> None:
        if option == self.CompressOption:
            update_compression(new_value)
        elif option == self.VendorsOption:
            update_vendor_rerolling(new_value)


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
