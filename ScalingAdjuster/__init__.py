import unrealsdk
from typing import Any, cast

from Mods.ModMenu import EnabledSaveType, Game, Mods, ModTypes, Options, RegisterMod, SDKMod


class ScalingAdjuster(SDKMod):
    Name: str = "Scaling Adjuster"
    Author: str = "apple1417"
    Description: str = (
        "Adds an option to let you easily adjust the game's base scaling value.\n"
        "Note that you may have to save quit to get values to update."
    )
    Version: str = "1.7"

    Types: ModTypes = ModTypes.Utility
    SaveEnabledState: EnabledSaveType = EnabledSaveType.LoadOnMainMenu

    ScalingObject: unrealsdk.UObject
    ScalingSlider: Options.Slider

    def __init__(self) -> None:
        self.ScalingObject = unrealsdk.FindObject(
            "ConstantAttributeValueResolver",
            "GD_Balance_HealthAndDamage.HealthAndDamage.Att_UniversalBalanceScaler:ConstantAttributeValueResolver_0"
        )

        self.Options = [
            Options.Slider(
                Caption="BL2 Scaling",
                Description="The game's base scaling value (multiplied by 100). 113 means every level the numbers get 13% higher.",
                StartingValue=113,
                MinValue=0,
                MaxValue=500,
                Increment=1,
                IsHidden=Game.GetCurrent() != Game.BL2
            ),
            Options.Slider(
                Caption="TPS Scaling",
                Description="The game's base scaling value (multiplied by 100). 111 means every level the numbers get 11% higher.",
                StartingValue=111,
                MinValue=0,
                MaxValue=500,
                Increment=1,
                IsHidden=Game.GetCurrent() != Game.TPS
            ),
            Options.Slider(
                Caption="AoDK Scaling",
                Description="The game's base scaling value (multiplied by 113). 113 means every level the numbers get 13% higher.",
                StartingValue=113,
                MinValue=0,
                MaxValue=500,
                Increment=1,
                IsHidden=Game.GetCurrent() != Game.AoDK
            ),
        ]

        self.ScalingSlider = cast(Options.Slider, next(x for x in self.Options if not x.IsHidden))

    def Enable(self) -> None:
        self.ScalingObject.ConstantValue = self.ScalingSlider.CurrentValue / 100

    def Disable(self) -> None:
        self.ScalingObject.ConstantValue = self.ScalingSlider.StartingValue / 100

    def ModOptionChanged(self, option: Options.Base, new_value: Any) -> None:
        if option == self.ScalingSlider:
            self.ScalingObject.ConstantValue = new_value / 100


instance = ScalingAdjuster()
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
