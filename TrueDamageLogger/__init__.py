import bl2sdk
import json
from os import path
from typing import ClassVar, List, Union

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
    bl2sdk.Log(f"[TDL] File path: {__file__}")


class TrueDamageLogger(bl2sdk.BL2MOD):
    Name: ClassVar[str] = "True Damage Logger"
    Author: ClassVar[str] = "apple1417"
    Description: ClassVar[str] = (
        "Prints the actual amount of damage you deal to console, bypassing visual damage cap."
    )
    Types: ClassVar[List[bl2sdk.ModTypes]] = [bl2sdk.ModTypes.Utility]
    Version: ClassVar[str] = "1.0"

    SETTINGS_PATH: ClassVar[str] = path.join(path.dirname(path.realpath(__file__)), "settings.json")

    MinZeros: int
    MinDamageSlider: bl2sdk.Options.SliderOption

    def __init__(self) -> None:
        # Hopefully I can remove this in a future SDK update
        self.Author += "\nVersion: " + str(self.Version)  # type: ignore

        try:
            with open(self.SETTINGS_PATH) as file:
                self.MinZeros = json.load(file)["MinZeros"]
        except OSError:
            self.MinZeros = 6

        self.MinDamageSlider = bl2sdk.Options.SliderOption(
            Description="The minimum amount of zeros a damage number has to have before it is logged to console.",
            Caption="Minimum Zeros",
            StartingValue=self.MinZeros,
            MinValue=0,
            MaxValue=40,
            Increment=1
        )

    def Enable(self) -> None:
        def TakeDamage(caller: bl2sdk.UObject, function: bl2sdk.UFunction, params: bl2sdk.FStruct) -> bool:
            PC = bl2sdk.GetEngine().GamePlayers[0].Actor

            if params.InstigatedBy != PC:
                return True

            if params.Damage < 10**self.MinZeros:
                return True

            name = caller.PathName(caller)
            if caller.AIClass is not None and caller.AIClass.DefaultDisplayName is not None:
                name = caller.AIClass.DefaultDisplayName

            if caller.BalanceDefinitionState.BalanceDefinition is not None:
                ptNum = PC.GetCurrentPlaythrough() + 1
                for pt in caller.BalanceDefinitionState.BalanceDefinition.PlayThroughs:
                    if pt.PlayThrough > ptNum:
                        continue
                    if pt.DisplayName is None or len(pt.DisplayName) == 0:
                        continue
                    name = pt.DisplayName

            bl2sdk.Log(f"Dealt {params.Damage} damage to level {caller.GetExpLevel()} {name}")

            return True

        self.RegisterGameConfigOption(self.MinDamageSlider)
        bl2sdk.RegisterHook("WillowGame.WillowPawn.TakeDamage", "TrueDamageLogger", TakeDamage)

    def Disable(self) -> None:
        self.UnregisterGameConfigOption(self.MinDamageSlider)
        bl2sdk.RemoveHook("WillowGame.WillowPawn.TakeDamage", "TrueDamageLogger")

    def ModOptionChanged(
        self,
        # Why can't these have a single base class
        option: Union[bl2sdk.Options.SliderOption, bl2sdk.Options.SpinnerOption, bl2sdk.Options.BooleanOption],
        newValue: int
    ) -> None:

        if option != self.MinDamageSlider:
            return

        self.MinZeros = int(newValue)

        with open(self.SETTINGS_PATH, "w") as file:
            json.dump({"MinZeros": self.MinZeros}, file, indent=4)


instance = TrueDamageLogger()
if __name__ == "__main__":
    bl2sdk.Log("[TDL] Manually loaded")
    for mod in bl2sdk.Mods:
        if mod.Name == instance.Name:
            mod.Disable()
            bl2sdk.Mods.remove(mod)
            bl2sdk.Log("[TDL] Disabled and removed last instance")
            break
    else:
        bl2sdk.Log("[TDL] Could not find previous instance")
    bl2sdk.Log("[TDL] Auto-enabling")
    instance.Status = "Enabled"
    instance.SettingsInputs = {"Enter": "Disable"}
    instance.Enable()
bl2sdk.Mods.append(instance)
