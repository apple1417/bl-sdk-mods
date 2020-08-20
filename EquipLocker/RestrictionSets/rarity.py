import unrealsdk
from dataclasses import dataclass
from typing import ClassVar, Dict, List, Tuple

from Mods.ModMenu import Game, Options

from . import BaseRestrictionSet


@dataclass
class RarityLevel:
    Name: str
    Value: int
    SupportedGames: Game = Game.BL2 | Game.TPS


ALL_RARITIES: Tuple[RarityLevel, ...] = (
    RarityLevel("Common", 1),
    RarityLevel("Uncommon", 2),
    RarityLevel("Rare", 3),
    RarityLevel("Very Rare", 4),
    RarityLevel("Legendary", 5),
    RarityLevel("Seraph", 6, Game.BL2),
    RarityLevel("Glitch", 6, Game.TPS),
    RarityLevel("Rainbow", 7, Game.BL2)
)


class Rarity(BaseRestrictionSet):
    Name: ClassVar[str] = "Rarity"
    Description: ClassVar[str] = (
        "Lock items based on their rarity. Mods that edit rarities may be compatible if they"
        " logically categorised all their new rarities."
    )

    UsedOptions: List[Options.Base]

    Globals: ClassVar[unrealsdk.UObject] = unrealsdk.FindObject(
        "GlobalsDefinition", "GD_Globals.General.Globals"
    )

    RarityOptionMap: Dict[int, Options.Boolean]

    def __init__(self) -> None:
        self.UsedOptions = []
        self.RarityOptionMap = {}

        current_game = Game.GetCurrent()
        for rarity in ALL_RARITIES:
            can_be_shown = current_game in rarity.SupportedGames
            option = Options.Boolean(
                Caption=rarity.Name,
                Description=f"Should you be able to equip {rarity.Name} items.",
                StartingValue=True,
                Choices=self.AllowChoices,
                IsHidden=not can_be_shown
            )
            self.UsedOptions.append(option)

            # Just to prevent seraph/glitch from overwriting each other
            if can_be_shown:
                self.RarityOptionMap[rarity.Value] = option

    def CanItemBeEquipped(self, item: unrealsdk.UObject) -> bool:
        rarity = self.Globals.GetRarityForLevel(item.RarityLevel)
        if rarity not in self.RarityOptionMap:
            return True

        return bool(self.RarityOptionMap[rarity].CurrentValue)
