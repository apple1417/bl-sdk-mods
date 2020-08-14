import unrealsdk
from dataclasses import dataclass
from typing import ClassVar, Dict, List, Optional, Tuple

from Mods.ModMenu import Game, Options

from . import BaseRestrictionSet


@dataclass
class Manufacturer:
    Name: str
    FlashLabelName: str
    Artifact: Optional[str] = None
    SupportedGames: Game = Game.BL2 | Game.TPS


ALL_MANUFACTURERS: Tuple[Manufacturer, ...] = (
    Manufacturer("Bandit", "s_and_s", Artifact="Artifact_AllegianceA", SupportedGames=Game.BL2),
    Manufacturer("Dahl", "dahl", Artifact="Artifact_AllegianceB"),
    Manufacturer("Hyperion", "hyperion", Artifact="Artifact_AllegianceC"),
    Manufacturer("Jakobs", "jakobs", Artifact="Artifact_AllegianceD"),
    Manufacturer("Maliwan", "maliwan", Artifact="Artifact_AllegianceE"),
    Manufacturer("Scav", "s_and_s", SupportedGames=Game.TPS),
    Manufacturer("Tediore", "tediore", Artifact="Artifact_AllegianceF"),
    Manufacturer("Torgue", "torgue", Artifact="Artifact_AllegianceG"),
    Manufacturer("Vladof", "vladof", Artifact="Artifact_AllegianceH"),
    Manufacturer("Anshin", "anshin"),
    Manufacturer("Pangolin", "pangolin"),
    Manufacturer("Eridan", "eridan", SupportedGames=Game.BL2)
)


class Allegiance(BaseRestrictionSet):
    Name: ClassVar[str] = "Allegiance"
    Description: ClassVar[str] = "Lock items based on their manufacturer."

    UsedOptions: List[Options.Base]

    ArtifactOptionMap: Dict[str, Options.Boolean]
    FlashNameOptionMap: Dict[str, Options.Boolean]

    AllegianceRelicsOption: Options.Boolean
    ItemsOption: Options.Boolean

    def __init__(self) -> None:
        self.UsedOptions = []
        self.ArtifactOptionMap = {}
        self.FlashNameOptionMap = {}

        current_game = Game.GetCurrent()
        for manu in ALL_MANUFACTURERS:
            can_be_shown = current_game in manu.SupportedGames
            option = Options.Boolean(
                Caption=manu.Name,
                Description=f"Should you be able to equip {manu.Name} items.",
                StartingValue=True,
                IsHidden=not can_be_shown,
                Choices=self.AllowChoices
            )
            self.UsedOptions.append(option)

            # Just to prevent bandit and scav from overwriting each other
            if can_be_shown:
                if manu.Artifact is not None:
                    self.ArtifactOptionMap[manu.Artifact] = option
                self.FlashNameOptionMap[manu.FlashLabelName] = option

        self.AllegianceRelicsOption = Options.Boolean(
            Caption="Allegiance Relics",
            Description=(
                "Should you be able to equip allegiance relics. You will only be able to equip ones"
                " that boost manufacturers you're already allowed to equip."
            ),
            StartingValue=False,
            IsHidden=current_game != Game.BL2,
            Choices=self.AllowChoices
        )

        self.ItemsOption = Options.Boolean(
            Caption="Always Allow Items",
            Description="Let items be equipped regardless of manufacturer.",
            StartingValue=False
        )

        self.UsedOptions.append(self.AllegianceRelicsOption)
        self.UsedOptions.append(self.ItemsOption)

    def CanItemBeEquipped(self, item: unrealsdk.UObject) -> bool:
        manu = item.GetManufacturer()
        if manu is None:
            return True

        flash = manu.FlashLabelName
        if flash not in self.FlashNameOptionMap:
            return True

        if self.ItemsOption.CurrentValue:
            if item.Class.Name != "WillowWeapon":
                return True

        if self.AllegianceRelicsOption.CurrentValue:
            if item.Class.Name == "WillowArtifact":
                item_def = item.DefinitionData.ItemDefinition
                if item_def is not None and item_def.Name in self.ArtifactOptionMap:
                    return bool(self.ArtifactOptionMap[item_def.Name].CurrentValue)

        return bool(self.FlashNameOptionMap[flash].CurrentValue)
