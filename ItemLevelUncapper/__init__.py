import bl2sdk

class ItemLevelUncapper(bl2sdk.BL2MOD):
    Name = "Item Level Uncapper"
    Author = "apple1417"
    Description = (
        "Fixes that items stop spawning past level 100."
        "\nNote that some items may continue to spawn at higher levels after disabling this."
    )
    Types = [bl2sdk.ModTypes.Utility]

    # Multitool hex edit caps at 255 so this should be more than enough
    NEW_LEVEL = 1024
    """
      We need to force load all the vehicles because I don't have a proper hook for spawning one
      I could also force load every other object that we need to modify but:
       1. I do have a hook which runs on level load to fix them (though it also occasionally runs
           at other times)
       2. There are over 200 objects in BL2 alone, they'd really bloat this file even more
       3. It is slighly *less* unlikely for gearbox to add new items than vehicles, meaning there's
           less chance I have to hardcode more things
    """
    _FORCE_LOAD_BL2 = {
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
        ("InventoryBalanceDefinition", "GD_Orchid_HarpoonHovercraft.Weapon.ItemGrades.ItemGrade_Harpoon")
      ),
      "GD_Orchid_RocketHovercraft": (
        ("InventoryBalanceDefinition", "GD_Orchid_RocketHovercraft.Weapon.ItemGrades.ItemGrade_DualRockets")
      ),
      "GD_Orchid_SawHovercraft": (
        ("InventoryBalanceDefinition", "GD_Orchid_SawHovercraft.Weapon.ItemGrades.ItemGrade_SawBladeLauncher")
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
    _FORCE_LOAD_TPS = {
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
    FORCE_LOAD = None
    def __init__(self):
        self.FORCE_LOAD = self._FORCE_LOAD_BL2
        # Not the greatest way of checking game
        if bl2sdk.FindObject("ItemNamePartDefinition", "GD_Flax_Items.CandyParts.Prefix_Rock") == None:
            self.FORCE_LOAD = self._FORCE_LOAD_TPS

    # For all objects we can access on the menu
    menuObjects = set()

    def Enable(self):
        bl2sdk.RegisterHook("WillowGame.WillowHUD.CreateWeaponScopeMovie", "ILU-MapLoad", parseNewItems)

        # If you're re-enabling then we can exit right here, the rest of this is non-reversible
        if len(self.menuObjects) > 0:
            return

        # Objects we load here should still be alive for all the FindAll commands
        for package, objects in self.FORCE_LOAD.items():
            bl2sdk.LoadPackage(package)
            for obj in objects:
                 bl2sdk.KeepAlive(bl2sdk.FindObject(obj[0], obj[1]))

        # FindAll() doesn't cover subclasses
        for obj in bl2sdk.FindAll("ItemBalanceDefinition"):
            self.handleInvBalance(obj)
            self.menuObjects.add(obj)
        for obj in bl2sdk.FindAll("ClassModBalanceDefinition"):
            self.handleInvBalance(obj)
            self.menuObjects.add(obj)
        for obj in bl2sdk.FindAll("WeaponBalanceDefinition"):
            self.handleInvBalance(obj)
            self.menuObjects.add(obj)
        for obj in bl2sdk.FindAll("MissionWeaponBalanceDefinition"):
            self.handleInvBalance(obj)
            self.menuObjects.add(obj)

        for obj in bl2sdk.FindAll("ItemPartListCollectionDefinition"):
            self.handlePartListCollection(obj)
            self.menuObjects.add(obj)
        for obj in bl2sdk.FindAll("WeaponPartListCollectionDefinition"):
            self.handlePartListCollection(obj)
            self.menuObjects.add(obj)

        for obj in bl2sdk.FindAll("ItemPartListDefinition"):
            self.handleRawPartList(obj)
            self.menuObjects.add(obj)
        for obj in bl2sdk.FindAll("WeaponPartListDefinition"):
            self.handleRawPartList(obj)
            self.menuObjects.add(obj)

        for obj in bl2sdk.FindAll("WeaponNamePartDefinition"):
            self.handleNamePart(obj)
            self.menuObjects.add(obj)
        for obj in bl2sdk.FindAll("ItemNamePartDefinition"):
            self.handleNamePart(obj)
            self.menuObjects.add(obj)

    def Disable(self):
        bl2sdk.RemoveHook("WillowGame.WillowHUD.CreateWeaponScopeMovie", "ILU-MapLoad")

    # Takes an object and a set of it's CAID indexes which corospond to level
    # Usually this will only be one index but just in case we handle multiple
    def fixCAID(self, obj, indexes):
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

    def handleInvBalance(self, obj):
        if "WillowGame.Default__" in str(obj):
            return
        if not obj.Manufacturers:
            return
        for manu in obj.Manufacturers:
            for grade in manu.Grades:
                grade.GameStageRequirement.MaxGameStage = self.NEW_LEVEL

    # This function takes in both Item and WeaponPartListCollections, which are very similar, BUT
    #  store their parts in different fields
    def handlePartListCollection(self, obj):
        if "WillowGame.Default__" in str(obj):
            return
        itemType = str(obj).split(" ")[0]
        allParts = set()
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
            bl2sdk.Log(f"ILU: Unexpected class on {str(obj)}")
            return

        levelIndexes = set()
        for part in allParts:
            weighted = getattr(obj, part).WeightedParts
            if weighted != None:
                for wPart in weighted:
                    if wPart.MaxGameStageIndex:
                        levelIndexes.add(wPart.MaxGameStageIndex)
        self.fixCAID(obj, levelIndexes)

    # For ____PartListDefinitions rather than ____PartList*Collection*Definitions
    def handleRawPartList(self, obj):
        if "WillowGame.Default__" in str(obj):
            return
        levelIndexes = set()
        for wPart in obj.WeightedParts:
            if wPart.MaxGameStageIndex:
                levelIndexes.add(wPart.MaxGameStageIndex)
        self.fixCAID(obj, levelIndexes)

    def handleNamePart(self, obj):
        if "WillowGame.Default__" in str(obj):
            return
        obj.MaxExpLevelRequirement = self.NEW_LEVEL

def parseNewItems(caller: bl2sdk.UObject, function: bl2sdk.UFunction, params: bl2sdk.FStruct) -> bool:
    for obj in bl2sdk.FindAll("InventoryBalanceDefinition"):
        if obj not in instance.menuObjects:
            instance.handleInvBalance(obj)

    for obj in bl2sdk.FindAll("ItemPartListCollectionDefinition"):
        if obj not in instance.menuObjects:
            instance.handlePartListCollection(obj)
    for obj in bl2sdk.FindAll("WeaponPartListCollectionDefinition"):
        if obj not in instance.menuObjects:
            instance.handlePartListCollection(obj)

    for obj in bl2sdk.FindAll("ItemPartListDefinition"):
        if obj not in instance.menuObjects:
            instance.handleRawPartList(obj)
    for obj in bl2sdk.FindAll("WeaponPartListDefinition"):
        if obj not in instance.menuObjects:
            instance.handleRawPartList(obj)

    for obj in bl2sdk.FindAll("WeaponNamePartDefinition"):
        if obj not in instance.menuObjects:
            instance.handleNamePart(obj)
    for obj in bl2sdk.FindAll("ItemNamePartDefinition"):
        if obj not in instance.menuObjects:
            instance.handleNamePart(obj)
    return True

instance = ItemLevelUncapper()
bl2sdk.Mods.append(instance)
