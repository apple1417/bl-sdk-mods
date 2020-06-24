import unrealsdk
from dataclasses import dataclass
from typing import ClassVar, Dict, List, Tuple

from . import BaseRestrictionSet, IS_BL2
from Mods import AAA_OptionsWrapper as OptionsWrapper


@dataclass
class RarityLevel:
    Name: str
    Value: int
    InBL2: bool = True
    InTPS: bool = True


ALL_RARITIES: Tuple[RarityLevel, ...] = (
    RarityLevel("Common", 1),
    RarityLevel("Uncommon", 2),
    RarityLevel("Rare", 3),
    RarityLevel("Very Rare", 4),
    RarityLevel("Legendary", 5),
    RarityLevel("Seraph", 6, InTPS=False),
    RarityLevel("Glitch", 6, InBL2=False),
    RarityLevel("Rainbow", 7, InTPS=False)
)


class Rarity(BaseRestrictionSet):
    Name: ClassVar[str] = "Rarity"
    Options: List[OptionsWrapper.Base]

    Globals: ClassVar[unrealsdk.UObject] = unrealsdk.FindObject(
        "GlobalsDefinition", "GD_Globals.General.Globals"
    )

    RarityOptionMap: Dict[int, OptionsWrapper.Boolean]

    def __init__(self) -> None:
        self.Options = []
        self.RarityOptionMap = {}
        for rarity in ALL_RARITIES:
            canBeShown = (IS_BL2 and rarity.InBL2) or (not IS_BL2 and rarity.InTPS)
            option = OptionsWrapper.Boolean(
                Caption=rarity.Name,
                Description=f"Should you be able to equip {rarity.Name} items.",
                StartingValue=True,
                IsHidden=not canBeShown,
                Choices=self.AllowChoices
            )
            self.Options.append(option)

            # Just to prevent seraph/glitch from overwriting each other
            if canBeShown:
                self.RarityOptionMap[rarity.Value] = option

    def CanItemBeEquipped(self, item: unrealsdk.UObject) -> bool:
        rarity = self.Globals.GetRarityForLevel(item.RarityLevel)
        if rarity not in self.RarityOptionMap:
            return True

        return bool(self.RarityOptionMap[rarity].CurrentValue)
