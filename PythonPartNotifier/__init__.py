import bl2sdk
import json
import os

import sys
sys.path.append("..")
from PythonPartNotifier import PartNamer

bl2sdk.Log("[PPN] Main file loaded")

# If __file__ is not defined temporarily define it as the empty string so this doesn't error
# It gets properly set later
try:
    fake_a = __file__
except:
    __file__ = ""

class PythonPartNotifier(bl2sdk.BL2MOD):
    # Use a short name so that the settings are readable
    Name = "PPN"
    Author = "apple1417"
    Description = (
        # Put the full name in the description
        "<font size='24' color='#FFDEAD'>Python Part Notifier</font>\n"
        "Lets you show all parts on your items and weapons, even if other mods have modified them.\n"
        "\n"
        "Make sure to check out the options menu to customize what exactly is shown."
    )
    Types = [bl2sdk.ModTypes.Utility]
    Version = "1.0"

    # A list to store options in the order they should appear, and a dict to map the option name
    #  to it's current value
    Options = []
    OptionsDict = {}

    BOOL_OPTIONS = (
        ("Detailed Part Names", "Should part names include the weapon and part type they're for rather than just the manufacturer.", False),
        ("Remove Descriptions", "Should the default descriptions be removed to create more space for the part descriptions.", False)
    )

    WEAPON_PARTS = (
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
    SHIELD_PARTS = (
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

    GRENADE_PARTS = (
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
    COM_PARTS = (
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
    ARTIFACT_PARTS = (
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
        ("Relic Extras", "MaterialItemPartDefinition", 1,
            "Should parts in slots that aren't normally used be shown if they contain a part."
        ),
    )
    # Map to turn the item class back into those above tables
    PARTS_MAP = {
        "WillowWeapon": WEAPON_PARTS,
        "WillowShield": SHIELD_PARTS,
        "WillowGrenadeMod": GRENADE_PARTS,
        "WillowClassMod": COM_PARTS,
        "WillowArtifact": ARTIFACT_PARTS
    }

    # List of options with headers
    ALL_OPTIONS = (
        ("Weapon Parts", WEAPON_PARTS),
        ("Shield Parts", SHIELD_PARTS),
        ("Grenade Parts", GRENADE_PARTS),
        ("Class Mod Parts", COM_PARTS),
        ("Relic Parts", ARTIFACT_PARTS)
    )

    IS_BL2 = True

    OPTIONS_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), "options.json")

    def __init__(self):
        # Hopefully I can remove this in a future SDK update
        self.Author += "\nVersion: " + str(self.Version)

        self.IS_BL2 = os.path.basename(sys.executable) == "Borderlands2.exe"

        savedOptions = {}
        if os.path.exists(self.OPTIONS_PATH):
            with open(self.OPTIONS_PATH) as file:
                savedOptions = json.load(file)

        for option in self.BOOL_OPTIONS:
            name = option[0]
            value = option[2]
            # Load option from file if it was set
            if name in savedOptions:
                value = savedOptions[name]
            descrip = option[1]

            self.Options.append(bl2sdk.Options.BooleanOption(
                Caption = name,
                Description = descrip,
                StartingValue = value
            ))
            self.OptionsDict[option[0]] = option[2]
        for optionCategory in self.ALL_OPTIONS:
            self.Options.append(bl2sdk.Options.SliderOption(
                Caption = self.translateTPS(optionCategory[0]),
                Description = "Category Header",
                StartingValue = 0,
                MinValue = 0,
                MaxValue = 0,
                Increment = 1
            ))
            for option in optionCategory[1]:
                name = option[0]
                value = option[2]
                # Load option from file if it was set
                if name in savedOptions:
                    value = savedOptions[name]
                # Check if we have a description override
                descrip = "Should the part be shown in the description or not."
                if len(option) == 4:
                    descrip = option[3]

                self.Options.append(bl2sdk.Options.SpinnerOption(
                    Caption =  self.translateTPS(name),
                    Description = descrip,
                    StartingChoiceIndex = value,
                    Choices = ["Hidden", "Shown"] # TODO: Stats
                ))
                self.OptionsDict[name] = value

    def ModOptionChanged(self, option, newValue):
        if option in self.Options:
            # Clean this up a bit for the settings file
            newValue = int(newValue)
            self.OptionsDict[option.Caption] = newValue

            # Would be better if we waited for you to close the settings window, but this is easy
            with open(self.OPTIONS_PATH, "w") as file:
                json.dump(self.OptionsDict, file, indent=4)

    # Add a key to reset all options when in the mod menu
    SettingsInputs = {
        "Enter": "Enable",
        "R": "Reset Options"
    }
    def SettingsInputPressed(self, name: str):
        if name == "Enable":
            self.Status = "Enabled"
            self.SettingsInputs = {
                "Enter": "Disable",
                "R": "Reset Options"
            }
            self.Enable()
        elif name == "Disable":
            self.Status = "Disabled"
            self.SettingsInputs = {
                "Enter": "Enable",
                "R": "Reset Options"
            }
            self.Disable()

        elif name == "Reset Options":
            if os.path.exists(self.OPTIONS_PATH):
                os.remove(self.OPTIONS_PATH)
            optionsListIndex = 0
            for option in self.BOOL_OPTIONS:
                self.OptionsDict[option[0]] = option[2]
                self.Options[optionsListIndex].CurrentValue = option[2]
                optionsListIndex += 1
            for optionCategory in self.ALL_OPTIONS:
                optionsListIndex += 1
                for option in optionCategory[1]:
                    self.OptionsDict[option[0]] = option[2]
                    self.Options[optionsListIndex].CurrentValue = option[2]
                    optionsListIndex += 1

    # The SDK doesn't support unicode yet (even though the game does), so some characters need to be
    #  replaced to keep everything readable
    UNICODE_REPLACEMENTS = (
        ("•", "*"), # The bullet point at the start of every line
    )

    # Some terms should be changed in TPS
    TPS_REPLACEMENTS = (
        ("Bandit", "Scav"),
        ("Bouncing Bonny", "Bouncing Bazza"),
        ("Relic", "Oz Kit")
    )
    def translateTPS(self, text):
        if not self.IS_BL2:
            for replacement in self.TPS_REPLACEMENTS:
                text = text.replace(replacement[0], replacement[1])
        return text

    blockSetFunStats = False

    def Enable(self):
        # Called whenever an item card is created
        def SetItemCardEx(caller: bl2sdk.UObject, function: bl2sdk.UFunction, params: bl2sdk.FStruct) -> bool:
            # If we don't actually have an item then there's no need to do anything special
            item = params.InventoryItem.ObjectPointer
            if item == None: return True

            # Get the default text and convert it as needed
            text = item.GenerateFunStatsText()
            if text == None or self.OptionsDict["Remove Descriptions"]:
                text = ""
            else:
                for replacement in self.UNICODE_REPLACEMENTS:
                    text = text.replace(replacement[0], replacement[1])

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
                    partText += self.handleSingleSlot(item, category)
                else:
                    partText += self.handleMultipleSlots(item, category)

            # If we're not adding anthing then we can let the normal function handle it
            if len(partText) == 0:
                return True

            text += self.translateTPS(partText)

            # This function is actually quite complex, so rather than replicate it we'll write out
            #  our text, then let the regular function run but block it from overwriting the text
            caller.SetFunStats(text)
            self.blockSetFunStats = True
            return True

        # Called to set the description on an item card
        # We just hook this so that we can occasionally block it
        def SetFunStats(caller: bl2sdk.UObject, function: bl2sdk.UFunction, params: bl2sdk.FStruct) -> bool:
            if self.blockSetFunStats:
                self.blockSetFunStats = False
            else:
                return True

        bl2sdk.RegisterHook("WillowGame.ItemCardGFxObject.SetFunStats", "PythonPartNotifier", SetFunStats)
        bl2sdk.RegisterHook("WillowGame.ItemCardGFxObject.SetItemCardEx", "PythonPartNotifier", SetItemCardEx)

        for option in self.Options:
            self.RegisterGameConfigOption(option)

    def Disable(self):
        bl2sdk.RemoveHook("WillowGame.ItemCardGFxObject.SetFunStats", "PythonPartNotifier")
        bl2sdk.RemoveHook("WillowGame.ItemCardGFxObject.SetItemCardEx", "PythonPartNotifier")

        for option in self.Options:
            self.UnregisterGameConfigOption(option)

    def handleSingleSlot(self, item, category):
        part = getattr(item.DefinitionData, category[1])
        if part == None:
            return ""

        trim = " ".join(category[0].split(" ")[1:])
        text = f"{trim}: <font color='#FFDEAD'>"
        text += PartNamer.getPartName(part, self.OptionsDict["Detailed Part Names"])
        text += "</font>"

        # TODO: Stats

        return text + "\n"

    def handleMultipleSlots(self, item, category):
        # Get a count of each part so we can combine them if there are multiple copies
        partCounts = {}
        for slot in category[1]:
            part = getattr(item.DefinitionData, slot)
            if part == None:
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
            text += PartNamer.getPartName(part, True)
            if partCounts[part] > 1:
                text += f" x{partCounts[part]}"

            # TODO: Stats?

            text += ", "
        # Remove the extra ", "
        return f"{text[:-2]} </font>\n"

instance = PythonPartNotifier()
if __name__ == "__main__":
    bl2sdk.Log("[PPN] Manually loaded")
    for mod in bl2sdk.Mods:
        if mod.Name == instance.Name:
            mod.Disable()
            bl2sdk.Mods.remove(mod)
            bl2sdk.Log("[PPN] Disabled and removed last instance")

            import importlib
            bl2sdk.Log("[PPN] Reloading other modules")
            importlib.reload(PartNamer)

            break
    else:
        bl2sdk.Log("[PPN] Could not find previous instance")

    # __file__ isn't set when you call this through a pyexec, so we have to do something real silly
    # If we cause an exception then the traceback will contain the file name, which we can regex out
    import re, traceback
    try:
        fake_b += 1
    except NameError as e:
        __file__ = re.search(r"File \"(.*?)\", line", traceback.format_exc()).group(1)
        bl2sdk.Log(f"[PPN] File path: {__file__}")

    bl2sdk.Log("[PPN] Auto-enabling")
    instance.Status = "Enabled"
    instance.SettingsInputs = {"Enter": "Disable"}
    instance.Enable()
bl2sdk.Mods.append(instance)
