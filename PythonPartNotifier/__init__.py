import unrealsdk
import argparse
import gzip
import json
import os
from collections import Counter
from dataclasses import dataclass
from types import ModuleType
from typing import Any, ClassVar
from typing import Counter as CounterType
from typing import Dict, Optional, Sequence, Tuple, Union

from Mods.ModMenu import (EnabledSaveType, Game, Hook, Mods, ModTypes, Options, RegisterMod,
                          SaveModSettings, SDKMod)
from Mods.PythonPartNotifier.PartNamer import legacy_get_part_name

CommandExtensions: Optional[ModuleType]
try:
    from Mods import CommandExtensions
    from Mods.CommandExtensions.builtins import parse_object
except ImportError:
    CommandExtensions = None

if unrealsdk.GetVersion() < (0, 7, 9):
    # To get here someone'll need to have a newer mod menu with an older sdk
    # Hardly worth supporting this so just throw a warning and let them deal with it.
    unrealsdk.Log(
        "[PythonPartNotifier] Warning: You're using an old SDK version, which doesn't support"
        " unicode. Some item card text will get garbled. Update the SDK to prevent this."
    )

if __name__ == "__main__":
    # See https://github.com/bl-sdk/PythonSDK/issues/68
    import sys
    try:
        raise NotImplementedError
    except NotImplementedError:
        __file__ = sys.exc_info()[-1].tb_frame.f_code.co_filename  # type: ignore

JSON = Dict[str, Any]

EMPHASIS_COLOUR: str = "#FFDEAD"
ELEMENT_COLOUR_REPLACEMENTS: Dict[str, str] = {
    "Fire": "<font color='#F57500'>Fire</font>",
    "Shock": "<font color='#00BDF3'>Shock</font>",
    "Corrosive": "<font color='#79DC3D'>Corrosive</font>",
    "Slag": "<font color='#9B00DE'>Slag</font>",
    "Cryo": "<font color='#00FFFF'>Cryo</font>",
    "Explosive": "<font color='#F1D300'>Explosive</font>",
}
RARITY_COLOUR_REPLACEMENTS: Dict[str, str] = {
    "Common": "<font color='#ffffff'>Common</font>",
    "Uncommon": "<font color='#3dd201'>Uncommon</font>",
    # Include the bracket to not match `Very Rare`
    "(Rare": "(<font color='#3c8eff'>Rare</font>",
    "Very Rare": "<font color='#a83fe5'>Very Rare</font>",
}

# Some terms should be changed in TPS
TPS_TYPE_REPLACEMENTS: Dict[str, str] = {
    "Relic": "Oz Kit",
}
# The legacy parser needs to replace a few extra things
LEGACY_TPS_REPLACEMENTS: Dict[str, str] = {
    **TPS_TYPE_REPLACEMENTS,
    "Bandit": "Scav",
    "Bouncing Bonny": "Bouncing Bazza",
}

PART_NAMES_FILE: str = os.path.join(os.path.dirname(__file__), "part_names.json.gz")
PART_NAMES: JSON = {}
try:
    with gzip.open(PART_NAMES_FILE, "rt", encoding="utf8") as file:
        PART_NAMES = json.load(file)
except (OSError, json.JSONDecodeError):
    pass


def apply_replacements(text: str, replacements: Dict[str, str]) -> str:
    """
    Given a dict of terms to replacements, apply all replacements to the given text.

    Args:
        text: The text to edit.
    Returns:
        The given text with TPS terms replaced.
    """
    for term, replacement in replacements.items():
        text = text.replace(term, replacement)
    return text


