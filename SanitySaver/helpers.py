import unrealsdk
from typing import Any, Dict, Iterator, Optional, Tuple, Union

JSON = Dict[str, Any]
DefDataTuple = Tuple[Union[int, unrealsdk.UObject], ...]

obj_cache: Dict[str, unrealsdk.UObject] = {}


def cached_obj_find(klass: str, name: str) -> unrealsdk.UObject:
    if name is None or name == "None":
        return None
    if name in obj_cache:
        return obj_cache[name]
    obj = unrealsdk.FindObject(klass, name)

    # Warn about missing objects but still cache them
    if obj is None:
        unrealsdk.Log(f"[SanitySaver] Couldn't find {klass}'{name}'")

    obj_cache[name] = obj
    return obj


def safe_pathname(obj: unrealsdk.UObject) -> Optional[str]:
    return None if obj is None else obj.PathName(obj)


def get_all_items_and_weapons(
    inv_manager: unrealsdk.UObject,
    include_items: bool = True,
    include_weapons: bool = True
) -> Iterator[unrealsdk.UObject]:
    seen = set()

    chain_starts = []
    if include_items:
        chain_starts.append(inv_manager.ItemChain)
    if include_weapons:
        chain_starts.append(inv_manager.InventoryChain)
    for item in chain_starts:
        while item is not None:
            if item not in seen:
                seen.add(item)
                yield item
            item = item.Inventory

    for item in inv_manager.Backpack:
        if item.Class.Name != "WillowWeapon" and include_items and item not in seen:
            seen.add(item)
            yield item
        elif item.Class.Name == "WillowWeapon" and include_weapons and item not in seen:
            seen.add(item)
            yield item

    if inv_manager.Role < 3:
        transitions = (
            inv_manager.BackpackInventoryBeingEquipped,
            inv_manager.EquippedInventoryGoingToBackpack
        )
        for item in transitions:
            if item is None:
                continue
            if item.Class.Name != "WillowWeapon" and include_items and item not in seen:
                seen.add(item)
                yield item
            elif item.Class.Name == "WillowWeapon" and include_weapons and item not in seen:
                seen.add(item)
                yield item


def expand_item_definition_data(obj: unrealsdk.FStruct) -> DefDataTuple:
    return (
        obj.ItemDefinition,
        obj.BalanceDefinition,
        obj.ManufacturerDefinition,
        obj.ManufacturerGradeIndex,
        obj.AlphaItemPartDefinition,
        obj.BetaItemPartDefinition,
        obj.GammaItemPartDefinition,
        obj.DeltaItemPartDefinition,
        obj.EpsilonItemPartDefinition,
        obj.ZetaItemPartDefinition,
        obj.EtaItemPartDefinition,
        obj.ThetaItemPartDefinition,
        obj.MaterialItemPartDefinition,
        obj.PrefixItemNamePartDefinition,
        obj.TitleItemNamePartDefinition,
        obj.GameStage,
        obj.UniqueId
    )


def pack_item_definition_data(obj: unrealsdk.FStruct) -> JSON:
    return {
        "ItemDefinition": safe_pathname(obj.ItemDefinition),
        "BalanceDefinition": safe_pathname(obj.BalanceDefinition),
        "ManufacturerDefinition": safe_pathname(obj.ManufacturerDefinition),
        "ManufacturerGradeIndex": obj.ManufacturerGradeIndex,
        "AlphaItemPartDefinition": safe_pathname(obj.AlphaItemPartDefinition),
        "BetaItemPartDefinition": safe_pathname(obj.BetaItemPartDefinition),
        "GammaItemPartDefinition": safe_pathname(obj.GammaItemPartDefinition),
        "DeltaItemPartDefinition": safe_pathname(obj.DeltaItemPartDefinition),
        "EpsilonItemPartDefinition": safe_pathname(obj.EpsilonItemPartDefinition),
        "ZetaItemPartDefinition": safe_pathname(obj.ZetaItemPartDefinition),
        "EtaItemPartDefinition": safe_pathname(obj.EtaItemPartDefinition),
        "ThetaItemPartDefinition": safe_pathname(obj.ThetaItemPartDefinition),
        "MaterialItemPartDefinition": safe_pathname(obj.MaterialItemPartDefinition),
        "PrefixItemNamePartDefinition": safe_pathname(obj.PrefixItemNamePartDefinition),
        "TitleItemNamePartDefinition": safe_pathname(obj.TitleItemNamePartDefinition),
        "GameStage": obj.GameStage,
        "UniqueId": obj.UniqueId,
    }


