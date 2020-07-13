import unrealsdk
from typing import Any, ClassVar, List, Optional

try:
    from Mods import AAA_OptionsWrapper as OptionsWrapper
except ImportError as ex:
    import webbrowser
    webbrowser.open("https://apple1417.github.io/bl2/didntread/?m=Spawn%20Multiplier&ow")
    raise ex


class SpawnMultiplier(unrealsdk.BL2MOD):
    Name: ClassVar[str] = "Spawn Multiplier"
    Author: ClassVar[str] = "apple1417"
    Description: ClassVar[str] = (
        "Adds an option to let you easily multiply the amount of spawns you're getting.\n"
        "Make sure to go to settings to configure what the multiplier is."
    )
    Types: ClassVar[List[unrealsdk.ModTypes]] = [unrealsdk.ModTypes.Gameplay]
    Version: ClassVar[str] = "1.0"

    Options: List[OptionsWrapper.Base]

    MultiplierSlider: OptionsWrapper.Slider
    SpawnLimitSpinner: OptionsWrapper.Spinner
    OldMultiplier: int

    PlayerAllegiance: unrealsdk.UObject
    CurrentPopMaster: Optional[unrealsdk.UObject]
    OriginalLimit: Optional[int]

    def __init__(self) -> None:
        # Hopefully I can remove this in a future SDK update
        self.Author += "\nVersion: " + str(self.Version)  # type: ignore

        self.MultiplierSlider = OptionsWrapper.Slider(
            Caption="Multiplier",
            Description="The amount to multiply spawns by.",
            StartingValue=1,
            MinValue=1,
            MaxValue=25,
            Increment=1
        )
        self.SpawnLimitSpinner = OptionsWrapper.Spinner(
            Caption="Spawn Limit",
            Description=(
                "How to handle the spawn limit."
                " Standard: Don't change it;"
                " Linear: Increase linearly with the multiplier;"
                " Unlimited: Remove it."
            ),
            StartingChoice="Linear",
            Choices=("Standard", "Linear", "Unlimited"),
        )
        self.OldMultiplier = self.MultiplierSlider.CurrentValue

        self.Options = [self.MultiplierSlider, self.SpawnLimitSpinner]

        self.PlayerAllegiance = unrealsdk.FindObject(
            "PawnAllegiance",
            "GD_AI_Allegiance.Allegiance_Player"
        )

        self.CurrentPopMaster = None
        self.OriginalLimit = None

    def Enable(self) -> None:
        def SpawnPopulationControlledActor(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            if caller != self.CurrentPopMaster:
                self.CurrentPopMaster = caller
                self.OriginalLimit = caller.MaxActorCost

                if self.SpawnLimitSpinner.CurrentValue == "Linear":
                    caller.MaxActorCost *= self.MultiplierSlider.CurrentValue
                elif self.SpawnLimitSpinner.CurrentValue == "Unlimited":
                    caller.MaxActorCost = 0x7FFFFFFF

            return True

        def PostBeginPlay(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            caller.PostBeginPlay()
            caller.SpawnData.MaxActiveActors = caller.SpawnData.MaxActiveActors * self.MultiplierSlider.CurrentValue
            caller.MaxActiveActorsIsNormal = caller.MaxActiveActorsIsNormal * self.MultiplierSlider.CurrentValue
            caller.MaxActiveActorsThreatened = caller.MaxActiveActorsThreatened * self.MultiplierSlider.CurrentValue
            caller.MaxTotalActors = caller.MaxTotalActors * self.MultiplierSlider.CurrentValue
            return True

        self.OldMultiplier = self.MultiplierSlider.CurrentValue
        unrealsdk.RunHook("GearboxFramework.PopulationMaster.SpawnPopulationControlledActorn", self.Name, SpawnPopulationControlledActor)
        unrealsdk.RunHook("WillowGame.PopulationOpportunityDen.PostBeginPlay", self.Name, PostBeginPlay)

    def Disable(self) -> None:
        unrealsdk.RemoveHook("GearboxFramework.PopulationMaster.SpawnPopulationControlledActorn", self.Name)
        unrealsdk.RemoveHook("WillowGame.PopulationOpportunityDen.PostBeginPlay", self.Name)

    def ModOptionChanged(
        self,
        option: OptionsWrapper.Base,
        newValue: Any
    ) -> None:
        if option not in self.Options:
            return

        # Only need to redo these numbers when changing multiplier, always have to redo spawn limit
        if option == self.MultiplierSlider:
            # This function gets called after the value is changed grr
            multiplier = self.MultiplierSlider.CurrentValue / self.OldMultiplier
            self.OldMultiplier = self.MultiplierSlider.CurrentValue

            for den in unrealsdk.FindAll("PopulationOpportunityDen"):
                den.SpawnData.MaxActiveActors = int(den.SpawnData.MaxActiveActors * multiplier)
                den.MaxActiveActorsIsNormal = int(den.MaxActiveActorsIsNormal * multiplier)
                den.MaxActiveActorsThreatened = int(den.MaxActiveActorsThreatened * multiplier)
                den.MaxTotalActors = int(den.MaxTotalActors * multiplier)

        # Don't want to use `self.CurrentPopMaster` just in case it's been GCed
        popMaster = unrealsdk.FindAll("WillowPopulationMaster")[-1]
        if popMaster is None:
            return
        if popMaster != self.CurrentPopMaster:
            self.CurrentPopMaster = popMaster
            self.OriginalLimit = popMaster.MaxActorCost

        if self.SpawnLimitSpinner.CurrentValue == "Standard":
            popMaster.MaxActorCost = self.OriginalLimit
        elif self.SpawnLimitSpinner.CurrentValue == "Linear":
            popMaster.MaxActorCost = self.OriginalLimit * self.MultiplierSlider.CurrentValue
        elif self.SpawnLimitSpinner.CurrentValue == "Unlimited":
            popMaster.MaxActorCost = 0x7FFFFFFF


instance = SpawnMultiplier()
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