def get_single_part_name(part: unrealsdk.UObject, show_slot: bool, show_type: bool) -> str:
    """
    Gets the name of a single part object.

    Args:
        part: The part to name.
        show_slot: If to show the slot the part is intended for.
        show_type: If to show the item type the part is intended for.
    Returns:
        The part's name.
    """
    obj_name = part.PathName(part)
    if obj_name in PART_NAMES:
        part_info = PART_NAMES[obj_name]

        name: str = part_info["name"]
        slot: str = part_info["slot"]
        item_type: str = part_info["type"]

        try:
            name = part_info["game_overrides"][Game.GetCurrent().name]
        except KeyError:
            pass

        name = apply_replacements(name, ELEMENT_COLOUR_REPLACEMENTS)
        name = apply_replacements(name, RARITY_COLOUR_REPLACEMENTS)
        if Game.GetCurrent() == Game.TPS:
            item_type = apply_replacements(item_type, TPS_TYPE_REPLACEMENTS)

        output = name
        if show_type:
            output += " " + item_type
        if show_slot:
            output += " " + slot
        return output
    else:
        # Will eventually get replaced with just `return part.Name`, once the list is more complete
        output = legacy_get_part_name(part, show_slot, show_type)
        if Game.GetCurrent() == Game.TPS:
            output = apply_replacements(output, LEGACY_TPS_REPLACEMENTS)
        return output


class PartOption(Options.Boolean):
    """
    Custom boolean option for determining what part slots to show.

    Attributes:
        Slots: The part slots this option controls.
    """
    Slots: Tuple[str, ...]

    def __init__(
        self,
        Caption: str,
        StartingValue: bool,
        Slots: Tuple[str, ...],
        Description: str = "Should the part be shown in the description or not."
    ):
        super().__init__(Caption, Description, StartingValue)
        self.Slots = Slots

    def name_item_parts(self, item: unrealsdk.UObject, show_slot: bool, show_type: bool) -> str:
        """
        Names all parts covered by this option on the given item.

        Args:
            item: The item to look for parts on.
            show_slot: If to show the slot the part is intended for.
            show_type: If to show the item type the part is intended for.
        Returns:
            A string containing all found part names, or an empty string if none were found.
        """
        # Get a count of each part so we can combine them if there are multiple copies
        part_counts: CounterType[unrealsdk.UObject] = Counter()
        for slot in self.Slots:
            part = getattr(item.DefinitionData, slot)
            if part is None:
                continue
            part_counts[part] += 1

        if len(part_counts) < 1:
            return ""

        text = f"{self.Caption}: <font color='{EMPHASIS_COLOUR}'>"
        first = True
        for part in part_counts:
            if not first:
                text += ", "
            first = True

            text += get_single_part_name(part, show_slot, show_type)
            if part_counts[part] > 1:
                text += f" x{part_counts[part]}"

        text += "</font>\n"
        return text


class ItemClassOption(Options.Nested):
    """
    Custom nested option for specific item classes.

    Attributes:
        ItemClass: The item class this option controls
    """
    Children: Sequence[PartOption]
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


@dataclass
class GameOverride:
    """
    Dataclass to store game overrides, for when adding new names via command extensions.

    Attributes:
        game: The game this override is for.
        name: The name to use if this override applies.
    """
    game: Game
    name: str


class GameOverrideAction(argparse.Action):
    """
    Custom Action which parses a game-name pair into a `GameOverride` object. Acts like the default
     append action otherwise.
    """

    LOWER_GAME_MAP: ClassVar[Dict[str, Game]] = {
        "bl2": Game.BL2,
        "tps": Game.TPS,
        "aodk": Game.AoDK,
    }

    # Argparse uses two different formats for these and now that I know I hate it
    GAME_CHOICES_METAVAR: ClassVar[str] = "{" + ",".join(map(str, Game._member_map_.keys())) + "}"
    GAME_CHOICES_ERR: ClassVar[str] = ", ".join(map(repr, Game._member_map_.keys()))

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: Union[str, Sequence[Any], None],
        option_string: Optional[str] = None
    ) -> None:
        game_str, override = values  # type: ignore
        game = GameOverrideAction.LOWER_GAME_MAP.get(game_str.lower(), None)
        if game is None:
            raise argparse.ArgumentError(
                self,
                f"invalid choice: {game_str!r} (choose from {GameOverrideAction.GAME_CHOICES_ERR})"
            )

        items = getattr(namespace, self.dest, None)
        if items is None:
            items = []
            setattr(namespace, self.dest, items)
        items.append(GameOverride(game, override))


