import unrealsdk
from typing import Collection, Dict, Set, Tuple

WEAPON_PART_SLOTS: Tuple[str, ...] = (
    "BodyPartData",
    "GripPartData",
    "BarrelPartData",
    "SightPartData",
    "StockPartData",
    "ElementalPartData",
    "Accessory1PartData",
    "Accessory2PartData",
    "MaterialPartData",
)


def get_parts_on_balance(bal: unrealsdk.UObject) -> Set[unrealsdk.UObject]:
    """
    Gets all parts which can spawn on the provided balance.

    Args:
        bal: The balance definition to check.
    Returns:
        A set of parts which can spawn on the balance.
    """
    parts: Set[unrealsdk.UObject] = set()

    if bal.RuntimePartListCollection is None:
        print(f"Unknown parts collection on {bal.PathName(bal)}")
        return parts

    for slot_name in WEAPON_PART_SLOTS:
        slot = getattr(bal.RuntimePartListCollection, slot_name)
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
        for weap_def in definitions:
            parts.update(_parts_by_definition[weap_def])
        return parts

    for bal in unrealsdk.FindAll("WeaponBalanceDefinition"):
        if bal.RuntimePartListCollection is None:
            print("Unknown parts collection on " + bal.PathName(bal))
            continue

        weap_def = bal.RuntimePartListCollection.AssociatedWeaponType
        if weap_def not in _parts_by_definition:
            _parts_by_definition[weap_def] = set()

        _parts_by_definition[weap_def].update(get_parts_on_balance(bal))

    return get_parts_for_definitions(definitions)
