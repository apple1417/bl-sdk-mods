import unrealsdk
from dataclasses import dataclass
from typing import ClassVar, Dict, List, Optional, Tuple

from . import BaseRestrictionSet, IS_BL2
from Mods import AAA_OptionsWrapper as OptionsWrapper


@dataclass
class Manufacturer:
    Name: str
    FlashLabelName: str
    Artifact: Optional[str] = None
    InBL2: bool = True
    InTPS: bool = True


ALL_MANUFACTURERS: Tuple[Manufacturer, ...] = (
    Manufacturer("Bandit", "s_and_s", Artifact="Artifact_AllegianceA", InTPS=False),
    Manufacturer("Dahl", "dahl", Artifact="Artifact_AllegianceB"),
    Manufacturer("Hyperion", "hyperion", Artifact="Artifact_AllegianceC"),
    Manufacturer("Jakobs", "jakobs", Artifact="Artifact_AllegianceD"),
    Manufacturer("Maliwan", "maliwan", Artifact="Artifact_AllegianceE"),
    Manufacturer("Scav", "s_and_s", InBL2=False),
    Manufacturer("Tediore", "tediore", Artifact="Artifact_AllegianceF"),
    Manufacturer("Torgue", "torgue", Artifact="Artifact_AllegianceG"),
    Manufacturer("Vladof", "vladof", Artifact="Artifact_AllegianceH"),
    Manufacturer("Anshin", "anshin"),
    Manufacturer("Pangolin", "pangolin"),
    Manufacturer("Eridan", "eridan", InTPS=False)
)


class Allegiance(BaseRestrictionSet):
    Name: ClassVar[str] = "Allegiance"
    Options: List[OptionsWrapper.Base]

    ArtifactOptionMap: Dict[str, OptionsWrapper.Boolean]
    FlashNameOptionMap: Dict[str, OptionsWrapper.Boolean]

    AllegianceRelicsOption: OptionsWrapper.Boolean
    ItemsOption: OptionsWrapper.Boolean

    def __init__(self) -> None:
        self.Options = []
        self.ArtifactOptionMap = {}
        self.FlashNameOptionMap = {}
        for manu in ALL_MANUFACTURERS:
            canBeShown = (IS_BL2 and manu.InBL2) or (not IS_BL2 and manu.InTPS)
            option = OptionsWrapper.Boolean(
                Caption=manu.Name,
                Description=f"Should you be able to equip {manu.Name} items.",
                StartingValue=True,
                IsHidden=not canBeShown,
                Choices=self.AllowChoices
            )
            self.Options.append(option)

            # Just to prevent bandit and scav from overwriting each other
            if canBeShown:
                if manu.Artifact is not None:
                    self.ArtifactOptionMap[manu.Artifact] = option
                self.FlashNameOptionMap[manu.FlashLabelName] = option

        self.AllegianceRelicsOption = OptionsWrapper.Boolean(
            Caption="Allegiance Relics",
            Description=(
                "Should you be able to equip allegiance relics. You will only be able to equip ones"
                " that boost manufacturers you're already allowed to equip."
            ),
            StartingValue=False,
            IsHidden=not IS_BL2,
            Choices=self.AllowChoices
        )

        self.ItemsOption = OptionsWrapper.Boolean(
            Caption="Always Allow Items",
            Description="Let items be equipped regardless of manufacturer.",
            StartingValue=False
        )

        self.Options.append(self.AllegianceRelicsOption)
        self.Options.append(self.ItemsOption)

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
                itemDef = item.DefinitionData.ItemDefinition
                if itemDef is not None and itemDef.Name in self.ArtifactOptionMap:
                    return bool(self.ArtifactOptionMap[itemDef.Name].CurrentValue)

        return bool(self.FlashNameOptionMap[flash].CurrentValue)
