import bl2sdk

class ItemLevelUncapper(bl2sdk.BL2MOD):
    Name = "Item Level Uncapper"
    Author = "apple1417"
    Description = (
        "Fixes the level cap of most items so that they continue spawning past level 100."
        "\nNote that some items may continue to spawn at higher levels after disabling this."
    )
    Types = [bl2sdk.ModTypes.Utility]
    Version = "1.1"

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
    CLASS_HANDLER_MAP = None
    def __init__(self):
        self.FORCE_LOAD = self._FORCE_LOAD_BL2
        # Not the greatest way of checking game
        if bl2sdk.FindObject("ItemNamePartDefinition", "GD_Flax_Items.CandyParts.Prefix_Rock") == None:
            self.FORCE_LOAD = self._FORCE_LOAD_TPS
        
        # All classes we will be searching through and their handlers
        # Do this in here so we can actually get a proper refrence to the functions
        self.CLASS_HANDLER_MAP = {
            "ClassModBalanceDefinition":            self.handleInvBalance,
            "ItemBalanceDefinition":                self.handleInvBalance,
            "MissionWeaponBalanceDefinition":       self.handleInvBalance,
            "WeaponBalanceDefinition":              self.handleInvBalance,
            
            "ItemPartListCollectionDefinition":     self.handlePartListCollection,
            "WeaponPartListCollectionDefinition":   self.handlePartListCollection,
            
            "ItemPartListDefinition":               self.handleRawPartList,
            "WeaponPartListDefinition":             self.handleRawPartList,
            
            "ItemNamePartDefinition":               self.handleNamePart,
            "WeaponNamePartDefinition":             self.handleNamePart
        }
    
        # Hopefully I can remove this in a future SDK update
        self.Author += "\nVersion: " + str(self.Version)
    
    """
      We store all objects that we can access on the menu so that we can save a decent amount of
       time by not trying to handle them again on map load
      Unfortuantly this does assume you're on the main menu
      If you manually import or exec it while in game it's possible that a dynamically loaded object
       gets flagged, and then doesn't get uncapped later on when it's unloaded + reloaded
      Seeing as most people are just going to enable it in the mods menu this is probably fine
    """
    menuObjects = set()
    
    def Enable(self):
        bl2sdk.RegisterHook("WillowGame.WillowHUD.CreateWeaponScopeMovie", "ILU-MapLoad", parseNewItems)
        
        # If you're re-enabling then we can exit right here, the rest of this is non-reversible
        if len(self.menuObjects) > 0:
            return
        
        # Objects we load here will still be alive for all the FindAll commands, we don't need to
        #  parse them yet
        for package, objects in self.FORCE_LOAD.items():
            bl2sdk.LoadPackage(package)
            for obj in objects:
                 bl2sdk.KeepAlive(bl2sdk.FindObject(obj[0], obj[1]))
        
        # Do our inital parse over everything, saving what we can access
        for clas, handler in self.CLASS_HANDLER_MAP.items():
            for obj in bl2sdk.FindAll(clas):
                self.menuObjects.add(obj)
                handler(obj)
    
    def Disable(self):
        bl2sdk.RemoveHook("WillowGame.WillowHUD.CreateWeaponScopeMovie", "ILU-MapLoad")
    
    def parseNewItems(self):
        for clas, handler in self.CLASS_HANDLER_MAP.items():
            for obj in bl2sdk.FindAll(clas):
                if obj not in self.menuObjects:
                    handler(obj)
    
    # Takes an object and a set of it's CAID indexes which corospond to max level
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
            bl2sdk.Log(f"[ILU] Unexpected class on {str(obj)}")
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
    instance.parseNewItems()
    return True

instance = ItemLevelUncapper()
if __name__ == "__main__":
    bl2sdk.Log("[ILU] Manually loaded")
    for mod in bl2sdk.Mods:
        if mod.Name == instance.Name:
            mod.Disable()
            bl2sdk.Mods.remove(mod)
            bl2sdk.Log("[ILU] Disabled and removed last instance")
            break
    else:
        bl2sdk.Log("[ILU] Could not find previous instance")
    
    bl2sdk.Log("[ILU] Auto-enabling")
    instance.Status = "Enabled"
    instance.SettingsInputs = {"Enter": "Disable"}
    instance.Enable()
bl2sdk.Mods.append(instance)
