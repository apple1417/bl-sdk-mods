import unrealsdk
from typing import Any, Dict, Tuple

YAML = Dict[str, Any]

MODIFIER_NAMES: Tuple[str, ...] = (
    "scale",
    "pre-add",
    "post-add"
)

WEAPON_PART_TYPE_NAMES: Tuple[str, ...] = (
    "body",
    "grip",
    "barrel",
    "sight",
    "stock",
    "element",
    "accessory",
    "accessory2",
    "material",
    "prefix",
    "title",
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
    "GD_Weap_Shotgun.Stock.SG_Stock_Bandit": "stock",
    "GD_Weap_Shotgun.Stock.SG_Stock_Hyperion": "stock",
    "GD_Weap_Shotgun.Stock.SG_Stock_Jakobs": "stock",
    "GD_Weap_Shotgun.Stock.SG_Stock_Tediore": "stock",
    "GD_Weap_Shotgun.Stock.SG_Stock_Torgue": "stock",
}


def float_error(val: float) -> float:
    return round(val, 5)
