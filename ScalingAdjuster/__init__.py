import unrealsdk
from typing import Any, cast, ClassVar, List

try:
    from Mods import AAA_OptionsWrapper as OptionsWrapper
except ImportError as ex:
    import webbrowser
    webbrowser.open("https://apple1417.github.io/bl2/didntread/?m=Scaling%20Adjuster&ow")
    raise ex


class ScalingAdjuster(unrealsdk.BL2MOD):
    Name: ClassVar[str] = "Scaling Adjuster"
    Author: ClassVar[str] = "apple1417"
    Description: ClassVar[str] = (
        "Adds an option to let you easily adjust the game's base scaling value.\n"
        "Note that you may have to save quit to get values to update."
    )
    Types: ClassVar[List[unrealsdk.ModTypes]] = [unrealsdk.ModTypes.Utility]
    Version: ClassVar[str] = "1.5"

    Options: List[OptionsWrapper.Base]

    IS_BL2: ClassVar[bool] = unrealsdk.GetEngine().GetEngineVersion() == 8639

    ScalingObject: unrealsdk.UObject
    ScalingSlider: OptionsWrapper.Slider

    def __init__(self) -> None:
        # Hopefully I can remove this in a future SDK update
        self.Author += "\nVersion: " + str(self.Version)  # type: ignore

        self.ScalingObject = unrealsdk.FindObject(
            "ConstantAttributeValueResolver",
            "GD_Balance_HealthAndDamage.HealthAndDamage.Att_UniversalBalanceScaler:ConstantAttributeValueResolver_0"
        )

        self.Options = [
            OptionsWrapper.Slider(
                Caption="BL2 Scaling",
                Description="The game's base scaling value (multiplied by 100). 113 means every level the numbers get 13% higher.",
                StartingValue=113,
                MinValue=0,
                MaxValue=500,
                Increment=1,
                IsHidden=not self.IS_BL2
            ),
            OptionsWrapper.Slider(
                Caption="TPS Scaling",
                Description="The game's base scaling value (multiplied by 100). 113 means every level the numbers get 13% higher.",
                StartingValue=111,
                MinValue=0,
                MaxValue=500,
                Increment=1,
                IsHidden=self.IS_BL2
            )
        ]

        self.ScalingSlider = cast(OptionsWrapper.Slider, self.Options[0 if self.IS_BL2 else 1])

    def Enable(self) -> None:
        self.ScalingObject.ConstantValue = self.ScalingSlider.CurrentValue / 100

    def Disable(self) -> None:
        self.ScalingObject.ConstantValue = self.ScalingSlider.StartingValue / 100

    def ModOptionChanged(
        self,
        option: OptionsWrapper.Base,
        newValue: Any
    ) -> None:
        if option == self.ScalingSlider:
            self.ScalingObject.ConstantValue = cast(int, newValue) / 100


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