def name_part_handler(args: argparse.Namespace) -> None:
    """
    Handles `name_part` command invokations.

    Args:
        args: The passed command line arguments.
    """
    part = parse_object(args.part)
    if part is None:
        return
    part_name = part.PathName(part)

    if args.delete:
        if args.dry_run:
            unrealsdk.Log(f"Would delete name for {part_name!r}")
            return

        try:
            del PART_NAMES[part.PathName(part)]
        except KeyError:
            unrealsdk.Log(f"{part_name!r} already did not have a name assigned to it!")
        return

    part_info = {
        "name": args.name,
        "slot": args.slot,
        "type": args.type,
    }

    if args.game_override:
        game_overrides: Dict[str, str] = {}
        for override in args.game_override:
            game_overrides[override.game.name] = override.name
        part_info["game_overrides"] = game_overrides

    if args.dry_run:
        unrealsdk.Log(json.dumps(part_info, indent=4, sort_keys=True))
    else:
        PART_NAMES[part_name] = part_info


def register_name_part() -> None:
    """ Registers the `name_part` console command, if Command Extensions is available. """
    if CommandExtensions is None:
        return

    parser = CommandExtensions.RegisterConsoleCommand(
        "name_part",
        name_part_handler,
        description=(
            "Sets the name used for the given part. Note that this command is very sensitive to"
            " punctuation, best to quote all args."
        )
    )
    parser.add_argument("part", help="The part to set the name of. Must be quoted.")
    parser.add_argument("name", help="The part's name.")
    parser.add_argument("type", help="The item type the part is intended for.")
    parser.add_argument("slot", help="The slot the part is intended to go into.")
    parser.add_argument(
        "-g", "--game-override",
        nargs=2, action=GameOverrideAction,
        metavar=(GameOverrideAction.GAME_CHOICES_METAVAR, "NAME"),
        help="Set game-specific part name overrides. May be used multiple times."
    )
    parser.add_argument(
        "-d", "--delete",
        action="store_true",
        help=(
            "Delete the stored name for the given part instead. You must still specify dummy names"
            " for the command to get parsed."
        )
    )
    parser.add_argument(
        "-y", "--dry-run",
        action="store_true",
        help=(
            "Don't modify anything, just print what the command would set the name to. Useful to"
            " check it's being parsed as expected."
        )
    )


def unregister_name_part() -> None:
    """ Unregisters the `name_part` console command, if Command Extensions is available. """
    if CommandExtensions is None:
        return
    CommandExtensions.UnregisterConsoleCommand("name_part")


