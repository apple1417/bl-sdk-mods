import unrealsdk
from typing import Dict, Sequence, Tuple, cast

from Mods.ModMenu import (EnabledSaveType, Game, Mods, ModTypes, Options, RegisterMod,
                          SaveModSettings, SDKMod)
from Mods.PythonPartNotifier.PartNamer import GetPartName


class PartOption(Options.Boolean):
    Parts: Tuple[str, ...]

    def __init__(
        self,
        Caption: str,
        StartingValue: bool,
        Parts: Tuple[str, ...],
        Description: str = "Should the part be shown in the description or not."
    ):
        super().__init__(Caption, Description, StartingValue)
        self.Parts = Parts


class ItemClassOption(Options.Nested):
    ItemClass: str

    def __init__(
        self,
        Caption: str,
        ItemClass: str,
        Children: Sequence[PartOption],
        *,
        IsHidden: bool = False
    ) -> None:
        super().__init__(
            Caption,
            f"Configure which {Caption[:-1].lower()} parts should be shown.",
            Children,
            IsHidden=IsHidden
        )
        self.ItemClass = ItemClass


class PythonPartNotifier(SDKMod):
    Name: str = "Python Part Notifier"
    Author: str = "apple1417"
    Description: str = (
        "Lets you show all parts on your items and weapons, even if other mods have modified them.\n"
        "\n"
        "Make sure to check out the options menu to customize what exactly is shown."
    )
    Version: str = "1.5"

    Types: ModTypes = ModTypes.Utility
    SaveEnabledState: EnabledSaveType = EnabledSaveType.LoadWithSettings

    SettingsInputs: Dict[str, str] = {
        "Enter": "Enable",
        "R": "Reset Options"
    }

    DetailedOption: Options.Boolean
    FontSizeOption: Options.Slider
    RemoveOption: Options.Boolean

    # The SDK doesn't support unicode yet (even though the game does), so some characters need to be
    #  replaced to keep everything readable
    UNICODE_REPLACEMENTS: Dict[str, str] = {
        "•": "*"  # The bullet point at the start of every line
    }

    # Some terms should be changed in TPS
    TPS_REPLACEMENTS: Dict[str, str] = {
        "Bandit": "Scav",
        "Bouncing Bonny": "Bouncing Bazza",
        "Relic": "Oz Kit"
    }

    def __init__(self) -> None:
        self.SetDefaultOptions()

    def SettingsInputPressed(self, action: str) -> None:
        if action == "Reset Options":
            self.SetDefaultOptions()
            SaveModSettings(self)
        else:
            super().SettingsInputPressed(action)

    def SetDefaultOptions(self) -> None:
        self.DetailedOption = Options.Boolean(
            "Detailed Part Names",
            "Should part names include the weapon and part type they're for rather than just"
            " the manufacturer.",
            False
        )
        self.FontSizeOption = Options.Slider(
            "Font Size",
            "What font size should the parts text use. Decrease this if text is getting cut off.",
            14, 8, 24, 1
        )
        self.RemoveOption = Options.Boolean(
            "Remove Descriptions",
            "Should the default descriptions be removed to create more space for the part"
            " descriptions.",
            False
        )

        self.Options = [
            self.DetailedOption,
            self.FontSizeOption,
            self.RemoveOption,
            ItemClassOption(
                "Weapons", "WillowWeapon", (
                    PartOption("Accessory", True, ("Accessory1PartDefinition",)),
                    PartOption("2nd Accessory", False, ("Accessory2PartDefinition",)),
                    PartOption("Barrel", True, ("BarrelPartDefinition",)),
                    PartOption("Body", False, ("BodyPartDefinition",)),
                    PartOption("Element", False, ("ElementalPartDefinition",)),
                    PartOption("Grip", True, ("GripPartDefinition",)),
                    PartOption("Material", False, ("MaterialPartDefinition",)),
                    PartOption("Sight", True, ("SightPartDefinition",)),
                    PartOption("Stock", True, ("StockPartDefinition",)),
                    PartOption("Type", False, ("WeaponTypeDefinition",))
                ),
            ),
            ItemClassOption(
                "Shields", "WillowShield", (
                    PartOption("Accessory", False, ("DeltaItemPartDefinition",)),
                    PartOption("Battery", True, ("BetaItemPartDefinition",)),
                    PartOption("Body", True, ("AlphaItemPartDefinition",)),
                    PartOption("Capacitor", True, ("GammaItemPartDefinition",)),
                    PartOption("Material", False, ("MaterialItemPartDefinition",)),
                    PartOption("Type", False, ("ItemDefinition",)),
                    PartOption("Extras", True, (
                        "EpsilonItemPartDefinition",
                        "ZetaItemPartDefinition",
                        "EtaItemPartDefinition",
                        "ThetaItemPartDefinition"
                    ), "Should parts in slots that aren't normally used be shown if they contain a part.")
                )
            ),
            ItemClassOption(
                "Grenades", "WillowGrenadeMod", (
                    PartOption("Accessory", False, ("DeltaItemPartDefinition",)),
                    PartOption("Blast Radius", True, ("ZetaItemPartDefinition",)),
                    PartOption("Child Count", True, ("EtaItemPartDefinition",)),
                    PartOption("Damage", False, ("EpsilonItemPartDefinition",)),
                    PartOption("Delivery", True, ("BetaItemPartDefinition",)),
                    PartOption("Material", False, ("MaterialItemPartDefinition",)),
                    PartOption("Payload", False, ("AlphaItemPartDefinition",)),
                    PartOption("Status Damage", False, ("ThetaItemPartDefinition",)),
                    PartOption("Trigger", True, ("GammaItemPartDefinition",)),
                    PartOption("Type", False, ("ItemDefinition",))
                )
            ),
            ItemClassOption(
                "Class Mods", "WillowClassMod", (
                    PartOption("Specialization", True, ("AlphaItemPartDefinition",)),
                    PartOption("Primary", True, ("BetaItemPartDefinition",)),
                    PartOption("Secondary", True, ("GammaItemPartDefinition",)),
                    PartOption("Penalty", True, ("MaterialItemPartDefinition",)),
                    PartOption("Type", False, ("ItemDefinition",)),
                    PartOption("Extras", True, (
                        "DeltaItemPartDefinition",
                        "EpsilonItemPartDefinition",
                        "ZetaItemPartDefinition",
                        "EtaItemPartDefinition",
                        "ThetaItemPartDefinition"
                    ), "Should parts in slots that aren't normally used be shown if they contain a part.")
                )
            ),
            ItemClassOption(
                "Relics", "WillowArtifact", (
                    PartOption("Body", False, ("EtaItemPartDefinition",)),
                    PartOption("Upgrade", True, ("ThetaItemPartDefinition",)),
                    # These are the various relic enable effect parts
                    # There isn't really a pattern to them so go with the slot name
                    PartOption("Alpha", False, ("AlphaItemPartDefinition",)),
                    PartOption("Beta", False, ("BetaItemPartDefinition",)),
                    PartOption("Gamma", False, ("GammaItemPartDefinition",)),
                    PartOption("Delta", False, ("DeltaItemPartDefinition",)),
                    PartOption("Epsilon", False, ("EpsilonItemPartDefinition",)),
                    PartOption("Zeta", False, ("ZetaItemPartDefinition",)),
                    PartOption("Type", False, ("ItemDefinition",)),
                    PartOption("Extras", True, (
                        "MaterialItemPartDefinition",
                    ), "Should parts in slots that aren't normally used be shown if they contain a part.")
                ), IsHidden=Game.GetCurrent() != Game.BL2
            ),
            ItemClassOption(
                "Oz Kits", "WillowArtifact", (
                    PartOption("Body", False, ("EtaItemPartDefinition",)),
                    PartOption("Upgrade", True, ("ThetaItemPartDefinition",)),
                    # These are the various relic enable effect parts
                    # There isn't really a pattern to them so go with the slot name
                    PartOption("Alpha", False, ("AlphaItemPartDefinition",)),
                    PartOption("Beta", False, ("BetaItemPartDefinition",)),
                    PartOption("Gamma", False, ("GammaItemPartDefinition",)),
                    PartOption("Delta", False, ("DeltaItemPartDefinition",)),
                    PartOption("Epsilon", False, ("EpsilonItemPartDefinition",)),
                    PartOption("Zeta", False, ("ZetaItemPartDefinition",)),
                    PartOption("Type", False, ("ItemDefinition",)),
                    PartOption("Extras", True, (
                        "MaterialItemPartDefinition",
                    ), "Should parts in slots that aren't normally used be shown if they contain a part.")
                ), IsHidden=Game.GetCurrent() != Game.TPS
            )
        ]

    def translateTPS(self, text: str, force: bool = False) -> str:
        if force or Game.GetCurrent() == Game.TPS:
            for rep in self.TPS_REPLACEMENTS:
                text = text.replace(rep, self.TPS_REPLACEMENTS[rep])
        return text

    _block_fun_stats: bool = False

    def Enable(self) -> None:
        # Called whenever an item card is created
        def SetItemCardEx(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            # If we don't actually have an item then there's no need to do anything special
            item = params.InventoryItem.ObjectPointer
            if item is None:
                return True

            # Get the default text and convert it as needed
            text = item.GenerateFunStatsText()
            if text is None or self.RemoveOption.CurrentValue:
                text = ""
            else:
                for rep in self.UNICODE_REPLACEMENTS:
                    text = text.replace(rep, self.UNICODE_REPLACEMENTS[rep])

            part_text = ""
            for option in self.Options:
                if not isinstance(option, ItemClassOption):
                    continue
                if option.ItemClass != item.Class.Name:
                    continue

                for child in option.Children:
                    child = cast(PartOption, child)
                    if not child.CurrentValue:
                        continue
                    if len(child.Parts) == 1:
                        part_text += self.handleSingleSlot(item, child)
                    else:
                        part_text += self.handleMultipleSlots(item, child)
                break
            else:
                return True

            # If we're not adding anthing then we can let the normal function handle it
            if len(part_text) == 0:
                return True

            text += f"<font size=\"{self.FontSizeOption.CurrentValue}\" color=\"#FFFFFF\">"
            text += self.translateTPS(part_text)
            text += "</font>"

            # This function is actually quite complex, so rather than replicate it we'll write out
            #  our text, then let the regular function run but block it from overwriting the text
            caller.SetFunStats(text)
            self._block_fun_stats = True
            return True

        # Called to set the description on an item card
        # We just hook this so that we can occasionally block it
        def SetFunStats(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            if self._block_fun_stats:
                self._block_fun_stats = False
                return False
            return True

        unrealsdk.RegisterHook("WillowGame.ItemCardGFxObject.SetFunStats", "PythonPartNotifier", SetFunStats)
        unrealsdk.RegisterHook("WillowGame.ItemCardGFxObject.SetItemCardEx", "PythonPartNotifier", SetItemCardEx)

    def Disable(self) -> None:
        unrealsdk.RemoveHook("WillowGame.ItemCardGFxObject.SetFunStats", "PythonPartNotifier")
        unrealsdk.RemoveHook("WillowGame.ItemCardGFxObject.SetItemCardEx", "PythonPartNotifier")

    def handleSingleSlot(self, item: unrealsdk.UObject, option: PartOption) -> str:
        part = getattr(item.DefinitionData, option.Parts[0])
        if part is None:
            return ""

        text = f"{option.Caption}: <font color='#FFDEAD'>"
        text += GetPartName(part, self.DetailedOption.CurrentValue)
        text += "</font>"

        # TODO: Stats?

        return text + "\n"

    def handleMultipleSlots(self, item: unrealsdk.UObject, option: PartOption) -> str:
        # Get a count of each part so we can combine them if there are multiple copies
        part_counts: Dict[unrealsdk.UObject, int] = {}
        for slot in option.Parts:
            part = getattr(item.DefinitionData, slot)
            if part is None:
                continue
            if part in part_counts:
                part_counts[part] += 1
            else:
                part_counts[part] = 1

        if len(part_counts) < 1:
            return ""

        text = f"{option.Caption}: <font color='#FFDEAD'>"
        for part in part_counts:
            text += GetPartName(part, True)
            if part_counts[part] > 1:
                text += f" x{part_counts[part]}"

            # TODO: Stats?

            text += ", "
        # Remove the extra ", "
        return f"{text[:-2]} </font>\n"


instance = PythonPartNotifier()
if __name__ == "__main__":
    unrealsdk.Log(f"[{instance.Name}] Manually loaded")
    for mod in Mods:
        if mod.Name == instance.Name:
            if mod.IsEnabled:
                mod.Disable()
            Mods.remove(mod)
            unrealsdk.Log(f"[{instance.Name}] Removed last instance")

            # Fixes inspect.getfile()
            instance.__class__.__module__ = mod.__class__.__module__
            break
RegisterMod(instance)
