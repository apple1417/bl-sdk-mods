import unrealsdk
from typing import Collection, Dict, Set

from .data import (ALLOWED_DEFINITION_CLASSES, ITEM_DEFINITION_PART_SLOTS, ITEM_PART_SLOTS,
                   PART_LIST_SLOTS, WEAPON_PART_SLOTS)


def get_parts_on_item_definition(item_def: unrealsdk.UObject) -> Set[unrealsdk.UObject]:
    """
    Gets all parts which can spawn as defined by the provided item definition.

    Args:
        item_def: The item definition to check.
    Returns:
        A set of parts which can spawn on the item definition.
    """
    parts: Set[unrealsdk.UObject] = set()

    for slot_name in ITEM_DEFINITION_PART_SLOTS:
        slot = getattr(item_def, slot_name)
        if slot is None:
            continue
        for part_struct in slot.WeightedParts:
            if part_struct.Part is None:
                continue
            parts.add(part_struct.Part)

    return parts


def get_parts_on_balance(bal: unrealsdk.UObject) -> Set[unrealsdk.UObject]:
    """
    Gets all parts which can spawn on the provided balance.

    Args:
        bal: The balance definition to check.
    Returns:
        A set of parts which can spawn on the balance.
    """

    # Of course nothing's simple, so we need different strategies for weapons, shields, and nades
    is_weapon = bal.Class.Name == "WeaponBalanceDefinition"
    is_shield = (
        bal.InventoryDefinition is not None
        and bal.InventoryDefinition.Class.Name == "ShieldDefinition"
    )

    if is_shield:
        return get_parts_on_item_definition(bal.InventoryDefinition)

    part_list = None
    for list_slot in PART_LIST_SLOTS:
        part_list = getattr(bal, list_slot, None)
        if part_list is not None:
            break
    else:
        if not is_weapon and bal.InventoryDefinition is not None:
            return get_parts_on_item_definition(bal.InventoryDefinition)
        return set()

    parts: Set[unrealsdk.UObject] = set()
    for slot_name in (WEAPON_PART_SLOTS if is_weapon else ITEM_PART_SLOTS):
        slot = getattr(part_list, slot_name)
        if not slot.bEnabled:
            continue
        for part_struct in slot.WeightedParts:
            part = part_struct.Part
            if part is None:
                continue
            if part.Class.Name == "WeaponNamePartDefinition":
                continue
            parts.add(part)

    return parts


_parts_by_definition: Dict[unrealsdk.UObject, Set[unrealsdk.UObject]] = {}


def get_parts_for_definitions(definitions: Collection[unrealsdk.UObject]) -> Set[unrealsdk.UObject]:
    """
    Gets all parts used on items of the provided definitions, by checking balances.

    Args:
        definitions: A collection of definition objects to get parts for.
    Returns:
        A set of used part objects.
    """
    if len(_parts_by_definition) > 0:
        parts: Set[unrealsdk.UObject] = set()
        for def_obj in definitions:
            parts.update(_parts_by_definition[def_obj])
        return parts

    for bal in unrealsdk.FindAll("InventoryBalanceDefinition", True):
        def_obj = None
        if bal.Class.Name == "WeaponBalanceDefinition":
            if bal.RuntimePartListCollection is None:
                continue
            def_obj = bal.RuntimePartListCollection.AssociatedWeaponType
        else:
            if bal.InventoryDefinition is None:
                continue
            if bal.InventoryDefinition.Class.Name not in ALLOWED_DEFINITION_CLASSES:
                continue
            def_obj = bal.InventoryDefinition

        if def_obj not in _parts_by_definition:
            _parts_by_definition[def_obj] = set()

        _parts_by_definition[def_obj].update(get_parts_on_balance(bal))

    return get_parts_for_definitions(definitions)
