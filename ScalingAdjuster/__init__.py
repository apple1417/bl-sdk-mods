import bl2sdk
import json
from os import path
from sys import executable
from typing import Dict
from typing import List


class ScalingAdjuster(bl2sdk.BL2MOD):
    Name: str = "Scaling Adjuster"
    Author: str = "apple1417"
    Description: str = (
        "Adds an option to let you easily adjust the game's base scaling value.\n"
        "Note that you may have to save quit to get values to update."
    )
    Types: List[bl2sdk.ModTypes] = [bl2sdk.ModTypes.Utility]
    Version = "1.1"

    # Doing options a little weirdly so that the same file works for both games
    EXE_NAME: str = path.basename(executable)
    OPTIONS_PATH: str = path.join(path.dirname(path.realpath(__file__)), "options.json")
    OptionsDict: Dict[str, float] = {}

    def __init__(self) -> None:
        # Hopefully I can remove this in a future SDK update
        self.Author += "\nVersion: " + str(self.Version)

        self.scalingObject = bl2sdk.FindObject(
            "ConstantAttributeValueResolver",
            "GD_Balance_HealthAndDamage.HealthAndDamage.Att_UniversalBalanceScaler:ConstantAttributeValueResolver_0"
        )
        # Save this so that we can properly revert to default in both games
        self.DEFAULT_SCALING: float = self.scalingObject.ConstantValue
        # Sliders don't properly support floats so we'll multiply the value by 100
        self.scalingSlider: bl2sdk.Options.SliderOption = bl2sdk.Options.SliderOption(
            Description="The game's base scaling value (multiplied by 100). 113 means every level the numbers get 13% higher.",
            Caption="",
            StartingValue=self.DEFAULT_SCALING * 100,
            MinValue=0,
            MaxValue=500,
            Increment=1
        )

        if path.exists(self.OPTIONS_PATH):
            with open(self.OPTIONS_PATH) as file:
                self.OptionsDict = json.load(file)

    def Enable(self) -> None:
        self.RegisterGameConfigOption(self.scalingSlider)

        if self.EXE_NAME in self.OptionsDict:
            self.scalingObject.ConstantValue = self.OptionsDict[self.EXE_NAME]
            self.scalingSlider.CurrentValue = int(self.OptionsDict[self.EXE_NAME] * 100)

    def Disable(self) -> None:
        self.UnregisterGameConfigOption(self.scalingSlider)

        self.scalingObject.ConstantValue = self.DEFAULT_SCALING
        self.scalingSlider.CurrentValue = self.DEFAULT_SCALING * 100

    def ModOptionChanged(self, scalingSlider: bl2sdk.Options.SliderOption, newValue: int) -> None:
        if scalingSlider == self.scalingSlider:
            self.scalingObject.ConstantValue = newValue / 100
            self.OptionsDict[self.EXE_NAME] = newValue / 100

            with open(self.OPTIONS_PATH, "w") as file:
                json.dump(self.OptionsDict, file, indent=4)


instance = ScalingAdjuster()
if __name__ == "__main__":
    bl2sdk.Log("[Scaling Adjuster] Manually loaded")
    for mod in bl2sdk.Mods:
        if mod.Name == instance.Name:
            mod.Disable()
            bl2sdk.Mods.remove(mod)
            bl2sdk.Log("[Scaling Adjuster] Disabled and removed last instance")
            break
    else:
        bl2sdk.Log("[Scaling Adjuster] Could not find previous instance")
    bl2sdk.Log("[Scaling Adjuster] Auto-enabling")
    instance.Status = "Enabled"
    instance.SettingsInputs = {"Enter": "Disable"}
    instance.Enable()
bl2sdk.Mods.append(instance)
