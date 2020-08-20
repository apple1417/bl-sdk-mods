import unrealsdk
from dataclasses import dataclass
from typing import ClassVar, Dict, List, Tuple

from Mods.ModMenu import Game, Options

from . import BaseRestrictionSet


@dataclass
class WeaponType:
    Name: str
    Value: int
    SupportedGames: Game = Game.BL2 | Game.TPS


@dataclass
class ItemType:
    Name: str
    Class: str
    SupportedGames: Game = Game.BL2 | Game.TPS


ALL_WEAPON_TYPES: Tuple[WeaponType, ...] = (
    WeaponType("Pistols", 0),
    WeaponType("Shotguns", 1),
    WeaponType("SMGs", 2),
    WeaponType("Snipers", 3),
    WeaponType("Rifles", 4),
    WeaponType("Launchers", 5),
    WeaponType("Lasers", 6, Game.TPS)
)

ALL_ITEM_TYPES: Tuple[ItemType, ...] = (
    ItemType("Shields", "WillowShield"),
    ItemType("Grenade Mods", "WillowGrenadeMod"),
    ItemType("Class Mods", "WillowClassMod"),
    ItemType("Relics", "WillowArtifact", Game.BL2),
    ItemType("Oz Kits", "WillowArtifact", Game.TPS)
)


class WeapItemType(BaseRestrictionSet):
    Name: ClassVar[str] = "Weapon/Item Type"
    Description: ClassVar[str] = "Lock items based on their type."

    UsedOptions: List[Options.Base]

    WeaponOptionMap: Dict[int, Options.Boolean]
    ItemOptionMap: Dict[str, Options.Boolean]

    def __init__(self) -> None:
        self.UsedOptions = []
        self.WeaponOptionMap = {}
        self.ItemOptionMap = {}

        current_game = Game.GetCurrent()
        for item_type in ALL_WEAPON_TYPES + ALL_ITEM_TYPES:
            can_be_shown = current_game in item_type.SupportedGames
            option = Options.Boolean(
                Caption=item_type.Name,
                Description=f"Should you be able to equip {item_type.Name}.",
                StartingValue=True,
                Choices=self.AllowChoices,
                IsHidden=not can_be_shown
            )
            self.UsedOptions.append(option)

            # Just to prevent relics/oz kits from overwriting each other
            if can_be_shown:
                if isinstance(item_type, WeaponType):
                    self.WeaponOptionMap[item_type.Value] = option
                else:
                    self.ItemOptionMap[item_type.Class] = option

    def CanItemBeEquipped(self, item: unrealsdk.UObject) -> bool:
        if item.Class.Name == "WillowWeapon":
            if item.DefinitionData.WeaponTypeDefinition is None:
                return True
            weap_type = item.DefinitionData.WeaponTypeDefinition.WeaponType
            if weap_type not in self.WeaponOptionMap:
                return True
            return bool(self.WeaponOptionMap[weap_type].CurrentValue)

        else:
            if item.Class.Name not in self.ItemOptionMap:
                return True
            return bool(self.ItemOptionMap[item.Class.Name].CurrentValue)
