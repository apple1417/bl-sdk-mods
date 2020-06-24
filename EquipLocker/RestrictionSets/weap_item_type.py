import unrealsdk
from dataclasses import dataclass
from typing import ClassVar, Dict, List, Tuple

from . import BaseRestrictionSet, IS_BL2
from Mods import AAA_OptionsWrapper as OptionsWrapper


@dataclass
class WeaponType:
    Name: str
    Value: int
    InBL2: bool = True
    InTPS: bool = True


@dataclass
class ItemType:
    Name: str
    Class: str
    InBL2: bool = True
    InTPS: bool = True


ALL_WEAPON_TYPES: Tuple[WeaponType, ...] = (
    WeaponType("Pistols", 0),
    WeaponType("Shotguns", 1),
    WeaponType("SMGs", 2),
    WeaponType("Snipers", 3),
    WeaponType("Rifles", 4),
    WeaponType("Launchers", 5),
    WeaponType("Lasers", 6, InBL2=False)
)

ALL_ITEM_TYPES: Tuple[ItemType, ...] = (
    ItemType("Shields", "WillowShield"),
    ItemType("Grenade Mods", "WillowGrenadeMod"),
    ItemType("Class Mods", "WillowClassMod"),
    ItemType("Relics", "WillowArtifact", InTPS=False),
    ItemType("Oz Kits", "WillowArtifact", InBL2=False)
)


class WeapItemType(BaseRestrictionSet):
    Name: ClassVar[str] = "Weapon/Item Type"
    Options: List[OptionsWrapper.Base]

    WeaponOptionMap: Dict[int, OptionsWrapper.Boolean]
    ItemOptionMap: Dict[str, OptionsWrapper.Boolean]

    def __init__(self) -> None:
        self.Options = []
        self.WeaponOptionMap = {}
        self.ItemOptionMap = {}
        for type in ALL_WEAPON_TYPES + ALL_ITEM_TYPES:
            canBeShown = (IS_BL2 and type.InBL2) or (not IS_BL2 and type.InTPS)
            option = OptionsWrapper.Boolean(
                Caption=type.Name,
                Description=f"Should you be able to equip {type.Name}.",
                StartingValue=True,
                IsHidden=not canBeShown,
                Choices=self.AllowChoices
            )
            self.Options.append(option)

            # Just to prevent relics/oz kits from overwriting each other
            if canBeShown:
                if isinstance(type, WeaponType):
                    self.WeaponOptionMap[type.Value] = option
                else:
                    self.ItemOptionMap[type.Class] = option

    def CanItemBeEquipped(self, item: unrealsdk.UObject) -> bool:
        if item.Class.Name == "WillowWeapon":
            if item.DefinitionData.WeaponTypeDefinition is None:
                return True
            weapType = item.DefinitionData.WeaponTypeDefinition.WeaponType
            if weapType not in self.WeaponOptionMap:
                return True
            return bool(self.WeaponOptionMap[weapType].CurrentValue)

        else:
            if item.Class.Name not in self.ItemOptionMap:
                return True
            return bool(self.ItemOptionMap[item.Class.Name].CurrentValue)