class PythonPartNotifier(SDKMod):
    Name: str = "Python Part Notifier"
    Author: str = "apple1417"
    Description: str = (
        "Lets you show all parts on your items and weapons, even if other mods have modified them.\n"
        "\n"
        "Make sure to check out the options menu to customize what exactly is shown."
    )
    Version: str = "1.8"

    Types: ModTypes = ModTypes.Utility
    SaveEnabledState: EnabledSaveType = EnabledSaveType.LoadWithSettings

    SettingsInputs: Dict[str, str] = {
        "Enter": "Enable",
        "R": "Reset Options"
    }

    SlotOption: Options.Boolean
    TypeOption: Options.Boolean
    FontSizeOption: Options.Slider
    RemoveOption: Options.Boolean

    def __init__(self) -> None:
        self.SetDefaultOptions()

    def SettingsInputPressed(self, action: str) -> None:
        if action == "Reset Options":
            self.SetDefaultOptions()
            SaveModSettings(self)
        else:
            super().SettingsInputPressed(action)

    def SetDefaultOptions(self) -> None:
        """ Sets the options array to use new options all at defaults. """
        self.TypeOption = Options.Boolean(
            "Include Item Type",
            "Should part names include the item type they're intended for.",
            False
        )
        self.SlotOption = Options.Boolean(
            "Include Part Slots",
            "Should part names include the slot they're intended for.",
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
            self.TypeOption,
            self.SlotOption,
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
                    PartOption("Definition", False, ("WeaponTypeDefinition",))
                ),
            ),
            ItemClassOption(
                "Shields", "WillowShield", (
                    PartOption("Accessory", False, ("DeltaItemPartDefinition",)),
                    PartOption("Battery", True, ("BetaItemPartDefinition",)),
                    PartOption("Body", True, ("AlphaItemPartDefinition",)),
                    PartOption("Capacitor", True, ("GammaItemPartDefinition",)),
                    PartOption("Material", False, ("MaterialItemPartDefinition",)),
                    PartOption("Definition", False, ("ItemDefinition",)),
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
                    PartOption("Definition", False, ("ItemDefinition",))
                )
            ),
            ItemClassOption(
                "Class Mods", "WillowClassMod", (
                    PartOption("Specialization", True, ("AlphaItemPartDefinition",)),
                    PartOption("Primary", True, ("BetaItemPartDefinition",)),
                    PartOption("Secondary", True, ("GammaItemPartDefinition",)),
                    PartOption("Penalty", True, ("MaterialItemPartDefinition",)),
                    PartOption("Definition", False, ("ItemDefinition",)),
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
                    PartOption("Definition", False, ("ItemDefinition",)),
                    PartOption("Extras", True, (
                        "MaterialItemPartDefinition",
                    ), "Should parts in slots that aren't normally used be shown if they contain a part.")
                ), IsHidden=Game.GetCurrent() == Game.TPS
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
                    PartOption("Definition", False, ("ItemDefinition",)),
                    PartOption("Extras", True, (
                        "MaterialItemPartDefinition",
                    ), "Should parts in slots that aren't normally used be shown if they contain a part.")
                ), IsHidden=Game.GetCurrent() != Game.TPS
            )
        ]

    @Hook("WillowGame.ItemCardGFxObject.SetItemCardEx")
    def SetItemCardEx(self, caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
        """
        This function is called whenever an item card is created - exactly when we need to add
        all the parts text.
        """

        # If we don't actually have an item then there's no need to do anything special
        item = params.InventoryItem.ObjectPointer
        if item is None:
            return True

        part_text = ""
        for option in self.Options:
            if not isinstance(option, ItemClassOption):
                continue
            if option.ItemClass != item.Class.Name:
                continue

            for child_option in option.Children:
                if not child_option.CurrentValue:
                    continue
                part_text += child_option.name_item_parts(
                    item,
                    self.SlotOption.CurrentValue,
                    self.TypeOption.CurrentValue
                )
            break
        # No matching item class found
        else:
            return True

        # If we're not adding anthing then we can let the normal function handle it
        if len(part_text) == 0:
            return True

        # Get the default text and convert it as needed
        text = "" if self.RemoveOption.CurrentValue else item.GenerateFunStatsText()

        text += f"<font size=\"{self.FontSizeOption.CurrentValue}\" color=\"#FFFFFF\">"
        text += part_text
        text += "</font>"

        # `SetItemCardEx` is actually quite complex, so rather than replicate it, we'll just
        #  write our text, then let the it run as normal, but block it from overwriting the text
        def SetFunStats(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            unrealsdk.RemoveHook("WillowGame.ItemCardGFxObject.SetFunStats", __file__)
            return False

        unrealsdk.RegisterHook("WillowGame.ItemCardGFxObject.SetFunStats", __file__, SetFunStats)

        caller.SetFunStats(text)

        return True

    def Enable(self) -> None:
        register_name_part()
        return super().Enable()

    def Disable(self) -> None:
        unregister_name_part()
        return super().Disable()


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
