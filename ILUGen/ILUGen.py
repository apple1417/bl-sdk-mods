import bl2sdk
from BLCMMFile import *

IS_BL2 = True
HOTFIX_NAME = "ItemLevelUncapper"
MIN_ACCEPTABLE_LEVEL = 520

BLACKLIST = {
    "InventoryBalanceDefinition WillowGame.Default__InventoryBalanceDefinition",
    "ItemPartListCollectionDefinition WillowGame.Default__ItemPartListCollectionDefinition",
    "ItemPartListCollectionDefinition WillowGame.Default__ItemBalanceDefinition.PartList",
    "ItemPartListCollectionDefinition WillowGame.Default__ClassModBalanceDefinition.PartList"
}

# Setup Mod File
mod = ModFile("Item Level Uncapper", IS_BL2)
mod.addChild(Comment("By apple1417"))
mod.addChild(Comment("This mod is useless by itself, it should be used alongside the hexedit to increase the player level cap"))
mod.addChild(Comment("Fixes the level cap of most items so that they continue spawning past level 100"))
mod.addChild(Comment("Note that items past level 127 will overflow upon save-quit, and that gibbed won't let you create items"))
mod.addChild(Comment(" past 127, so past that point you'll have to pick up everything you use within the same session."))
mod.addChild(Comment("Also note that there may still be various other issues with an increased level cap, this only fixes that"))
mod.addChild(Comment(" most items stopped spawning"))

guns = Category("Guns")
shields = Category("Shields")
grenades = Category("Grenade Mods")
classMods = Category("Class Mods")
relics = Category("Relics" if IS_BL2 else "Oz Kits")
skins = Category("Skins/Heads")
names = Category("Names/Prefixes")
misc = Category("Misc")

mod.addChild(guns)
mod.addChild(shields)
mod.addChild(grenades)
mod.addChild(classMods)
mod.addChild(relics)
mod.addChild(skins)
mod.addChild(names)
mod.addChild(misc)

modified = set()

def parseBVCTuple(tuple):
    output = f"(BaseValueConstant={str(tuple.BaseValueConstant)},"
    output += f"BaseValueAttribute={str(tuple.BaseValueAttribute)},"
    output += f"InitializationDefinition={str(tuple.InitializationDefinition)},"
    output += f"BaseValueScaleConstant={str(tuple.BaseValueScaleConstant)})"
    return output

def toFullName(item):
    itemClass = str(item).split(" ")[0]
    name = item.name
    item = item.outer
    if item.name.startswith("PartList") or item.name.startswith("WeaponPartListCollectionDefinition"):
        name = item.name + ":" + name
        item = item.outer
    while item != None:
        name = item.name + "." + name
        item = item.outer
    return f"{itemClass}'{name}'"

def placeCommand(com):
    itemType = com.object.split("'")[0]
    itemName = com.object.split("'")[1]
    if itemType == "WeaponTypeDefinition" or itemType == "WeaponPartListCollectionDefinition":
        guns.addChild(com)
    elif itemType == "ShieldDefinition":
        shields.addChild(com)
    elif itemType == "GrenadeModDefinition":
        grenades.addChild(com)
    elif itemType == "ClassModDefinition":
        classMods.addChild(com)
    elif itemType == "ArtifactDefinition":
        relics.addChild(com)
    elif itemType == "UsableCustomizationItemDefinition":
        skins.addChild(com)
    else:
        if "Shield" in itemName:
            shields.addChild(com)
        elif "GrenadeMod" in itemName:
            grenades.addChild(com)
        elif "ClassMod" in itemName:
            classMods.addChild(com)
        elif "Artifact" in itemName:
            relics.addChild(com)
        elif "Head" in itemName or "Skin" in itemName:
            skins.addChild(com)
        elif ("A_Weapons" in itemName or "AssaultRifle" in itemName or "Launcher" in itemName or
            "Pistol" in itemName or "SMG" in itemName or "Shotgun" in itemName or
            "SniperRifle" in itemName) and not "CustomItems" in itemName and not "ItemGrades" in itemName:
            guns.addChild(com)
        else:
            misc.addChild(com)

