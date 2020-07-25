import unrealsdk
from enum import Enum, unique
from typing import Any, cast, ClassVar, List, Optional, Set

try:
    from Mods import AAA_OptionsWrapper as OptionsWrapper
except ImportError as ex:
    import webbrowser
    webbrowser.open("https://apple1417.github.io/bl2/didntread/?m=Spawn%20Multiplier&ow")
    raise ex


@unique
class SpawnLimitType(Enum):
    Standard: str = "Standard"
    Linear: str = "Linear"
    Unlimited: str = "Unlimited"

    def __eq__(self, o: object) -> bool:
        if isinstance(o, str):
            return bool(self.value == o)
        else:
            return super().__eq__(o)

    def __str__(self) -> str:
        return str(self.value)


class SpawnMultiplier(unrealsdk.BL2MOD):
    Name: ClassVar[str] = "Spawn Multiplier"
    Author: ClassVar[str] = "apple1417"
    Description: ClassVar[str] = (
        "Adds an option to let you easily multiply the amount of spawns you're getting.\n"
        "Make sure to go to settings to configure what the multiplier is."
    )
    Types: ClassVar[List[unrealsdk.ModTypes]] = [unrealsdk.ModTypes.Gameplay]
    Version: ClassVar[str] = "1.4"

    Options: List[OptionsWrapper.Base]

    MultiplierSlider: OptionsWrapper.Slider
    SpawnLimitSpinner: OptionsWrapper.Spinner
    OldMultiplier: int

    CurrentPopMaster: Optional[unrealsdk.UObject]
    OriginalLimit: Optional[int]

    Blacklist: ClassVar[Set[str]] = {
        "Grass_Cliffs_Combat.TheWorld:PersistentLevel.PopulationOpportunityDen_16",
        "Boss_Cliffs_CombatLoader.TheWorld:PersistentLevel.PopulationOpportunityDen_4",
        "Sage_RockForest_Combat.TheWorld:PersistentLevel.PopulationOpportunityDen_11",
        "Helios_Mission_Main.TheWorld:PersistentLevel.PopulationOpportunityDen_6",
    }

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
                f" {SpawnLimitType.Standard}: Don't change it;"
                f" {SpawnLimitType.Linear}: Increase linearly with the multiplier;"
                f" {SpawnLimitType.Unlimited}: Remove it."
            ),
            StartingChoice=SpawnLimitType.Linear.value,
            Choices=[t.value for t in SpawnLimitType],
        )
        self.OldMultiplier = self.MultiplierSlider.CurrentValue

        self.Options = [self.MultiplierSlider, self.SpawnLimitSpinner]

        self.CurrentPopMaster = None
        self.OriginalLimit = None

    def Enable(self) -> None:
        def UpdateOpportunityEnabledStates(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            # Seems to be -1 on map load - though I've never seen it get called at another time
            if params.nWave != -1:
                return True

            self.MultiplePopEncounterIfAble(caller, self.MultiplierSlider.CurrentValue)

            return True

        def SpawnPopulationControlledActor(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            if caller != self.CurrentPopMaster:
                self.CurrentPopMaster = caller
                self.OriginalLimit = caller.MaxActorCost

                if self.SpawnLimitSpinner.CurrentValue == SpawnLimitType.Linear:
                    caller.MaxActorCost *= self.MultiplierSlider.CurrentValue
                elif self.SpawnLimitSpinner.CurrentValue == SpawnLimitType.Unlimited:
                    caller.MaxActorCost = 0x7FFFFFFF

            return True

        def PostBeginPlay(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            unrealsdk.DoInjectedCallNext()
            caller.PostBeginPlay()

            self.MultiplyDenIfAble(caller, self.MultiplierSlider.CurrentValue)

            return False

        for den in unrealsdk.FindAll("PopulationOpportunityDen"):
            self.MultiplyDenIfAble(den, self.MultiplierSlider.CurrentValue)
        for encounter in unrealsdk.FindAll("PopulationEncounter"):
            self.MultiplePopEncounterIfAble(encounter, self.MultiplierSlider.CurrentValue)

        self.OldMultiplier = self.MultiplierSlider.CurrentValue

        unrealsdk.RunHook("GearboxFramework.PopulationEncounter.UpdateOpportunityEnabledStates", self.Name, UpdateOpportunityEnabledStates)
        unrealsdk.RunHook("GearboxFramework.PopulationMaster.SpawnPopulationControlledActor", self.Name, SpawnPopulationControlledActor)
        unrealsdk.RunHook("WillowGame.PopulationOpportunityDen.PostBeginPlay", self.Name, PostBeginPlay)

    def Disable(self) -> None:
        unrealsdk.RemoveHook("GearboxFramework.PopulationEncounter.UpdateOpportunityEnabledStates", self.Name)
        unrealsdk.RemoveHook("GearboxFramework.PopulationMaster.SpawnPopulationControlledActor", self.Name)
        unrealsdk.RemoveHook("WillowGame.PopulationOpportunityDen.PostBeginPlay", self.Name)

        for den in unrealsdk.FindAll("PopulationOpportunityDen"):
            self.MultiplyDenIfAble(den, 1 / self.MultiplierSlider.CurrentValue)
        for encounter in unrealsdk.FindAll("PopulationEncounter"):
            self.MultiplePopEncounterIfAble(encounter, 1 / self.MultiplierSlider.CurrentValue)

        # Being careful incase our reference has been GCed
        if unrealsdk.FindAll("WillowPopulationMaster")[-1] == self.CurrentPopMaster:
            self.CurrentPopMaster.MaxActorCost = self.OriginalLimit

    def ModOptionChanged(
        self,
        option: OptionsWrapper.Base,
        new_value: Any
    ) -> None:
        if option not in self.Options:
            return

        # Only need to redo these numbers when changing multiplier, always have to redo spawn limit
        if option == self.MultiplierSlider:
            new_value = cast(int, new_value)
            # This function gets called after the value is changed grr
            adjustment = new_value / self.OldMultiplier
            self.OldMultiplier = new_value

            for den in unrealsdk.FindAll("PopulationOpportunityDen"):
                self.MultiplyDenIfAble(den, adjustment)
            for encounter in unrealsdk.FindAll("PopulationEncounter"):
                self.MultiplePopEncounterIfAble(encounter, adjustment)

        # Again careful incase our reference has been GCed
        pop_master = unrealsdk.FindAll("WillowPopulationMaster")[-1]
        if pop_master is None:
            return
        if pop_master != self.CurrentPopMaster:
            self.CurrentPopMaster = pop_master
            self.OriginalLimit = pop_master.MaxActorCost

        # This doesn't matter right now, but in a future sdk version this function is called before
        #  the option is changed, so we need to make sure we have the new version
        spawn_limit = self.SpawnLimitSpinner.CurrentValue
        if option == self.SpawnLimitSpinner:
            spawn_limit = cast(str, new_value)

        if spawn_limit == SpawnLimitType.Standard:
            pop_master.MaxActorCost = self.OriginalLimit
        elif spawn_limit == SpawnLimitType.Linear:
            multiplier = self.MultiplierSlider.CurrentValue
            if option == self.MultiplierSlider:
                multiplier = cast(int, new_value)

            pop_master.MaxActorCost = round(self.OriginalLimit * multiplier)
        elif spawn_limit == SpawnLimitType.Unlimited:
            pop_master.MaxActorCost = 0x7FFFFFFF

    def CanDenBeMultiplied(self, den: unrealsdk.UObject) -> bool:
        if den is None or den.PathName(den) in self.Blacklist:
            return False
        pop_def = den.PopulationDef
        if pop_def is None:
            return False
        count = 0
        for actor in pop_def.ActorArchetypeList:
            factory = actor.SpawnFactory
            if factory is None:
                return False
            if factory.Class.Name in (
                "PopulationFactoryBlackMarket",
                "PopulationFactoryInteractiveObject",
                "PopulationFactoryVendingMachine"
            ):
                return False
            count += 1
        if count == 0:
            return False

        return True

    def MultiplyDenIfAble(self, den: unrealsdk.UObject, amount: float) -> None:
        if self.CanDenBeMultiplied(den):
            den.SpawnData.MaxActiveActors = round(den.SpawnData.MaxActiveActors * amount)
            den.MaxActiveActorsIsNormal = round(den.MaxActiveActorsIsNormal * amount)
            den.MaxActiveActorsThreatened = round(den.MaxActiveActorsThreatened * amount)
            den.MaxTotalActors = round(den.MaxTotalActors * amount)

    def MultiplePopEncounterIfAble(self, encounter: unrealsdk.UObject, amount: float) -> None:
        if encounter is None or encounter.PathName(encounter) in self.Blacklist:
            return

        for wave in encounter.Waves:
            for den in wave.MemberOpportunities:
                if not self.CanDenBeMultiplied(den):
                    break
            else:
                if wave.SpawnLimits is None:
                    continue

                for limit in wave.SpawnLimits:
                    limit.MaxTotalToSpawn.BaseValueScaleConstant = round(limit.MaxTotalToSpawn.BaseValueScaleConstant * amount)
                    limit.MaxActiveAtATime.BaseValueScaleConstant = round(limit.MaxActiveAtATime.BaseValueScaleConstant * amount)


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
