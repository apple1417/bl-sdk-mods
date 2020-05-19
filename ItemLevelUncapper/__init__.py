import unrealsdk
from typing import Callable, ClassVar, Dict, List, Set, Tuple


class ItemLevelUncapper(unrealsdk.BL2MOD):
    Name: ClassVar[str] = "Item Level Uncapper"
    Author: ClassVar[str] = "apple1417"
    Description: ClassVar[str] = (
        "Fixes the level cap of most items so that they continue spawning past level 100."
        "\nNote that some items may continue to spawn at higher levels after disabling this."
    )
    Types: ClassVar[List[unrealsdk.ModTypes]] = [unrealsdk.ModTypes.Utility]
    Version: ClassVar[str] = "1.2"

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
        "GD_Runner_Streaming": (
            ("InventoryBalanceDefinition", "GD_Runner_Streaming.Weapon.ItemGrades.ItemGrade_FrontMachineGun"),
            ("InventoryBalanceDefinition", "GD_Runner_Streaming.Weapon.ItemGrades.ItemGrade_MachineGun"),
            ("InventoryBalanceDefinition", "GD_Runner_Streaming.Weapon.ItemGrades.ItemGrade_RocketLauncher"),
            ("WeaponPartListDefinition", "GD_Runner_Streaming.Parts.SightPartList_LightRunnerMG"),
            ("WeaponPartListDefinition", "GD_Runner_Streaming.Parts.SightPartList_RocketRunner"),
            ("WeaponPartListCollectionDefinition", "GD_Runner_Streaming.Parts.WeaponParts_LightRunnerMG"),
            ("WeaponPartListCollectionDefinition", "GD_Runner_Streaming.Parts.WeaponParts_RocketRunner")
        ),
        "GD_BTech_Streaming": (
            ("InventoryBalanceDefinition", "GD_BTech_Streaming.Weapon.ItemGrades.ItemGrade_Catapult"),
            ("InventoryBalanceDefinition", "GD_BTech_Streaming.Weapon.ItemGrades.ItemGrade_FrontMachineGun"),
            ("InventoryBalanceDefinition", "GD_BTech_Streaming.Weapon.ItemGrades.ItemGrade_SawBladeLauncher")
        ),
        "GD_Orchid_HarpoonHovercraft": (
            ("InventoryBalanceDefinition", "GD_Orchid_HarpoonHovercraft.Weapon.ItemGrades.ItemGrade_Harpoon"),
        ),
        "GD_Orchid_RocketHovercraft": (
            ("InventoryBalanceDefinition", "GD_Orchid_RocketHovercraft.Weapon.ItemGrades.ItemGrade_DualRockets"),
        ),
        "GD_Orchid_SawHovercraft": (
            ("InventoryBalanceDefinition", "GD_Orchid_SawHovercraft.Weapon.ItemGrades.ItemGrade_SawBladeLauncher"),
        ),
        "GD_Sage_ShockFanBoat": (
            ("InventoryBalanceDefinition", "GD_Sage_ShockFanBoat.Weapons.ItemGrades.ItemGrade_StickyShock"),
            ("WeaponPartListDefinition", "GD_Sage_ShockFanBoat.Weapons.WeaponParts.SightPartList_StickyShock"),
            ("WeaponPartListCollectionDefinition", "GD_Sage_ShockFanBoat.Weapons.WeaponParts.WeaponParts_StickyShock")
        ),
        "GD_Sage_CorrosiveFanBoat": (
            ("InventoryBalanceDefinition", "GD_Sage_CorrosiveFanBoat.Weapons.ItemGrades.ItemGrade_CorrosiveSpew"),
            ("WeaponPartListDefinition", "GD_Sage_CorrosiveFanBoat.Weapons.WeaponParts.SightPartList_CorrosiveSpew"),
            ("WeaponPartListCollectionDefinition", "GD_Sage_CorrosiveFanBoat.Weapons.WeaponParts.WeaponParts_CorrosiveSpew")
        ),
        "GD_Sage_IncendiaryFanBoat": (
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
        "GD_MoonBuggy_Streaming": (
            ("InventoryBalanceDefinition", "GD_MoonBuggy_Streaming.Weapon.ItemGrades.ItemGrade_FrontMachineGun"),
            ("InventoryBalanceDefinition", "GD_MoonBuggy_Streaming.Weapon.ItemGrades.ItemGrade_LightLaser"),
            ("InventoryBalanceDefinition", "GD_MoonBuggy_Streaming.Weapon.ItemGrades.ItemGrade_MissilePod"),
            ("InventoryBalanceDefinition", "GD_MoonBuggy_Streaming.Weapon.ItemGrades.ItemGrade_MissilePod_AIOnly"),
            ("WeaponPartListDefinition", "GD_MoonBuggy_Streaming.Parts.SightPartList_LaserBuggy"),
            ("WeaponPartListCollectionDefinition", "GD_MoonBuggy_Streaming.Parts.WeaponParts_LaserBuggy")
        ),
        "GD_Co_Stingray_Streaming": (
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
       time by not trying to handle them again on map load
      Unfortuantly this does assume you're on the main menu
      If you manually import or exec it while in game it's possible that a dynamically loaded object
       gets flagged, and then doesn't get uncapped later on when it's unloaded + reloaded
      Seeing as most people are just going to enable it in the mods menu this is probably fine
    """
    MenuObjects: Set[unrealsdk.UObject] = set()

    def __init__(self) -> None:
        # Hopefully I can remove this in a future SDK update
        self.Author += "\nVersion: " + str(self.Version)  # type: ignore

        if unrealsdk.GetEngine().GetEngineVersion() == 8639:
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
        def CreateWeaponScopeMovie(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            for clas, handler in self.CLASS_HANDLER_MAP.items():
                for obj in unrealsdk.FindAll(clas):
                    if obj not in self.MenuObjects:
                        handler(obj)
            return True

        unrealsdk.RegisterHook("WillowGame.WillowHUD.CreateWeaponScopeMovie", "ItemLevelUncapper", CreateWeaponScopeMovie)

        # If you're re-enabling then we can exit right here, the rest of this is non-reversible
        if len(self.MenuObjects) > 0:
            return

        # Objects we load here will still be alive for all the FindAll commands, we don't need to
        #  parse them yet
        for package, objects in self.FORCE_LOAD.items():
            unrealsdk.LoadPackage(package)
            for obj in objects:
                unrealsdk.KeepAlive(unrealsdk.FindObject(obj[0], obj[1]))

        # Do our inital parse over everything, saving what we can access
        for clas, handler in self.CLASS_HANDLER_MAP.items():
            for obj in unrealsdk.FindAll(clas):
                self.MenuObjects.add(obj)
                handler(obj)

    def Disable(self) -> None:
        unrealsdk.RemoveHook("WillowGame.WillowHUD.CreateWeaponScopeMovie", "ItemLevelUncapper")

    # Takes an object and a set of it's CAID indexes which corospond to max level
    # Usually this will only be one index but just in case we handle multiple
    def FixCAID(self, obj: unrealsdk.UObject, indexes: Set[int]) -> None:
        if not obj.ConsolidatedAttributeInitData:
            return
        # I can't call len() on these arrays (for now), so I need to manually count it
        index = 0
        changeAmount = 0
        for BVC in obj.ConsolidatedAttributeInitData:
            if index in indexes:
                # I don't really think anything uses a scale but just in case
                BVC.BaseValueConstant = self.NEW_LEVEL
                BVC.BaseValueScaleConstant = 1

                changeAmount += 1
                if changeAmount >= len(indexes):
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
        itemType = str(obj).split(" ")[0]
        allParts: Set[str] = set()
        if itemType == "ItemPartListCollectionDefinition":
            allParts = {
                "AlphaPartData", "BetaPartData", "GammaPartData", "DeltaPartData",
                "EpsilonPartData", "ZetaPartData", "EtaPartData", "ThetaPartData",
                "MaterialPartData"
            }
        elif itemType == "WeaponPartListCollectionDefinition":
            allParts = {
                "BodyPartData", "GripPartData", "BarrelPartData", "SightPartData",
                "StockPartData", "ElementalPartData", "Accessory1PartData", "Accessory2PartData",
                "MaterialPartData"
            }
        else:
            unrealsdk.Log(f"[ILU] Unexpected class on {str(obj)}")
            return

        levelIndexes = set()
        for part in allParts:
            weighted = getattr(obj, part).WeightedParts
            if weighted is not None:
                for wPart in weighted:
                    if wPart.MaxGameStageIndex:
                        levelIndexes.add(wPart.MaxGameStageIndex)
        self.FixCAID(obj, levelIndexes)

    # For ____PartListDefinitions rather than ____PartList*Collection*Definitions
    def HandleRawPartList(self, obj: unrealsdk.UObject) -> None:
        if "WillowGame.Default__" in str(obj):
            return
        levelIndexes = set()
        for wPart in obj.WeightedParts:
            if wPart.MaxGameStageIndex:
                levelIndexes.add(wPart.MaxGameStageIndex)
        self.FixCAID(obj, levelIndexes)

    def HandleNamePart(self, obj: unrealsdk.UObject) -> None:
        if "WillowGame.Default__" in str(obj):
            return
        obj.MaxExpLevelRequirement = self.NEW_LEVEL

    def HandleGradedObject(self, obj: unrealsdk.UObject) -> None:
        for grade in obj.Grades:
            grade.GameStageRequirement.MaxGameStage = self.NEW_LEVEL


instance = ItemLevelUncapper()
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
