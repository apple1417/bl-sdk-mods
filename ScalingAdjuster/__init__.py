import unrealsdk
from typing import ClassVar, List, Union


class ScalingAdjuster(unrealsdk.BL2MOD):
    Name: ClassVar[str] = "Scaling Adjuster"
    Author: ClassVar[str] = "apple1417"
    Description: ClassVar[str] = (
        "Adds an option to let you easily adjust the game's base scaling value.\n"
        "Note that you may have to save quit to get values to update."
    )
    Types: ClassVar[List[unrealsdk.ModTypes]] = [unrealsdk.ModTypes.Utility]
    Version: ClassVar[str] = "1.2"

    Options: List[Union[unrealsdk.Options.Slider, unrealsdk.Options.Spinner, unrealsdk.Options.Boolean, unrealsdk.Options.Hidden]]

    IS_BL2: ClassVar[bool] = unrealsdk.GetEngine().GetEngineVersion() == 8639

    ScalingObject: unrealsdk.UObject
    ScalingSlider: unrealsdk.Options.Slider
    DEFAULT_SCALING: float

    def __init__(self) -> None:
        # Hopefully I can remove this in a future SDK update
        self.Author += "\nVersion: " + str(self.Version)  # type: ignore

        self.ScalingObject = unrealsdk.FindObject(
            "ConstantAttributeValueResolver",
            "GD_Balance_HealthAndDamage.HealthAndDamage.Att_UniversalBalanceScaler:ConstantAttributeValueResolver_0"
        )

        # Sliders don't properly support floats so we'll multiply the value by 100
        shownCaption = "BL2 Scaling"
        shownValue = 113.0
        hiddenCaption = "TPS Scaling"
        hiddenValue = 111.0
        if not self.IS_BL2:
            shownCaption, hiddenCaption = hiddenCaption, shownCaption
            shownValue, hiddenValue = hiddenValue, shownValue

        self.DEFAULT_SCALING = shownValue
        self.ScalingSlider = unrealsdk.Options.Slider(
            Description="The game's base scaling value (multiplied by 100). 113 means every level the numbers get 13% higher.",
            Caption=shownCaption,
            StartingValue=shownValue,
            MinValue=0,
            MaxValue=500,
            Increment=1
        )
        hiddenOption = unrealsdk.Options.Hidden(
            valueName=hiddenCaption,
            StartingValue=hiddenValue
        )

        self.Options = []
        if self.IS_BL2:
            self.Options.append(self.ScalingSlider)
            self.Options.append(hiddenOption)
        else:
            self.Options.append(hiddenOption)
            self.Options.append(self.ScalingSlider)

    def Enable(self) -> None:
        self.ScalingObject.ConstantValue = self.ScalingSlider.CurrentValue

    def Disable(self) -> None:
        self.ScalingObject.ConstantValue = self.DEFAULT_SCALING

    def ModOptionChanged(
        self,
        option: Union[unrealsdk.Options.Slider, unrealsdk.Options.Spinner, unrealsdk.Options.Boolean, unrealsdk.Options.Hidden],
        newValue: int
    ) -> None:
        if option == self.ScalingSlider:
            self.ScalingObject.ConstantValue = newValue / 100


instance = ScalingAdjuster()
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
