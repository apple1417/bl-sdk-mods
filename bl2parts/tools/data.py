import unrealsdk
import json
from typing import Dict, Tuple, Union

ALL_WEAPON_DEFINITIONS: Dict[str, Tuple[str, ...]] = {
    "shotgun": (
        "GD_Weap_Shotgun.A_Weapons.WT_Bandit_Shotgun",
        "GD_Weap_Shotgun.A_Weapons.WT_Hyperion_Shotgun",
        "GD_Weap_Shotgun.A_Weapons.WT_Jakobs_Shotgun",
        "GD_Weap_Shotgun.A_Weapons.WT_Tediore_Shotgun",
        "GD_Weap_Shotgun.A_Weapons.WT_Torgue_Shotgun",
    )
}

NON_UNIQUE_BALANCES: Dict[str, Tuple[str, ...]] = {
    "shotgun": (
        "GD_Aster_Weapons.Shotguns.SG_Bandit_4_Quartz",
        "GD_Aster_Weapons.Shotguns.SG_Hyperion_4_Diamond",
        "GD_Aster_Weapons.Shotguns.SG_Jakobs_4_Citrine",
        "GD_Aster_Weapons.Shotguns.SG_Tediore_4_CubicZerconia",
        "GD_Aster_Weapons.Shotguns.SG_Torgue_4_Rock",
        "GD_Ma_Weapons.A_Weapons.SG_Bandit_6_Glitch",
        "GD_Ma_Weapons.A_Weapons.SG_Hyperion_6_Glitch",
        "GD_Ma_Weapons.A_Weapons.SG_Jakobs_6_Glitch",
        "GD_Ma_Weapons.A_Weapons.SG_Old_Hyperion_6_Glitch",
        "GD_Ma_Weapons.A_Weapons.SG_Tediore_6_Glitch",
        "GD_Ma_Weapons.A_Weapons.SG_Torgue_6_Glitch",
        "GD_Weap_Shotgun.A_Weapons.SG_Bandit_4_VeryRare",
        "GD_Weap_Shotgun.A_Weapons.SG_Bandit_5_Alien",
        "GD_Weap_Shotgun.A_Weapons.SG_Hyperion_4_VeryRare",
        "GD_Weap_Shotgun.A_Weapons.SG_Hyperion_5_Alien",
        "GD_Weap_Shotgun.A_Weapons.SG_Jakobs_4_VeryRare",
        "GD_Weap_Shotgun.A_Weapons.SG_Old_Hyperion_4_VeryRare",
        "GD_Weap_Shotgun.A_Weapons.SG_Tediore_4_VeryRare",
        "GD_Weap_Shotgun.A_Weapons.SG_Tediore_5_Alien",
        "GD_Weap_Shotgun.A_Weapons.SG_Torgue_4_VeryRare",
    )
}

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

DEFINITION_PART_TYPE: str = "definition"

PLURAL_WEAPON_PART_TYPE: Dict[str, str] = {
    "body": "bodies",
    "grip": "grips",
    "barrel": "barrels",
    "sight": "sights",
    "stock": "stocks",
    "element": "elements",
    "accessory": "accessories",
    "accessory2": "accessory2s",
    "material": "materials",
    "prefix": "prefixes",
    "title": "titles",
    "definition": "definitions",
}

WEAPON_MANU_ATTRIBUTES: Dict[unrealsdk.UObject, str] = {
    unrealsdk.FindObject("AttributeDefinition", obj_name): name
    for obj_name, name in (
        ("D_Attributes.WeaponManufacturer.Weapon_Is_Bandit", "Bandit"),
        ("D_Attributes.WeaponManufacturer.Weapon_Is_Dahl", "Dahl"),
        ("D_Attributes.WeaponManufacturer.Weapon_Is_Hyperion_Old", "Old Hyperion"),
        ("D_Attributes.WeaponManufacturer.Weapon_Is_Hyperion", "Hyperion"),
        ("D_Attributes.WeaponManufacturer.Weapon_Is_Jakobs", "Jakobs"),
        ("D_Attributes.WeaponManufacturer.Weapon_Is_Maliwan", "Maliwan"),
        ("D_Attributes.WeaponManufacturer.Weapon_Is_Tediore", "Tediore"),
        ("D_Attributes.WeaponManufacturer.Weapon_Is_Torgue", "Torgue"),
        ("D_Attributes.WeaponManufacturer.Weapon_Is_Vladof", "Vladof"),
    )
    if unrealsdk.FindObject("AttributeDefinition", obj_name) is not None
}

SCALING_ATTRIBUTES: Dict[unrealsdk.UObject, str] = {
    unrealsdk.FindObject("AttributeDefinition", obj_name): scale
    for obj_name, scale in (
        ("D_Attributes.ExperienceResourcePool.PlayerExperienceLevel", "[Player Level]"),
    )
    if unrealsdk.FindObject("AttributeDefinition", obj_name) is not None
}

PART_TYPE_OVERRIDES: Dict[str, str] = {
    "GD_Anemone_Weapons.Shotguns.SG_Barrel_Alien_Swordsplosion": WEAPON_PART_TYPE_NAMES[2],
    "GD_Cork_Weap_Shotgun.Stock.SG_Stock_Jakobs_Boomacorn": WEAPON_PART_TYPE_NAMES[4],
    "GD_Cork_Weap_Shotgun.Stock.SG_Stock_Jakobs_TooScoops": WEAPON_PART_TYPE_NAMES[4],
    "GD_Weap_Shotgun.Stock.SG_Stock_Bandit": WEAPON_PART_TYPE_NAMES[4],
    "GD_Weap_Shotgun.Stock.SG_Stock_Hyperion": WEAPON_PART_TYPE_NAMES[4],
    "GD_Weap_Shotgun.Stock.SG_Stock_Jakobs": WEAPON_PART_TYPE_NAMES[4],
    "GD_Weap_Shotgun.Stock.SG_Stock_Tediore": WEAPON_PART_TYPE_NAMES[4],
    "GD_Weap_Shotgun.Stock.SG_Stock_Torgue": WEAPON_PART_TYPE_NAMES[4],
}

"""
Dict of:
```
"<obj name>": {
    "name": "<name>",
    "game_overrides": {
        "<game>": "<name>"
    }
    "type": "<weapon type>",
    "slot": "<part slot>",
}
```

`game_overrides` is optional if not needed.
"""
PART_NAMES: Dict[str, Dict[str, Union[str, Dict[str, str]]]]

with open("Mods/bl2parts/part_names.json") as file:
    PART_NAMES = json.load(file)