def unpack_item_definition_data(data: JSON) -> DefDataTuple:
    return (
        cached_obj_find("ItemDefinition", data["ItemDefinition"]),
        cached_obj_find("InventoryBalanceDefinition", data["BalanceDefinition"]),
        cached_obj_find("ManufacturerDefinition", data["ManufacturerDefinition"]),
        data["ManufacturerGradeIndex"],
        cached_obj_find("ItemPartDefinition", data["AlphaItemPartDefinition"]),
        cached_obj_find("ItemPartDefinition", data["BetaItemPartDefinition"]),
        cached_obj_find("ItemPartDefinition", data["GammaItemPartDefinition"]),
        cached_obj_find("ItemPartDefinition", data["DeltaItemPartDefinition"]),
        cached_obj_find("ItemPartDefinition", data["EpsilonItemPartDefinition"]),
        cached_obj_find("ItemPartDefinition", data["ZetaItemPartDefinition"]),
        cached_obj_find("ItemPartDefinition", data["EtaItemPartDefinition"]),
        cached_obj_find("ItemPartDefinition", data["ThetaItemPartDefinition"]),
        cached_obj_find("ItemPartDefinition", data["MaterialItemPartDefinition"]),
        cached_obj_find("ItemNamePartDefinition", data["PrefixItemNamePartDefinition"]),
        cached_obj_find("ItemNamePartDefinition", data["TitleItemNamePartDefinition"]),
        data["GameStage"],
        data["UniqueId"]
    )


def expand_weapon_definition_data(obj: unrealsdk.FStruct) -> DefDataTuple:
    return (
        obj.WeaponTypeDefinition,
        obj.BalanceDefinition,
        obj.ManufacturerDefinition,
        obj.ManufacturerGradeIndex,
        obj.BodyPartDefinition,
        obj.GripPartDefinition,
        obj.BarrelPartDefinition,
        obj.SightPartDefinition,
        obj.StockPartDefinition,
        obj.ElementalPartDefinition,
        obj.Accessory1PartDefinition,
        obj.Accessory2PartDefinition,
        obj.MaterialPartDefinition,
        obj.PrefixPartDefinition,
        obj.TitlePartDefinition,
        obj.GameStage,
        obj.UniqueId
    )


def pack_weapon_definition_data(obj: unrealsdk.FStruct) -> JSON:
    return {
        "WeaponTypeDefinition": safe_pathname(obj.WeaponTypeDefinition),
        "BalanceDefinition": safe_pathname(obj.BalanceDefinition),
        "ManufacturerDefinition": safe_pathname(obj.ManufacturerDefinition),
        "ManufacturerGradeIndex": obj.ManufacturerGradeIndex,
        "BodyPartDefinition": safe_pathname(obj.BodyPartDefinition),
        "GripPartDefinition": safe_pathname(obj.GripPartDefinition),
        "BarrelPartDefinition": safe_pathname(obj.BarrelPartDefinition),
        "SightPartDefinition": safe_pathname(obj.SightPartDefinition),
        "StockPartDefinition": safe_pathname(obj.StockPartDefinition),
        "ElementalPartDefinition": safe_pathname(obj.ElementalPartDefinition),
        "Accessory1PartDefinition": safe_pathname(obj.Accessory1PartDefinition),
        "Accessory2PartDefinition": safe_pathname(obj.Accessory2PartDefinition),
        "MaterialPartDefinition": safe_pathname(obj.MaterialPartDefinition),
        "PrefixPartDefinition": safe_pathname(obj.PrefixPartDefinition),
        "TitlePartDefinition": safe_pathname(obj.TitlePartDefinition),
        "GameStage": obj.GameStage,
        "UniqueId": obj.UniqueId
    }


def unpack_weapon_definition_data(data: JSON) -> DefDataTuple:
    return (
        cached_obj_find("WeaponTypeDefinition", data["WeaponTypeDefinition"]),
        cached_obj_find("InventoryBalanceDefinition", data["BalanceDefinition"]),
        cached_obj_find("ManufacturerDefinition", data["ManufacturerDefinition"]),
        data["ManufacturerGradeIndex"],
        cached_obj_find("WeaponPartDefinition", data["BodyPartDefinition"]),
        cached_obj_find("WeaponPartDefinition", data["GripPartDefinition"]),
        cached_obj_find("WeaponPartDefinition", data["BarrelPartDefinition"]),
        cached_obj_find("WeaponPartDefinition", data["SightPartDefinition"]),
        cached_obj_find("WeaponPartDefinition", data["StockPartDefinition"]),
        cached_obj_find("WeaponPartDefinition", data["ElementalPartDefinition"]),
        cached_obj_find("WeaponPartDefinition", data["Accessory1PartDefinition"]),
        cached_obj_find("WeaponPartDefinition", data["Accessory2PartDefinition"]),
        cached_obj_find("WeaponPartDefinition", data["MaterialPartDefinition"]),
        cached_obj_find("WeaponNamePartDefinition", data["PrefixPartDefinition"]),
        cached_obj_find("WeaponNamePartDefinition", data["TitlePartDefinition"]),
        data["GameStage"],
        data["UniqueId"]
    )
