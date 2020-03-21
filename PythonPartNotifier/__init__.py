import unrealsdk
from Mods.SaveManager import storeModSettings  # type: ignore
from typing import Any, cast, ClassVar, Dict, List, Tuple, Union

from Mods.PythonPartNotifier.PartNamer import GetPartName  # noqa
from Mods import AAA_OptionsWrapper as OptionsWrapper

OptionDescription = Tuple[Union[
    Tuple[str, Union[str, Tuple[str, ...]], int],
    Tuple[str, Union[str, Tuple[str, ...]], int, str]
], ...]


class PythonPartNotifier(unrealsdk.BL2MOD):
    # Use a short name so that the settings are readable
    Name: ClassVar[str] = "PPN"
    Author: ClassVar[str] = "apple1417"
    Description: ClassVar[str] = (
        # Put the full name in the description
        "<font size='24' color='#FFDEAD'>Python Part Notifier</font>\n"
        "Lets you show all parts on your items and weapons, even if other mods have modified them.\n"
        "\n"
        "Make sure to check out the options menu to customize what exactly is shown."
    )
    Types: ClassVar[List[unrealsdk.ModTypes]] = [unrealsdk.ModTypes.Utility]
    Version: ClassVar[str] = "1.2"

    Options: List[OptionsWrapper.Base]
    OptionsDict: Dict[str, Union[int, bool]]

    BOOL_OPTIONS: ClassVar[Tuple[Tuple[str, str, bool], ...]] = (
        ("Detailed Part Names", "Should part names include the weapon and part type they're for rather than just the manufacturer.", False),
        ("Remove Descriptions", "Should the default descriptions be removed to create more space for the part descriptions.", False)
    )

    WEAPON_PARTS: ClassVar[OptionDescription] = (
        # Name, Attribute, Default Option Value, Custom Description
        ("Weapon Accessory", "Accessory1PartDefinition", 1),
        ("Weapon 2nd Accessory", "Accessory2PartDefinition", 0),
        ("Weapon Barrel", "BarrelPartDefinition", 1),
        ("Weapon Body", "BodyPartDefinition", 0),
        ("Weapon Element", "ElementalPartDefinition", 0),
        ("Weapon Grip", "GripPartDefinition", 1),
        ("Weapon Material", "MaterialPartDefinition", 0),
        ("Weapon Sight", "SightPartDefinition", 1),
        ("Weapon Stock", "StockPartDefinition", 1),
        ("Weapon Type", "WeaponTypeDefinition", 0)
    )
    SHIELD_PARTS: ClassVar[OptionDescription] = (
        ("Shield Accessory", "DeltaItemPartDefinition", 0),
        ("Shield Battery", "BetaItemPartDefinition", 1),
        ("Shield Body", "AlphaItemPartDefinition", 1),
        ("Shield Capacitor", "GammaItemPartDefinition", 1),
        ("Shield Material", "MaterialItemPartDefinition", 0),
        ("Shield Type", "ItemDefinition", 0),
        ("Shield Extras", (
            "EpsilonItemPartDefinition",
            "ZetaItemPartDefinition",
            "EtaItemPartDefinition",
            "ThetaItemPartDefinition"
        ), 1, "Should parts in slots that aren't normally used be shown if they contain a part.")
    )

    GRENADE_PARTS: ClassVar[OptionDescription] = (
        ("Grenade Accessory", "DeltaItemPartDefinition", 0),
        ("Grenade Blast Radius", "ZetaItemPartDefinition", 1),
        ("Grenade Child Count", "EtaItemPartDefinition", 1),
        ("Grenade Damage", "EpsilonItemPartDefinition", 0),
        ("Grenade Delivery", "BetaItemPartDefinition", 1),
        ("Grenade Material", "MaterialItemPartDefinition", 0),
        ("Grenade Payload", "AlphaItemPartDefinition", 0),
        ("Grenade Status Damage", "ThetaItemPartDefinition", 0),
        ("Grenade Trigger", "GammaItemPartDefinition", 1),
        ("Grenade Type", "ItemDefinition", 0)
    )
    COM_PARTS: ClassVar[OptionDescription] = (
        ("COM Specialization", "AlphaItemPartDefinition", 1),
        ("COM Primary", "BetaItemPartDefinition", 1),
        ("COM Secondary", "GammaItemPartDefinition", 1),
        ("COM Penalty", "MaterialItemPartDefinition", 1),
        ("COM Type", "ItemDefinition", 0),
        ("COM Extras", (
            "DeltaItemPartDefinition",
            "EpsilonItemPartDefinition",
            "ZetaItemPartDefinition",
            "EtaItemPartDefinition",
            "ThetaItemPartDefinition"
        ), 1, "Should parts in slots that aren't normally used be shown if they contain a part.")
    )
    ARTIFACT_PARTS: ClassVar[OptionDescription] = (
        ("Relic Body", "EtaItemPartDefinition", 0),
        ("Relic Upgrade", "ThetaItemPartDefinition", 1),
        # These are the various relic enable effect parts
        # There isn't really a pattern to them so go with the slot name
        ("Relic Alpha", "AlphaItemPartDefinition", 0),
        ("Relic Beta", "BetaItemPartDefinition", 0),
        ("Relic Gamma", "GammaItemPartDefinition", 0),
        ("Relic Delta", "DeltaItemPartDefinition", 0),
        ("Relic Epsilon", "EpsilonItemPartDefinition", 0),
        ("Relic Zeta", "ZetaItemPartDefinition", 0),
        ("Relic Type", "ItemDefinition", 0),
        (
            "Relic Extras",
            "MaterialItemPartDefinition",
            1,
            "Should parts in slots that aren't normally used be shown if they contain a part."
        )
    )
    # Map to turn the item class back into those above tables
    PARTS_MAP: Dict[str, OptionDescription] = {
        "WillowWeapon": WEAPON_PARTS,
        "WillowShield": SHIELD_PARTS,
        "WillowGrenadeMod": GRENADE_PARTS,
        "WillowClassMod": COM_PARTS,
        "WillowArtifact": ARTIFACT_PARTS
    }

    # List of options with headers
    ALL_OPTIONS: Tuple[Tuple[str, OptionDescription], ...] = (
        ("Weapon Parts", WEAPON_PARTS),
        ("Shield Parts", SHIELD_PARTS),
        ("Grenade Parts", GRENADE_PARTS),
        ("Class Mod Parts", COM_PARTS),
        ("Relic Parts", ARTIFACT_PARTS),
        ("Oz Kit Parts", ARTIFACT_PARTS)
    )

    IS_BL2: ClassVar[bool] = unrealsdk.GetEngine().GetEngineVersion() == 8639

    def __init__(self) -> None:
        # Hopefully I can remove this in a future SDK update
        self.Author += "\nVersion: " + str(self.Version)  # type: ignore

        self.SetDefaultOptions()

    def SetDefaultOptions(self) -> None:
        self.Options = []
        self.OptionsDict = {}

        for boolOption in self.BOOL_OPTIONS:
            name = boolOption[0]
            boolValue = boolOption[2]
            descrip = boolOption[1]

            self.Options.append(OptionsWrapper.Boolean(
                Caption=name,
                Description=descrip,
                StartingValue=boolValue
            ))
            self.OptionsDict[boolOption[0]] = boolOption[2]

        for optionCategory in self.ALL_OPTIONS:
            relics = optionCategory[0] == "Relic Parts"
            ozKits = optionCategory[0] == "Oz Kit Parts"
            hidden = (relics and not self.IS_BL2) or (ozKits and self.IS_BL2)

            self.Options.append(OptionsWrapper.Slider(
                Caption=optionCategory[0],
                Description="Category Header",
                StartingValue=0,
                MinValue=0,
                MaxValue=0,
                Increment=1,
                IsHidden=hidden
            ))

            for option in optionCategory[1]:
                name = option[0]
                value = int(option[2])

                if ozKits:
                    name = self.translateTPS(name, True)

                # Check if we have a description override
                descrip = "Should the part be shown in the description or not."
                if len(option) == 4:
                    descrip = cast(Tuple[str, str, int, str], option)[3]

                self.Options.append(OptionsWrapper.Spinner(
                    Caption=name,
                    Description=descrip,
                    StartingChoice=["Hidden", "Shown"][value],
                    Choices=["Hidden", "Shown"],
                    IsHidden=hidden
                ))
                self.OptionsDict[name] = value

    def ModOptionChanged(
        self,
        option: OptionsWrapper.Base,
        newValue: Any
    ) -> None:
        if option in self.Options:
            if isinstance(option, OptionsWrapper.Spinner):
                self.OptionsDict[option.Caption] = option.Choices.index(newValue)
            elif isinstance(option, OptionsWrapper.Boolean):
                self.OptionsDict[option.Caption] = cast(bool, newValue)

    # Add a key to reset all options when in the mod menu
    SettingsInputs: Dict[str, str] = {
        "Enter": "Enable",
        "R": "Reset Options"
    }

    def SettingsInputPressed(self, name: str) -> None:
        if name == "Enable":
            self.Status = "Enabled"
            self.SettingsInputs["Enter"] = "Disable"
            self.Enable()
        elif name == "Disable":
            self.Status = "Disabled"
            self.SettingsInputs["Enter"] = "Enable"
            self.Disable()

        elif name == "Reset Options":
            self.SetDefaultOptions()
            storeModSettings()

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

    def translateTPS(self, text: str, force: bool = False) -> str:
        if force or not self.IS_BL2:
            for rep in self.TPS_REPLACEMENTS:
                text = text.replace(rep, self.TPS_REPLACEMENTS[rep])
        return text

    _blockSetFunStats: bool = False

    def Enable(self) -> None:
        # Called whenever an item card is created
        def SetItemCardEx(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            # If we don't actually have an item then there's no need to do anything special
            item = params.InventoryItem.ObjectPointer
            if item is None:
                return True

            # Get the default text and convert it as needed
            text = item.GenerateFunStatsText()
            if text is None or self.OptionsDict["Remove Descriptions"]:
                text = ""
            else:
                for rep in self.UNICODE_REPLACEMENTS:
                    text = text.replace(rep, self.UNICODE_REPLACEMENTS[rep])

            # Based off of item class we need to look at different parts
            clas = str(item).split(" ")[0]
            if clas not in self.PARTS_MAP:
                return True

            partText = ""
            for category in self.PARTS_MAP[clas]:
                # If the category is hidden skip it
                if self.OptionsDict[category[0]] == 0:
                    continue

                if type(category[1]) == str:
                    partText += self.handleSingleSlot(item, cast(Tuple[str, str, int], category))
                else:
                    partText += self.handleMultipleSlots(item, cast(Tuple[str, List[str], int], category))

            # If we're not adding anthing then we can let the normal function handle it
            if len(partText) == 0:
                return True

            text += self.translateTPS(partText)

            # This function is actually quite complex, so rather than replicate it we'll write out
            #  our text, then let the regular function run but block it from overwriting the text
            caller.SetFunStats(text)
            self._blockSetFunStats = True
            return True

        # Called to set the description on an item card
        # We just hook this so that we can occasionally block it
        def SetFunStats(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            if self._blockSetFunStats:
                self._blockSetFunStats = False
                return False
            return True

        unrealsdk.RegisterHook("WillowGame.ItemCardGFxObject.SetFunStats", "PythonPartNotifier", SetFunStats)
        unrealsdk.RegisterHook("WillowGame.ItemCardGFxObject.SetItemCardEx", "PythonPartNotifier", SetItemCardEx)

    def Disable(self) -> None:
        unrealsdk.RemoveHook("WillowGame.ItemCardGFxObject.SetFunStats", "PythonPartNotifier")
        unrealsdk.RemoveHook("WillowGame.ItemCardGFxObject.SetItemCardEx", "PythonPartNotifier")

    def handleSingleSlot(self, item: unrealsdk.UObject, category: Tuple[str, str, int]) -> str:
        part = getattr(item.DefinitionData, category[1])
        if part is None:
            return ""

        trim = " ".join(category[0].split(" ")[1:])
        text = f"{trim}: <font color='#FFDEAD'>"
        text += GetPartName(part, cast(bool, self.OptionsDict["Detailed Part Names"]))
        text += "</font>"

        # TODO: Stats

        return text + "\n"

    def handleMultipleSlots(self, item: unrealsdk.UObject, category: Tuple[str, List[str], int]) -> str:
        # Get a count of each part so we can combine them if there are multiple copies
        partCounts: Dict[unrealsdk.UObject, int] = {}
        for slot in category[1]:
            part = getattr(item.DefinitionData, slot)
            if part is None:
                continue
            if part in partCounts:
                partCounts[part] += 1
            else:
                partCounts[part] = 1

        if len(partCounts) < 1:
            return ""

        trim = " ".join(category[0].split(" ")[1:])
        text = f"{trim}: <font color='#FFDEAD'>"
        for part in partCounts:
            text += GetPartName(part, True)
            if partCounts[part] > 1:
                text += f" x{partCounts[part]}"

            # TODO: Stats?

            text += ", "
        # Remove the extra ", "
        return f"{text[:-2]} </font>\n"


instance = PythonPartNotifier()
if __name__ != "__main__":
    unrealsdk.RegisterMod(instance)
else:
    unrealsdk.Log(f"[{instance.Name}] Manually loaded")
    for i in range(len(unrealsdk.Mods)):
        mod = unrealsdk.Mods[i]
        if unrealsdk.Mods[i].Name == instance.Name:
            unrealsdk.Mods[i].Disable()

            unrealsdk.RegisterMod(instance)
            unrealsdk.Mods.remove(instance)
            unrealsdk.Mods[i] = instance
            unrealsdk.Log(f"[{instance.Name}] Disabled and removed last instance")
            break
    else:
        unrealsdk.Log(f"[{instance.Name}] Could not find previous instance")
        unrealsdk.RegisterMod(instance)

    unrealsdk.Log(f"[{instance.Name}] Auto-enabling")
    instance.Status = "Enabled"
    instance.SettingsInputs["Enter"] = "Disable"
    instance.Enable()
