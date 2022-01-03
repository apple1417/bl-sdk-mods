import unrealsdk
from typing import Any, Dict, Tuple

YAML = Dict[str, Any]

MODIFIER_NAMES: Tuple[str, ...] = (
    "scale",
    "pre-add",
    "post-add"
)

WEAPON_PART_TYPE_NAMES: Tuple[str, ...] = (
    "bodies",
    "grips",
    "barrels",
    "sights",
    "stocks",
    "elements",
    "accessories",
    "accessory2s",
    "materials",
    "prefixes",
    "titles",
)

WEAPON_MANU_ATTRIBUTES: Dict[unrealsdk.UObject, str] = {
    unrealsdk.FindObject("AttributeDefinition", obj_name): name
    for obj_name, name in (
        ("D_Attributes.WeaponManufacturer.OffhandWeapon_Is_Bandit", "Bandit (Offhand)"),
        ("D_Attributes.WeaponManufacturer.OffhandWeapon_Is_Dahl", "Dahl (Offhand)"),
        ("D_Attributes.WeaponManufacturer.OffhandWeapon_Is_Hyperion", "Hyperion (Offhand)"),
        ("D_Attributes.WeaponManufacturer.OffhandWeapon_Is_Jakobs", "Jakobs (Offhand)"),
        ("D_Attributes.WeaponManufacturer.OffhandWeapon_Is_Maliwan", "Maliwan (Offhand)"),
        ("D_Attributes.WeaponManufacturer.OffhandWeapon_Is_Tediore", "Tediore (Offhand)"),
        ("D_Attributes.WeaponManufacturer.OffhandWeapon_Is_Torgue", "Torgue (Offhand)"),
        ("D_Attributes.WeaponManufacturer.OffhandWeapon_Is_Vladof", "Vladof (Offhand)"),
        ("D_Attributes.WeaponManufacturer.Weapon_Is_Bandit", "Bandit"),
        ("D_Attributes.WeaponManufacturer.Weapon_Is_Dahl", "Dahl"),
        ("D_Attributes.WeaponManufacturer.Weapon_Is_Hyperion", "Hyperion"),
        ("D_Attributes.WeaponManufacturer.Weapon_Is_Jakobs", "Jakobs"),
        ("D_Attributes.WeaponManufacturer.Weapon_Is_Maliwan", "Maliwan"),
        ("D_Attributes.WeaponManufacturer.Weapon_Is_Tediore", "Tediore"),
        ("D_Attributes.WeaponManufacturer.Weapon_Is_Torgue", "Torgue"),
        ("D_Attributes.WeaponManufacturer.Weapon_Is_Vladof", "Vladof"),
    )
}

PART_TYPE_OVERRIDES: Dict[str, str] = {
    "GD_Weap_Shotgun.Stock.SG_Stock_Bandit": WEAPON_PART_TYPE_NAMES[4],
    "GD_Weap_Shotgun.Stock.SG_Stock_Hyperion": WEAPON_PART_TYPE_NAMES[4],
    "GD_Weap_Shotgun.Stock.SG_Stock_Jakobs": WEAPON_PART_TYPE_NAMES[4],
    "GD_Weap_Shotgun.Stock.SG_Stock_Tediore": WEAPON_PART_TYPE_NAMES[4],
    "GD_Weap_Shotgun.Stock.SG_Stock_Torgue": WEAPON_PART_TYPE_NAMES[4],
    "GD_Anemone_Weapons.Shotguns.SG_Barrel_Alien_Swordsplosion": WEAPON_PART_TYPE_NAMES[2],
}


def float_error(val: float) -> float:
    rounded = round(val, 5)
    if int(rounded) == rounded:
        return int(rounded)
    return rounded
