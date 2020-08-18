import unrealsdk
from typing import Callable, ClassVar, Dict, Set, Tuple

from Mods.ModMenu import EnabledSaveType, Game, Mods, ModTypes, RegisterMod, SDKMod


class ItemLevelUncapper(SDKMod):
    Name: str = "Item Level Uncapper"
    Author: str = "apple1417"
    Description: str = (
        "Edits the level cap of most items so that they continue spawning past level 100.\n"
        "\n"
        "Note that some items may continue to spawn at higher levels after disabling this, you must"
        " restart the game to truely disable it."
    )
    Version: str = "1.3"

    Types: ModTypes = ModTypes.Utility
    SaveEnabledState: EnabledSaveType = EnabledSaveType.LoadOnMainMenu

    # Multitool hex edit caps at 255 so this should be more than enough
    NEW_LEVEL: ClassVar[int] = 1024

    """
      We need to force load all the vehicles because I don't have a proper hook for spawning one
      I could also force load every other object that we need to modify but:
       1. I do have a hook which runs on level load to fix them (though it also occasionally runs
           at other times)
       2. There are over 200 objects in BL2 alone, they'd really bloat this file even more
       3. It is slighly *less* unlikely for gearbox to add new items than vehicles, meaning there's
           less chance I have to hardcode more things
    """
    _FORCE_LOAD_BL2: Dict[str, Tuple[Tuple[str, str], ...]] = {
        "GD_Runner_Streaming_SF": (
            ("InventoryBalanceDefinition", "GD_Runner_Streaming.Weapon.ItemGrades.ItemGrade_FrontMachineGun"),
            ("InventoryBalanceDefinition", "GD_Runner_Streaming.Weapon.ItemGrades.ItemGrade_MachineGun"),
            ("InventoryBalanceDefinition", "GD_Runner_Streaming.Weapon.ItemGrades.ItemGrade_RocketLauncher"),
            ("WeaponPartListDefinition", "GD_Runner_Streaming.Parts.SightPartList_LightRunnerMG"),
            ("WeaponPartListDefinition", "GD_Runner_Streaming.Parts.SightPartList_RocketRunner"),
            ("WeaponPartListCollectionDefinition", "GD_Runner_Streaming.Parts.WeaponParts_LightRunnerMG"),
            ("WeaponPartListCollectionDefinition", "GD_Runner_Streaming.Parts.WeaponParts_RocketRunner")
        ),
        "GD_BTech_Streaming_SF": (
            ("InventoryBalanceDefinition", "GD_BTech_Streaming.Weapon.ItemGrades.ItemGrade_Catapult"),
            ("InventoryBalanceDefinition", "GD_BTech_Streaming.Weapon.ItemGrades.ItemGrade_FrontMachineGun"),
            ("InventoryBalanceDefinition", "GD_BTech_Streaming.Weapon.ItemGrades.ItemGrade_SawBladeLauncher")
        ),
        "GD_Orchid_HarpoonHovercraft_SF": (
            ("InventoryBalanceDefinition", "GD_Orchid_HarpoonHovercraft.Weapon.ItemGrades.ItemGrade_Harpoon"),
        ),
        "GD_Orchid_RocketHovercraft_SF": (
            ("InventoryBalanceDefinition", "GD_Orchid_RocketHovercraft.Weapon.ItemGrades.ItemGrade_DualRockets"),
        ),
        "GD_Orchid_SawHovercraft_SF": (
            ("InventoryBalanceDefinition", "GD_Orchid_SawHovercraft.Weapon.ItemGrades.ItemGrade_SawBladeLauncher"),
        ),
        "GD_Sage_ShockFanBoat_SF": (
            ("InventoryBalanceDefinition", "GD_Sage_ShockFanBoat.Weapons.ItemGrades.ItemGrade_StickyShock"),
            ("WeaponPartListDefinition", "GD_Sage_ShockFanBoat.Weapons.WeaponParts.SightPartList_StickyShock"),
            ("WeaponPartListCollectionDefinition", "GD_Sage_ShockFanBoat.Weapons.WeaponParts.WeaponParts_StickyShock")
        ),
        "GD_Sage_CorrosiveFanBoat_SF": (
            ("InventoryBalanceDefinition", "GD_Sage_CorrosiveFanBoat.Weapons.ItemGrades.ItemGrade_CorrosiveSpew"),
            ("WeaponPartListDefinition", "GD_Sage_CorrosiveFanBoat.Weapons.WeaponParts.SightPartList_CorrosiveSpew"),
            ("WeaponPartListCollectionDefinition", "GD_Sage_CorrosiveFanBoat.Weapons.WeaponParts.WeaponParts_CorrosiveSpew")
        ),
        "GD_Sage_IncendiaryFanBoat_SF": (
            ("InventoryBalanceDefinition", "GD_Sage_IncendiaryFanBoat.Weapons.ItemGrades.ItemGrade_Flamethrower"),
            ("InventoryBalanceDefinition", "GD_Sage_IncendiaryFanBoat.Weapons.ItemGrades.ItemGrade_IncendiaryMachineGun"),
            ("WeaponPartListDefinition", "GD_Sage_IncendiaryFanBoat.Weapons.WeaponParts.BarrelPartList_FlameThrower"),
            ("WeaponPartListDefinition", "GD_Sage_IncendiaryFanBoat.Weapons.WeaponParts.SightPartList_FlameThrower"),
            ("WeaponPartListDefinition", "GD_Sage_IncendiaryFanBoat.Weapons.WeaponParts.SightPartList_IncendiaryMachineGun"),
            ("WeaponPartListCollectionDefinition", "GD_Sage_IncendiaryFanBoat.Weapons.WeaponParts.WeaponParts_FlameThrower"),
            ("WeaponPartListCollectionDefinition", "GD_Sage_IncendiaryFanBoat.Weapons.WeaponParts.WeaponParts_IncendiaryMachineGun")
        )
    }

    _FORCE_LOAD_TPS: Dict[str, Tuple[Tuple[str, str], ...]] = {
        "GD_MoonBuggy_Streaming_SF": (
            ("InventoryBalanceDefinition", "GD_MoonBuggy_Streaming.Weapon.ItemGrades.ItemGrade_FrontMachineGun"),
            ("InventoryBalanceDefinition", "GD_MoonBuggy_Streaming.Weapon.ItemGrades.ItemGrade_LightLaser"),
            ("InventoryBalanceDefinition", "GD_MoonBuggy_Streaming.Weapon.ItemGrades.ItemGrade_MissilePod"),
            ("InventoryBalanceDefinition", "GD_MoonBuggy_Streaming.Weapon.ItemGrades.ItemGrade_MissilePod_AIOnly"),
            ("WeaponPartListDefinition", "GD_MoonBuggy_Streaming.Parts.SightPartList_LaserBuggy"),
            ("WeaponPartListCollectionDefinition", "GD_MoonBuggy_Streaming.Parts.WeaponParts_LaserBuggy")
        ),
        "GD_Co_Stingray_Streaming_SF": (
            ("InventoryBalanceDefinition", "GD_Co_StingRay_Streaming.Weapon.ItemGrades.ItemGrade_FlakBurst"),
            ("InventoryBalanceDefinition", "GD_Co_StingRay_Streaming.Weapon.ItemGrades.ItemGrade_Laser"),
            ("InventoryBalanceDefinition", "GD_Co_StingRay_Streaming.Weapon.ItemGrades.ItemGrade_Rocket"),
            ("WeaponPartListDefinition", "GD_Co_StingRay_Streaming.Parts.SightPartList_StingRay_Tether")
        )
    }

    FORCE_LOAD: Dict[str, Tuple[Tuple[str, str], ...]]
    CLASS_HANDLER_MAP: Dict[str, Callable[[unrealsdk.UObject], None]]

    """
      We store all objects that we can access on the menu so that we can save a decent amount of
       time by not trying to handle them again on map load.
      Unfortuantly this does assume you're on the main menu.
      If you manually import or exec it while in game it's possible that a dynamically loaded object
       gets flagged, and then doesn't get uncapped later on when it's unloaded + reloaded.
      Seeing as most people are just going to enable it in the mods menu this is probably fine.
    """
    MenuObjects: Set[unrealsdk.UObject] = set()

    def __init__(self) -> None:
        if Game.GetCurrent() == Game.BL2:
            self.FORCE_LOAD = self._FORCE_LOAD_BL2
        else:
            self.FORCE_LOAD = self._FORCE_LOAD_TPS

        # All classes we will be searching through and their handlers
        # Do this in here so we can actually get a proper reference to the functions
        self.CLASS_HANDLER_MAP = {
            "InventoryBalanceDefinition": self.HandleInvBalance,
            "ItemBalanceDefinition": self.HandleInvBalance,
            "ClassModBalanceDefinition": self.HandleInvBalance,
            "WeaponBalanceDefinition": self.HandleInvBalance,
            "MissionWeaponBalanceDefinition": self.HandleInvBalance,

            "ItemPartListCollectionDefinition": self.HandlePartListCollection,
            "WeaponPartListCollectionDefinition": self.HandlePartListCollection,

            "ItemPartListDefinition": self.HandleRawPartList,
            "WeaponPartListDefinition": self.HandleRawPartList,

            "ItemNamePartDefinition": self.HandleNamePart,
            "WeaponNamePartDefinition": self.HandleNamePart,

            "InteractiveObjectBalanceDefinition": self.HandleGradedObject,
            "VehicleBalanceDefinition": self.HandleGradedObject
        }

    def Enable(self) -> None:
        def WillowClientDisableLoadingMovie(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            for clas, handler in self.CLASS_HANDLER_MAP.items():
                for obj in unrealsdk.FindAll(clas):
                    if obj not in self.MenuObjects:
                        handler(obj)
            return True

        unrealsdk.RegisterHook("WillowGame.WillowPlayerController.WillowClientDisableLoadingMovie", self.Name, WillowClientDisableLoadingMovie)

        # If you're re-enabling then we can exit right here, the rest of this is non-reversible
        if len(self.MenuObjects) > 0:
            return

        # Objects we load here will still be alive for all the FindAll commands, we don't need to
        #  parse them yet
        for package, objects in self.FORCE_LOAD.items():
            unrealsdk.LoadPackage(package)
            for obj_name in objects:
                obj = unrealsdk.FindObject(obj_name[0], obj_name[1])
                if obj is None:
                    unrealsdk.Log(f"[{self.Name}] Unable to find object '{obj_name[1]}'")

                unrealsdk.KeepAlive(obj)

        # Do our inital parse over everything, saving what we can access
        for clas, handler in self.CLASS_HANDLER_MAP.items():
            for obj in unrealsdk.FindAll(clas):
                self.MenuObjects.add(obj)
                handler(obj)

    def Disable(self) -> None:
        unrealsdk.RemoveHook("WillowGame.WillowPlayerController.WillowClientDisableLoadingMovie", self.Name)

    # Takes an object and a set of it's CAID indexes which corospond to max level
    # Usually this will only be one index but just in case we handle multiple
    def FixCAID(self, obj: unrealsdk.UObject, indexes: Set[int]) -> None:
        if not obj.ConsolidatedAttributeInitData:
            return
        # I can't call len() on these arrays (for now), so I need to manually count it
        index = 0
        change_amount = 0
        for bvc in obj.ConsolidatedAttributeInitData:
            if index in indexes:
                # I don't really think anything uses a scale but just in case
                bvc.BaseValueConstant = self.NEW_LEVEL
                bvc.BaseValueScaleConstant = 1

                change_amount += 1
                if change_amount >= len(indexes):
                    return
            index += 1

    def HandleInvBalance(self, obj: unrealsdk.UObject) -> None:
        if "WillowGame.Default__" in str(obj):
            return
        if not obj.Manufacturers:
            return
        for manu in obj.Manufacturers:
            self.HandleGradedObject(manu)

    # This function takes in both Item and WeaponPartListCollections, which are very similar, BUT
    #  store their parts in different fields
    def HandlePartListCollection(self, obj: unrealsdk.UObject) -> None:
        if "WillowGame.Default__" in str(obj):
            return
        item_type = str(obj).split(" ")[0]
        all_parts: Set[str] = set()
        if item_type == "ItemPartListCollectionDefinition":
            all_parts = {
                "AlphaPartData", "BetaPartData", "GammaPartData", "DeltaPartData",
                "EpsilonPartData", "ZetaPartData", "EtaPartData", "ThetaPartData",
                "MaterialPartData"
            }
        elif item_type == "WeaponPartListCollectionDefinition":
            all_parts = {
                "BodyPartData", "GripPartData", "BarrelPartData", "SightPartData",
                "StockPartData", "ElementalPartData", "Accessory1PartData", "Accessory2PartData",
                "MaterialPartData"
            }
        else:
            unrealsdk.Log(f"[{self.Name}] Unexpected class '{item_type}' on '{obj.PathName(obj)}'")
            return

        level_indexes = set()
        for part in all_parts:
            weighted = getattr(obj, part).WeightedParts
            if weighted is not None:
                for weighted_part in weighted:
                    if weighted_part.MaxGameStageIndex:
                        level_indexes.add(weighted_part.MaxGameStageIndex)
        self.FixCAID(obj, level_indexes)

    # For ____PartListDefinitions rather than ____PartList*Collection*Definitions
    def HandleRawPartList(self, obj: unrealsdk.UObject) -> None:
        if "WillowGame.Default__" in str(obj):
            return
        level_indexes = set()
        for weighted_part in obj.WeightedParts:
            if weighted_part.MaxGameStageIndex:
                level_indexes.add(weighted_part.MaxGameStageIndex)
        self.FixCAID(obj, level_indexes)

    def HandleNamePart(self, obj: unrealsdk.UObject) -> None:
        if "WillowGame.Default__" in str(obj):
            return
        obj.MaxExpLevelRequirement = self.NEW_LEVEL

    def HandleGradedObject(self, obj: unrealsdk.UObject) -> None:
        for grade in obj.Grades:
            grade.GameStageRequirement.MaxGameStage = self.NEW_LEVEL


instance = ItemLevelUncapper()
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