for item in bl2sdk.FindAll("InventoryBalanceDefinition"):
    if str(item) in BLACKLIST or str(item) in modified:
        continue
    if not item.Manufacturers:
        continue
    for manu in item.Manufacturers:
        for grade in manu.Grades:
            if grade.GameStageRequirement.MaxGameStage < MIN_ACCEPTABLE_LEVEL:
                modified.add(str(item))
                grade.GameStageRequirement.MaxGameStage = MIN_ACCEPTABLE_LEVEL
    if not str(item) in modified:
        continue
    # Reconstruct the Manufacturers array as a string
    newValue = "("
    for manu in item.Manufacturers:
        newValue += f"(Manufacturer={toFullName(manu.Manufacturer)},Grades=("
        for grade in manu.Grades:
            newValue +=  "(GradeModifiers=("
            newValue += f"ExpLevel={str(grade.GradeModifiers.ExpLevel)},"
            newValue += f"CustomInventoryDefinition={str(grade.GradeModifiers.CustomInventoryDefinition)}"
            newValue +=  "),GameStageRequirement=("
            newValue += f"MinGameStage={str(grade.GameStageRequirement.MinGameStage)},"
            newValue += f"MaxGameStage={str(grade.GameStageRequirement.MaxGameStage)}"
            newValue +=  "),"
            newValue += f"MinSpawnProbabilityModifier={parseBVCTuple(grade.MinSpawnProbabilityModifier)}"
            newValue += ","
            newValue += f"MaxSpawnProbabilityModifier={parseBVCTuple(grade.MaxSpawnProbabilityModifier)}"
            newValue +=  "),"
        newValue = newValue[:-1] + ")),"
    placeCommand(Command(
        toFullName(item),
        "Manufacturers",
        newValue[:-1] + ")"
    ))

def fixCAID(item, indexes):
    if not item.ConsolidatedAttributeInitData:
        return
    # I can't call len() on these arrays meaning I need to manually count it :(
    index = 0
    # Also going to reconstruct it as a string as we go
    newValue = "("
    for BVC in item.ConsolidatedAttributeInitData:
        if index in indexes:
            # Nothing we care about uses BVA/ID but just to be sure
            if BVC.BaseValueAttribute != None or BVC.InitializationDefinition != None:
                bl2sdk.Log("BVA or ID was set in CAID")
                bl2sdk.Log("BVA: " + str(BVC.BaseValueAttribute))
                bl2sdk.Log("ID: " + str(BVC.InitializationDefinition))
            # I don't really think anything uses a scale but just in case
            if BVC.BaseValueConstant * BVC.BaseValueScaleConstant < MIN_ACCEPTABLE_LEVEL:
                BVC.BaseValueConstant = MIN_ACCEPTABLE_LEVEL
                BVC.BaseValueScaleConstant = 1
        index += 1
        newValue += parseBVCTuple(BVC) + ","
    # If we had a CAID array but it was empty
    if index == 0:
        return
    placeCommand(Command(
        toFullName(item),
        "ConsolidatedAttributeInitData",
        newValue[:-1] + ")"
    ))

def invPartList(item):
    if str(item) in BLACKLIST or str(item) in modified:
        return
    itemType = str(item).split(" ")[0]
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
        bl2sdk.Log(f"Unknown item type on {str(item)}")
        return
    
    levelIndexes = set()
    for part in allParts:
        weighted = getattr(item, part).WeightedParts
        if weighted != None:
            for wPart in weighted:
                if wPart.MaxGameStageIndex:
                    levelIndexes.add(wPart.MaxGameStageIndex)
    fixCAID(item, levelIndexes)

# I was hoping I could just dump the parent but it doesn't seem to work :(
for item in bl2sdk.FindAll("ItemPartListCollectionDefinition"):
    invPartList(item)
for item in bl2sdk.FindAll("WeaponPartListCollectionDefinition"):
    invPartList(item)

for item in bl2sdk.FindAll("ItemPartListDefinition"):
    levelIndexes = set()
    for wPart in item.WeightedParts:
        if wPart.MaxGameStageIndex:
            levelIndexes.add(wPart.MaxGameStageIndex)
    fixCAID(item, levelIndexes)

# Finally something simple
def namePart(item):
    if item.MaxExpLevelRequirement < MIN_ACCEPTABLE_LEVEL:
        item.MaxExpLevelRequirement = MIN_ACCEPTABLE_LEVEL
        names.addChild(Command(
            toFullName(item),
            "MaxExpLevelRequirement",
            str(MIN_ACCEPTABLE_LEVEL)
        ))

for item in bl2sdk.FindAll("WeaponNamePartDefinition"):
    namePart(item)
for item in bl2sdk.FindAll("ItemNamePartDefinition"):
    namePart(item)

mod.toFile("../ItemLevelUncapper.blcm")