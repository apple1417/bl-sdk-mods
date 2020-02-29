import unrealsdk
from typing import cast, Dict, Optional, Tuple


# Easier to split out the different item types to different functions
def GetPartName(part: unrealsdk.UObject, full: bool = False) -> str:
    name = str(part)
    if name.startswith("Weapon"):
        return _getWeaponPartName(part, full)
    elif name.startswith("Shield"):
        return _getShieldPartName(part, full)
    elif name.startswith("GrenadeMod"):
        return _getGrenadePartName(part, full)
    elif name.startswith("ClassMod"):
        return _getCOMPartName(part, full)
    elif name.startswith("Artifact"):
        return _getArtifactPartName(part, full)

    return str(part.Name)


# Little helper function that looks for elements in a string and returns a coloured representation
#  if it finds one
def _getElement(string: str) -> Optional[str]:
    string = string.lower()
    if "fire" in string or "incendiary" in string:
        return "<font color='#F57500'>Fire</font>"
    elif "shock" in string:
        return "<font color='#00BDF3'>Shock</font>"
    elif "corrosive" in string:
        return "<font color='#79DC3D'>Corrosive</font>"
    elif "slag" in string:
        return "<font color='#9B00DE'>Slag</font>"
    elif "ice" in string or "cryo" in string:
        return "<font color='#00FFFF'>Cryo</font>"
    elif "explosive" in string:
        return "<font color='#F1D300'>Explosive</font>"
    elif "none" in string:
        return "None"
    return None


def _getWeaponPartName(part: unrealsdk.UObject, full: bool) -> str:
    # Check through meshes first, which will eliminate most parts
    mesh = part.GestaltModeSkeletalMeshName
    if mesh in WEAP_MESH_NAMES and part.bIsGestaltMode:
        return WEAP_MESH_NAMES[mesh][0] + (f" {WEAP_MESH_NAMES[mesh][1]}" if full else "")
    # We can seperate some shared meshes through another table
    if part.Name in WEAP_OBJ_NAMES:
        return WEAP_OBJ_NAMES[part.Name][0] + (f" {WEAP_OBJ_NAMES[part.Name][1]}" if full else "")

    name = str(part).lower()
    # Messy way to find what weapon type this part belongs to
    weapType = ""
    if "assaultrifle" in name:
        weapType = "AR"
    elif "pistol" in name:
        weapType = "Pistol"
    elif "launcher" in name:
        weapType = "RL"
    elif "laser" in name:
        weapType = "Laser"
    elif "shotgun" in name:
        weapType = "SG"
    elif "smg" in name:
        weapType = "SMG"
    elif "sniperrifle" in name:
        weapType = "SR"
    # This might seem weird but it works out
    elif "moonstone" in name:
        weapType = "Moonstone"

    manufacturer = ""
    # Messy way to find what manufacturer this part has
    if "alien" in name:
        manufacturer = "ETech"
    elif "bandit" in name or "Scav" in name:
        manufacturer = "Bandit"
    elif "dahl" in name:
        manufacturer = "Dahl"
    elif "hyperion" in name:
        manufacturer = "Hyperion"
    elif "jakobs" in name:
        manufacturer = "Jakobs"
    elif "maliwan" in name:
        manufacturer = "Maliwan"
    elif "tediore" in name:
        manufacturer = "Tediore"
    elif "torgue" in name:
        manufacturer = "Torgue"
    elif "vladof" in name:
        manufacturer = "Vladof"

    # The 'No Accessory', 'No Sight', and 'No Element' parts don't expand well in the normal format
    if ("accessory" in name or "accessories" in name) and "none" in name:
        if full:
            # This here is why moonstone is a valid weapon type
            return f"'No Accessory' {weapType} Accessory"
        else:
            return "None"
    elif "sight" in name and "none" in name:
        if full:
            return f"'No Sight' {weapType} Sight"
        else:
            return "None"
    # Element parts share a lot of meshes so it's easier to seperate them here
    elif "element" in name:
        element = _getElement(name)
        if element is None and "egun" in name:
            element = "EGun"
        elif full and element == "None":
            return f"'No Element' {weapType} Element"
        else:
            return cast(str, element) + (f" {weapType} Element" if full else "")
    # Glitch attachment parts share meshes again
    elif "glitch_attachment" in name:
        # Get the full proper name
        splitName = part.PathName(part).split(".")[-1].split("_")
        if len(splitName) == 3:
            return f"{splitName[2]} Glitch" + (f" Attachment" if full else "")
        return f"Glitch Attachment"
    # Types don't really fit as a normal part, need their own processing too
    elif name.startswith("weapontypedefinition"):
        return f"{manufacturer} {weapType}" + (" Weapon Type" if full else "")

    # For everything else (materials) just return the object name
    return str(part.Name)


def _getShieldPartName(part: unrealsdk.UObject, full: bool) -> str:
    # Despite widely different base packages, the 2nd last ones are mostly the sam
    partType = part.Outer.Name
    name = part.Name
    nameSplit = name.split("_")

    # Unfortantly there are a few DLC parts that need this
    if name in SHIELD_PART_TYPE_OVERRIDES:
        partType = SHIELD_PART_TYPE_OVERRIDES[name]

    # All of these can be done the same way
    if partType in ("Accessory", "Battery", "Body", "Capacitor"):
        # Try work out the manufacturer from the mesh
        mesh = part.GestaltModeSkeletalMeshName

        if mesh in SHIELD_MESH_NAMES:
            return SHIELD_MESH_NAMES[mesh] + (f" Shield {partType}" if full else "")

        text = ""
        # Want to add Nova/Spike to the Torgue accessories
        if mesh == "Shield_Body_Torgue":
            text = "Torgue"
            # This will always return the same thing but it's better to keep formatting in one place
            element = _getElement(name)
            if element is not None and element != "None":
                text += f" {element}"
            if "Nova" in name:
                text += " Nova"
            elif "Spike" in name:
                text += " Spike"
        # Maliwan and Anshin accessories share a model
        elif mesh == "Shield_Body_Anshin":
            if "Chimera" in name or name == "Orchid_Seraph_Anshin_Shield_Accessory":
                text = "Anshin"
            else:
                text = "Maliwan"
                element = _getElement(name)
                if element is not None and element != "None":
                    text += f" {element}"
                if "Nova" in name:
                    text += " Nova"
                elif "Spike" in name:
                    text += " Spike"
        # Small workaround for anshin roid parts
        elif "Anshin" in mesh:
            text = "Anshin"
        # Maliwan and Pangolin batteries share a model
        elif mesh == "Shield_Battery_Pangolin":
            if name == "Battery5_Maliwan":
                text = "Maliwan"
            elif name == "Battery8_Pangolin":
                text = "Pangolin"
        # Maliwan and Torgue capacitors both share a (non-existant) model, and have elements
        elif mesh == "Shield_Pickup_A-1":
            text = nameSplit[1]
            element = _getElement(name)
            if element != "":
                text += f" {element} Res"

        if text != "":
            # Anshin Battery, Body and Capacitor have these "Roid" variants used in a few spots
            if text == "Anshin" and "RoidLegendary" in name:
                text += " Roid"

            return text + (f" Shield {partType}" if full else "")

    elif str(part).startswith("ShieldDefinition"):
        # A few DLC parts don't follow the pattern
        if name in SHIELD_TYPE_OVERRIDES:
            return SHIELD_TYPE_OVERRIDES[name] + (" Shield Type" if full else "")

        # This works suprisngly well
        text = nameSplit[1]
        # Just need to translate a few terms
        if text == "Chimera":
            text = "Adaptive"
        elif text == "Impact":
            text = "Amp"
        elif text == "Juggernaut":
            text = "Turtle"

        # Add the element if applicable
        if text == "Nova" or text == "Spike":
            element = _getElement(name)
            if not element == "":
                text = f"{element} {text}"

        return text + (" Shield Type" if full else "")

    return str(part.Name)


def _getGrenadePartName(part: unrealsdk.UObject, full: bool) -> str:
    # Grenade parts split up nicely just like shield ones
    partType = part.Outer.Name
    name = part.Name
    nameSplit = name.split("_")

    if name in GRENADE_PART_TYPE_OVERRIDES:
        partType = GRENADE_PART_TYPE_OVERRIDES[name]

    if partType == "Accessory":
        element = _getElement(name)
        if element is None or element == "None":
            element = "Non-Elemental"

        # These accessories only have one grade, no need to show "Grade 0"
        if name == "Accessory_Explosive":
            # This will always be the same element but keep all the formatting in the same place
            return element + (" Grenade Accessory" if full else "")
        elif name == "Accessory_MonsterTrap":
            return "Monster Trap" + (" Grenade Accessory" if full else "")

        # All parts after grade 0 have a suffix "_Grade[n]"
        grade = "0"
        if len(nameSplit) > 2:
            grade = name[-1]

        return f"{element} Grade {grade}" + (" Grenade Accessory" if full else "")

    # A lot of grenade parts just have the info we want as a suffix
    elif partType == "ChildCount":
        return f"Grade {name[-1]}" + (" Grenade Child Count" if full else "")
    elif partType == "Damage":
        return f"Grade {name[-1]}" + (" Grenade Damage" if full else "")
    elif partType == "StatusDamage":
        return f"Grade {name[-1]}" + (" Grenade Status Damage" if full else "")
    elif partType == "Trigger":
        return f"Grade {name[-1]}" + (" Grenade Trigger" if full else "")
    elif partType == "DamageRadius":
        size = cast(str, nameSplit[1])
        # Just want to add a space :)
        if size == "ExtraLarge":
            size = "Extra Large"
        return size + (" Grenade Blast Radius" if full else "")

    # These parts are easier to just hardcode in a table
    elif partType == "Delivery":
        if name in GRENADE_DELIVERY_NAMES:
            return GRENADE_DELIVERY_NAMES[name] + (" Grenade Delivery" if full else "")
    elif partType == "Payload":
        # Deal with shattering payloads - they all append "_AirMask" to an existing one
        airMask = ""
        if name.endswith("AirMask"):
            name = name[:-8]
            airMask = "Shattering "

        if name in GRENADE_PAYLOAD_NAMES:
            return airMask + GRENADE_PAYLOAD_NAMES[name] + (" Grenade Payload" if full else "")
    elif str(part).startswith("GrenadeModDefinition"):
        if name in GRENADE_DEFINTION_NAMES:
            return GRENADE_DEFINTION_NAMES[name] + (" Grenade Type" if full else "")

    return str(part.Name)


def _getCOMPartName(part: unrealsdk.UObject, full: bool) -> str:
    partType = part.Outer.Name
    name = part.Name
    nameSplit = name.split("_")

    # Can you belive that not a single object in either game messes up anything so we can actually
    #  do this entirely programtically
    if partType == "Specialization":
        # While a little unclear, I think it's best to leave these with the proper name for people
        #  using gibbed, and instead let the stats explain what each part actually is
        return "_".join(nameSplit[1:]) + (" COM Specialization" if full else "")
    elif partType == "StatPrimary":
        return f"Grade {name[-7]}" + (" COM Primary" if full else "")
    elif partType == "StatPrimary02":
        return f"Grade {name[-4]}" + (" COM Secondary" if full else "")
    elif partType == "StatPenalty":
        return f"Grade {name[-1]}" + (" COM Penalty" if full else "")

    elif str(part).startswith("ClassModDefinition"):
        # Most COMs just have the full name as the last part after the last underscore
        comName = cast(str, nameSplit[-1])

        if name in COM_DEFINITION_OVERRIDES:
            return COM_DEFINITION_OVERRIDES[name] + (" COM Type" if full else "")

        # Deal with Tina COMs
        if comName in ("CE", "CG", "CN", "LE", "LG", "LN", "NE", "NG"):
            player = nameSplit[-2]
            # Need to convert two of the names
            if player == "Mechromancer":
                player = "Necromancer"
            elif player == "Merc":
                player == "Monk"

            return f"{comName} {player}" + (" COM Type" if full else "")

        # These names have a COM for each character, so there's no sense in having 6 copies of each
        #  in the override list
        if comName == "EridianVanquisher":
            comName = "Eridian Vanquisher"
        elif comName == "ChroniclerOfElpis":
            comName = "Chronicler Of Elpis"
        elif comName == "SlayerOfTerramorphous":
            comName = "Slayer Of Terramorphous"

        # Add a space into the Legendary/Celestial COM names
        if comName.startswith("Legendary"):
            comName = f"Legendary {comName[9:]}"
        elif comName.startswith("Celestial"):
            comName = f"Celestial {comName[9:]}"

        return comName + (" COM Type" if full else "")

    return str(part.Name)


def _getArtifactPartName(part: unrealsdk.UObject, full: bool) -> str:
    partType = part.Outer.Name
    name = part.Name
    nameSplit = name.split("_")

    # Really there don't need to be 4 versions of these enable parts, they all act the same
    if partType in ("Enable1st", "Enable2nd", "Enable3rd", "Enable4th"):
        return f"Effect {name[-1]}" + (f" Relic Enable {partType[6:]}" if full else "")
    # Only the seraph blood relic gets this type, it behaves differently too so seperate it
    elif partType == "Effects":
        return "Seraph Blood" + (" Relic Effect" if full else "")

    # Only in TPS
    elif partType == "EnableSpecial":
        element = _getElement(ARTIFACT_SPECIAL_NAMES[name])
        if full:
            return f"{element} Oz Kit Element"
        return f"{element} Element"

    # Luckily all of the objects that get the type "Might" are upgrades
    elif partType in ("Upgrade", "Might"):
        text = f"Grade {nameSplit[-1][5:]}"
        # The seraph relic upgrades don't boost as many effects as the others so let's explictly
        #  mention them
        # The seraph blood also doesn't have "Grade[n]" in it's name so we have to manually set it
        if nameSplit[-1] == "SeraphBloodRelic":
            text = "Grade 15 Blood of the Seraphs"
        elif "SeraphShadow" in name:
            text += " Shadow of the Seraphs"
        elif "SeraphBreath" in name:
            text += " Breath of the Seraphs"

        return text + (" Relic Upgrade" if full else "")

    elif partType == "Body":
        text = nameSplit[-1]
        if name in ARTIFACT_BODY_OVERRIDES:
            text = ARTIFACT_BODY_OVERRIDES[name]
        return text + (" Relic Body" if full else "")

    elif str(part).startswith("ArtifactDefinition"):
        text = nameSplit[-1]
        if str(part) in ARTIFACT_DEFINITION_OVERRIDES:
            text = ARTIFACT_DEFINITION_OVERRIDES[str(part)]

        # A few definitions have multiple similar variants, just differing by the last char
        for baseName in ARTIFACT_DEFINITION_VARIANTS:
            if nameSplit[-1].startswith(baseName):
                map = ARTIFACT_DEFINITION_VARIANTS[baseName]
                text = map[name[-1]]

                # Keep the element formatting in one place
                if baseName == "TwoFace":
                    text = ""
                    element = _getElement(text)
                    if element is not None and element != "None":
                        text += element + " "
                    text += "Two Face Duality"

        return text + (" Relic Type" if full else "")

    return str(part.Name)


ARTIFACT_DEFINITION_VARIANTS: Dict[str, Dict[str, str]] = {
    "Aggression": {
        "A": "AR Aggression",
        "B": "RL Aggression",
        "C": "Pistol Aggression",
        "D": "SG Aggression",
        "E": "SMG Aggression",
        "F": "SR Aggression"
    },
    "Allegiance": {
        "A": "Bandit Allegiance",
        "B": "Dahl Allegiance",
        "C": "Hyperion Allegiance",
        "D": "Jakobs Allegiance",
        "E": "Maliwan Allegiance",
        "F": "Tediore Allegiance",
        "G": "Torgue Allegiance",
        "H": "Vladof Allegiance"
    },
    "Duality": {
        "A": "SG/SR Vac Duality",
        "B": "Laser/AR Vac Duality",
        "C": "Pistol/SMG Duality",
        "D": "SMG/RL Duality",
        "E": "RL/Laser Duality",
        "F": "Laser/Pistol Duality",
        "G": "SMG/Laser Duality",
        "H": "SG/AR Duality",
        "I": "RL/SG Duality",
        "J": "Laser/SR Duality"
    },
    "TwoFace": {
        "A": "Corrosive",
        "B": "Fire",
        "C": "Shock",
        "D": "Explosive",
        "F": "Cryo",
        "G": "Crit"
    }
}

# Need to use full names for this one cause of Anemone duplicating stuff
ARTIFACT_DEFINITION_OVERRIDES: Dict[str, str] = {
    "ArtifactDefinition GD_Anemone_Relics.A_Item_Unique.Artifact_Deputy": "Hard Carry",
    "ArtifactDefinition GD_Anemone_Relics.A_Item_Unique.Relic_Lust": "Mouthwash",
    "ArtifactDefinition GD_Anemone_Relics.A_Item.Artifact_Elemental_Status": "Winter is Over",
    "ArtifactDefinition GD_Artifacts.A_Item_Unique.Artifact_Terramorphous": "Blood of Terra",
    "ArtifactDefinition GD_Artifacts.A_Item_Unique.Artifact_VaultHunter": "Vault Hunter's",
    "ArtifactDefinition GD_Artifacts.A_Item.Artifact_Elemental_Status": "Elemental",
    "ArtifactDefinition GD_Aster_Artifacts.A_Item_Unique.Artifact_MysteryAmulet": "Amulet",
    "ArtifactDefinition GD_Aster_Artifacts.A_Item_Unique.Artifact_SeraphShadow": "Shadow of the Seraphs",
    "ArtifactDefinition GD_Gladiolus_Artifacts.A_Item.Artifact_AggressionTenacityAssault": "AR Heart of the Ancients",
    "ArtifactDefinition GD_Gladiolus_Artifacts.A_Item.Artifact_AggressionTenacityLauncher": "RL Heart of the Ancients",
    "ArtifactDefinition GD_Gladiolus_Artifacts.A_Item.Artifact_AggressionTenacityPistol": "Pistol Heart of the Ancients",
    "ArtifactDefinition GD_Gladiolus_Artifacts.A_Item.Artifact_AggressionTenacityShotgun": "SG Heart of the Ancients",
    "ArtifactDefinition GD_Gladiolus_Artifacts.A_Item.Artifact_AggressionTenacitySMG": "SMG Heart of the Ancients",
    "ArtifactDefinition GD_Gladiolus_Artifacts.A_Item.Artifact_AggressionTenacitySniper": "Sniper Heart of the Ancients",
    "ArtifactDefinition GD_Gladiolus_Artifacts.A_Item.Artifact_ElementalProficiency": "Bone of the Ancients",
    "ArtifactDefinition GD_Gladiolus_Artifacts.A_Item.Artifact_ResistanceProtection": "Skin of the Ancients",
    "ArtifactDefinition GD_Gladiolus_Artifacts.A_Item.Artifact_VitalityStockpile": "Blood of the Ancients",
    "ArtifactDefinition GD_Iris_SeraphItems.Might.Iris_Seraph_Artifact_Might": "Strength of the Seraphs",
    "ArtifactDefinition GD_MoonItems.A_Item_Unique.MoonItem_AckAck": "Ack Ack",
    "ArtifactDefinition GD_MoonItems.A_Item_Unique.MoonItem_AntiAir_PerdyLights": "Perdy Lights",
    "ArtifactDefinition GD_MoonItems.A_Item_Unique.MoonItem_Astrotech": "3DD1.E",
    "ArtifactDefinition GD_MoonItems.A_Item_Unique.MoonItem_MoonlightSaga": "Moonlight Saga",
    "ArtifactDefinition GD_MoonItems.A_Item_Unique.MoonItem_Poopdeck": "Cathartic",
    "ArtifactDefinition GD_MoonItems.A_Item_Unique.MoonItem_SupportRelay": "Support Relay",
    "ArtifactDefinition GD_MoonItems.A_Item_Unique.MoonItem_SystemsPurge": "Systems Purge",
    "ArtifactDefinition GD_MoonItems.A_Item.MoonItem_AntiAir": "Clear Skies",
    "ArtifactDefinition GD_MoonItems.A_Item.MoonItem_PrecisionStrike": "Precision Strike",
    "ArtifactDefinition GD_MoonItems.A_Item.MoonItem_StrafingRun": "Strafing Run",
    "ArtifactDefinition GD_Orchid_Artifacts.A_Item_Unique.Artifact_Blade": "Otto Idol",
    "ArtifactDefinition GD_Orchid_Artifacts.A_Item_Unique.Artifact_SeraphBloodRelic": "Blood of the Seraphs",
    "ArtifactDefinition GD_Sage_Artifacts.A_Item.Artifact_SeraphBreath": "Breath of the Seraphs"
}

ARTIFACT_BODY_OVERRIDES: Dict[str, str] = {
    "Body_AckAck": "Ack Ack",
    "Body_AggressionTenacity": "Heart of the Ancients",
    "Body_AntiAir_PerdyLights": "Perdy Lights",
    "Body_AntiAir": "Clear Skies",
    "Body_Astrotech": "3DD1.E",
    "Body_Blade": "Otto Idol",
    "Body_ElementalProficiency": "Bone of the Ancients",
    "Body_MoonlightSaga": "Moonlight Saga",
    "Body_MysteryAmulet": "Amulet",
    "Body_Poopdeck": "Cathartic",
    "Body_PrecisionStrike": "Precision Strike",
    "Body_ResistanceProtection": "Skin of the Ancients",
    "Body_SeraphBloodRelic": "Blood of the Seraphs",
    "Body_SeraphBreath": "Breath of the Seraphs",
    "Body_SeraphShadow": "Shadow of the Seraphs",
    "Body_StrafingRun": "Strafing Run",
    "Body_SupportRelay": "Support Relay",
    "Body_SystemsPurge": "System Purge",
    "Body_Terramorphous": "Blood of Terra",
    "Body_TwoFace": "Two Face Duality",
    "Body_VaultHunter": "Vault Hunter's",
    "Body_VitalityStockpile": "Blood of the Ancients"
}

ARTIFACT_SPECIAL_NAMES: Dict[str, str] = {
    "EnableSpecial_Element1": "Fire",
    "EnableSpecial_Element2": "Shock",
    "EnableSpecial_Element3": "Corrosive",
    "EnableSpecial_Element4": "Ice",
    "EnableSpecial_ElementNone": "Explosive"
}

COM_DEFINITION_OVERRIDES: Dict[str, str] = {
    "ClassMod_Assassin_Rogue": "TN Rouge",
    "ClassMod_Mechromancer_Necromancer": "TN Necromancer",
    "ClassMod_Barbarian_Barbarian": "TN Barbarian",
    "ClassMod_Merc_Monk": "TN Monk",
    "ClassMod_Siren_Cleric": "TN Cleric",
    "ClassMod_Soldier_Ranger": "TN Ranger",
    "ClassMod_Mechromancer_Legendary_Anarchist": "Legendary Anarchist",
    "ClassMod_Mechromancer_Legendary_Catalyst": "Legendary Catalyst",
    "ClassMod_Mechromancer_Legendary_Roboteer": "Legendary Roboteer",
    "ClassMod_Psycho_Legendary_Reaper": "Legendary Reaper",
    "ClassMod_Psycho_Legendary_Sickle": "Legendary Sickle",
    "ClassMod_Psycho_Legendary_Torch": "Legendary Torch",
    "ClassMod_Baroness_BigGameHunter": "Big Game Hunter",
    "ClassMod_Baroness_BlueBlood": "Blue Blood",
    "ClassMod_Baroness_CremeDeLaCreme": "Creme de la Creme",
    "ClassMod_Baroness_HighDef": "High Definition",
    "ClassMod_Baroness_SportHunter": "Sport Hunter",
    "ClassMod_Lawbringer_BountyHunter": "Bounty Hunter",
    "ClassMod_Lawbringer_LawEnforcer": "Law Enforcer",
    "ClassMod_Lawbringer_LoneStar": "Lone Star",
    "ClassMod_Lawbringer_SixShooter": "Six Shooter",
    "ClassMod_Lawbringer_TheKid": "The Kid",
    "ClassMod_Lawbringer_Z_LegendaryLawbringer": "Celestial Lawbringer",
    "ClassMod_Gladiator_FemmeFatale": "Femme Fatale",
    "ClassMod_Prototype_FactorySecond": "Factory Second",
    "ClassMod_Prototype_LooseCannon": "Lose Cannon",
    "ClassMod_Prototype_ShortCircuit": "Short Circuit",
    "ClassMod_Doppelganger_BestMan": "Best Man",
    "ClassMod_Doppelganger_RoleModel": "Role Model",
}

GRENADE_DEFINTION_NAMES: Dict[str, str] = {
    "GrenadeMod_BabyBoomer": "Baby Boomer",
    "GrenadeMod_Blade": "Midnight Star",
    "GrenadeMod_BonusPackage": "Bonus Package",
    "GrenadeMod_BouncingBonny": "Bouncing Bonny",
    "GrenadeMod_DataScrubber": "Data Scrubber",
    "GrenadeMod_Exterminator": "Exterminator",
    "GrenadeMod_Fastball": "Fastball",
    "GrenadeMod_FlameSpurt": "Flame Spurt",
    "GrenadeMod_FourSeasons": "Four Seasons",
    "GrenadeMod_FusterCluck": "Fuster Cluck",
    "GrenadeMod_Leech": "Leech",
    "GrenadeMod_MagicSpell": "Magic Spell",
    "GrenadeMod_Meganade": "Meganade",
    "GrenadeMod_MonsterTrap": "Monster Trap",
    "GrenadeMod_NastySurprise": "Nasty Suprise",
    "GrenadeMod_Quasar": "Quasar",
    "GrenadeMod_RollingThunder": "Rolling Thunder",
    "GrenadeMod_SkyRocket": "Sky Rocket",
    "GrenadeMod_Snowball": "Snowball",
    "GrenadeMod_Standard": "Standard",
    "Iris_Seraph_GrenadeMod_Crossfire": "Crossfire",
    "Iris_Seraph_GrenadeMod_MeteorShower": "Meteor Shower",
    "Iris_Seraph_GrenadeMod_ONegative": "O-Negative"
}

GRENADE_DELIVERY_NAMES: Dict[str, str] = {
    "Delivery_BabyBoomer": "Baby Boomer",
    "Delivery_Blade": "Midnight Star",
    "Delivery_ChainLightning": "Chain Lightning",
    "Delivery_DataScrubber": "Data Scrubber",
    "Delivery_Fastball": "Fastball",
    "Delivery_Fireball": "Fireball",
    "Delivery_FireStorm": "Fire Storm",
    "Delivery_Homing_Sticky": "Sticky Homing",
    "Delivery_Homing": "Homing",
    "Delivery_LightningBolt": "Lightning Bolt",
    "Delivery_Lob_Flamer": "New Pandora Pyro",
    "Delivery_Lob_Sticky": "Sticky Lobbed",
    "Delivery_Lob": "Lobbed",
    "Delivery_LongBow_Sticky": "Sticky Longbow",
    "Delivery_LongBow": "Longbow",
    "Delivery_MagicMissile": "x2 Magic Missile",
    "Delivery_MagicMissileRare": "x4 Magic Missile",
    "Delivery_Meganade": "Meganade",
    "Delivery_NastySurprise": "Nasty Suprise",
    "Delivery_RollingThunder": "Rolling Thunder",
    "Delivery_Rubberized": "Rubberized",
    "Delivery_SkyRocket": "Sky Rocket",
    "Delivery_Snowball": "Snowball"
}

GRENADE_PAYLOAD_NAMES: Dict[str, str] = {
    "Iris_Seraph_GrenadeMod_Crossfire_Part_Payload": "Crossfire",
    "Iris_Seraph_GrenadeMod_MeteorShower_Part_Payload": "Meteor Shower",
    "Payload_AreaEffect": "Area Effect",
    "Payload_BonusPackage": "Bonus Package",
    "Payload_BouncingBetty": "Bouncing Betty",
    "Payload_BouncingBonny": "Bouncing Bonny",
    "Payload_Exterminator": "Exterminator",
    "Payload_FlameSpurt": "Breath of Terra",
    "Payload_FourSeasons": "Four Seasons",
    "Payload_FusterCluck": "Fuster Cluck",
    "Payload_KissOfDeath": "Kiss of Death",
    "Payload_Leech": "Leech",
    "Payload_Mirv": "MIRV",
    "Payload_Quasar": "Quasar",
    "Payload_Singularity": "Singularity",
    "Payload_Standard": "Standard",
    "Payload_Transfusion": "Transfusion"
}

GRENADE_PART_TYPE_OVERRIDES: Dict[str, str] = {
    "Iris_Seraph_GrenadeMod_MeteorShower_Part_Damage4": "Damage",
    "Iris_Seraph_GrenadeMod_MeteorShower_Part_Damage5": "Damage",
    "Iris_Seraph_GrenadeMod_MeteorShower_Part_Damage6": "Damage",
    "Iris_Seraph_GrenadeMod_MeteorShower_Part_Damage7": "Damage",
    "Iris_Seraph_GrenadeMod_MeteorShower_Part_Payload": "Payload",
    "Iris_Seraph_GrenadeMod_Crossfire_Part_Payload": "Payload",
    "Iris_Seraph_GrenadeMod_Crossfire_Part_Damage6": "Damage",
    "Iris_Seraph_GrenadeMod_Crossfire_Part_Damage7": "Damage",
    "Iris_Seraph_GrenadeMod_ONegative_Part_Damage6": "Damage",
    "Iris_Seraph_GrenadeMod_ONegative_Part_Damage7": "Damage",
}

SHIELD_MESH_NAMES: Dict[str, str] = {
    # These are actually bodies
    "Shield_Accessory_Bandit": "Bandit",
    "Shield_Accessory_Dahl": "Dahl",
    "Shield_Accessory_Hyperion": "Hyperion",
    "Shield_Accessory_Tediore": "Tediore",
    "Shield_Accessory_Torgue": "Torgue",
    "Shield_Accessory_Vladof": "Vladof",
    "Shield_Accessory01_Pangolin": "Pangolin",
    "Shield_Accessory02_Pangolin": "Maliwan",
    "Shield_Battery_Bandit": "Bandit",
    "Shield_Battery_Dahl": "Dahl",
    "Shield_Battery_Hyperion": "Hyperion",
    "Shield_Battery_Tediore": "Tediore",
    "Shield_Battery_Torgue": "Torgue",
    "Shield_Battery_Vladof": "Vladof",
    # These are actually accessories
    "Shield_Body_Bandit": "Bandit",
    "Shield_Body_Dahl": "Dahl",
    "Shield_Body_Hyperion": "Hyperion",
    "Shield_Body_Pangolin": "Pangolin",
    "Shield_Body_Tediore": "Tediore",  # Turns out tediore body actually uses this name too
    "Shield_Body_Vladof": "Vladof",
    "Shield_Capacitor_Bandit": "Bandit",
    "Shield_Capacitor_Dahl": "Dahl",
    "Shield_Capacitor_Hyperion": "Hyperion",
    "Shield_Capacitor_Pangolin": "Pangolin",
    "Shield_Capacitor_Tediore": "Tediore",
    "Shield_Capacitor_Vladof": "Vladof"
}

SHIELD_PART_TYPE_OVERRIDES: Dict[str, str] = {
    "Iris_Seraph_Shield_Booster_Accessory4_Booster": "Accessory",
    "Iris_Seraph_Shield_Booster_Material": "Material",
    "Iris_Seraph_Shield_Juggernaut_Material": "Material",
    "Iris_Seraph_Shield_Pun-chee_Part_Material": "Material",
    "Iris_Seraph_Shield_Sponge_Part_Material": "Material",
    "Accessory4_Booster_MoxxisSlammer": "Accessory",
    "Orchid_Seraph_Anshin_Shield_Accessory": "Accessory",
    "Orchid_Seraph_Anshin_Shield_Material": "Material"
}

SHIELD_TYPE_OVERRIDES: Dict[str, str] = {
    "Aster_Seraph_Antagonist_Shield": "Antagonist",
    "Aster_Seraph_Blockade_Shield": "Blockade",
    "Iris_Seraph_Shield_Booster": "Big Boom Blaster",
    "Iris_Seraph_Shield_Juggernaut": " Hoplite",
    "Iris_Seraph_Shield_Pun-chee": "Pun-chee",
    "Iris_Seraph_Shield_Sponge": "Sponge",
    "Orchid_Seraph_Anshin_Shield": "Evolution",
    "Shield_Blade": "Manly Man",
    "Shield_Buckler": "Rough Rider",
    "Shield_Nova_Shock_Singularity_Peak": "Easy Mode",
    "Shield_RapidRelease": "Rapid Release",
    "Shield_Worming": "Retainer"
}

WEAP_OBJ_NAMES: Dict[str, Tuple[str, str]] = {
    "AR_Accessory_BanditClamp_Damage": ("Damage Clamp", "AR Accessory"),
    "AR_Accessory_BanditClamp_Wild": ("Wild Clamp", "AR Accessory"),
    "AR_Accessory_Bayonet": ("Bayonet", "1 AR Accessory"),
    "AR_Accessory_CryBaby_Rapid": ("Crybaby Rapid", "AR Accessory"),
    "AR_Accessory_CryBaby_Triple": ("Crybaby Triple", "AR Accessory"),
    "AR_Elemental_CryBaby_Piercing": ("Crybaby Piercing", "AR Element"),
    "AR_Elemental_CryBaby_Rage": ("Crybaby Rage", "AR Element"),
    "Laser_Accessory_Bayonet": ("Bayonet", "Laser Accessory"),
    "Laser_Accessory_Rosie_Thorns": ("Rosie", "Laser Accessory"),
    "Laser_Elemental_Egun": ("EGun", "Laser Element"),
    "Moonstone_Attachment_Boominator": ("Boominator", "Moonstone Accessory"),
    "Moonstone_Attachment_FastLearner": ("Fast Learner", "Moonstone Accessory"),
    "Moonstone_Attachment_HardenUp": ("Harden Up", "Moonstone Accessory"),
    "Moonstone_Attachment_MareksMouth": ("Mareks Mouth", "Moonstone Accessory"),
    "Moonstone_Attachment_Oxygenator": ("Oxygenator", "Moonstone Accessory"),
    "Moonstone_Attachment_PiercingRounds": ("Piercing Rounds", "Moonstone Accessory"),
    "Moonstone_Attachment_Punisher": ("Punisher", "Moonstone Accessory"),
    "Moonstone_Attachment_Safeguard": ("Safeguard", "Moonstone Accessory"),
    "Moonstone_Attachment_Serenity": ("Serenity", "Moonstone Accessory"),
    "Pistol_Accessory_Laser_Accuracy": ("Accuracy Laser", "Pistol Accessory"),
    "Pistol_Accessory_Laser_Double_DvaInfinity": ("Double Laser", "Pistol Accessory"),
    "Pistol_Accessory_Laser_Double": ("Double Laser", "Pistol Accessory"),
    "Pistol_Barrel_Torgue_88Fragnum": ("Torgue", "Pistol Barrel"),
    "Pistol_Barrel_Torgue": ("Torgue", "Pistol Barrel"),
    "SG_Accessory_Bayonet": ("Bayonet", "1 SG Accessory"),
    "SG_Accessory_MoonClip": ("Moon Clip", "SG Accessory"),
    "SG_Accessory_ShotgunShell": ("Shotgun Shell", "SG Accessory"),
    "SG_Accessory_Tech": ("Accuracy Tech 1", "SG Accessory"),
    "SMG_Accessory_Bayonet": ("Bayonet", "1 SMG Accessory"),
    "SMG_Accessory_Body1_Accurate": ("Accuracy Body", "SMG Accessory"),
    "SMG_Accessory_Body2_Damage": ("Damage Body", "SMG Accessory"),
    "SMG_Accessory_Body3_Accelerated": ("Bullet Speed Body", "SMG Accessory"),
    "SMG_Accessory_Stock1_Stabilized": ("Stability Stock", "SMG Accessory"),
    "SMG_Accessory_Stock2_Reload": ("Reload Stock", "SMG Accessory"),
    "Sniper_Accessory_Bayonet1": ("Bayonet", "SR Accessory"),
}

WEAP_MESH_NAMES: Dict[str, Tuple[str, str]] = {
    "Acc_Barrel_Bayonet2": ("Bayonet", "2 AR Accessory"),
    "Acc_Barrel_Bipod": ("Accuracy Bipod", "SR Accessory"),
    "Acc_Barrel_Bipod2": ("Crit Bipod", "SR Accessory"),
    "Acc_Barrel_Blade1": ("Blade", "1 Pistol Accessory"),
    "Acc_Barrel_Blade2": ("Blade", "2 Pistol Accessory"),
    "Acc_Barrel_ForeGrip": ("Foregrip", "SR Accessory"),
    "Acc_Barrel_Grip": ("Foregrip", "AR Accessory"),
    "Acc_Barrel_Tech1": ("Mag Tech", "Pistol Accessory"),
    "Acc_Barrel_Tech2": ("Damage Tech", "Pistol Accessory"),
    "Acc_Barrel_Tech3": ("Firerate Tech", "Pistol Accessory"),
    "Acc_Bayonet2": ("Bayonet", "2 SG Accessory"),
    "Acc_Body_Box": ("Box", "AR Accessory"),
    "Acc_BodyMod1": ("Mag Body Mod", "RL Accessory"),
    "Acc_BodyMod2": ("Accuracy Body Mod", "RL Accessory"),
    "Acc_Grip_Stock": ("Stock", "Pistol Accessory"),
    "Acc_Gripper": ("Gripper", "RL Accessory"),
    "Acc_Handle": ("Handle", "RL Accessory"),
    "Acc_Scope_Mount1": ("Mag Mount", "SR Accessory"),
    "Acc_Scope_Mount2": ("Firerate Mount", "SR Accessory"),
    "Acc_Scope_Mount3": ("Damage Mount", "SR Accessory"),
    "Acc_Stock_Shroud1": ("Mag Shroud", "SR Accessory"),
    "Acc_Stock_Shroud2": ("Accuracy Shroud", "SR Accessory"),
    "Acc_StockCover": ("Stock Cover", "RL Accessory"),
    "Acc_StockTube": ("Stock Tube", "RL Accessory"),
    "Acc_Tech2": ("Crit Tech 2", "SG Accessory"),
    "Acc_Tech3": ("Reload Tech 3", "SG Accessory"),
    "Acc_TipCover": ("Tip Cover", "RL Accessory"),
    "Acc_VerticalGrip": ("Vertical Grip", "SG Accessory"),
    "AR_Barrel_Alien": ("ETech", "AR Barrel"),
    "AR_Barrel_Bandit": ("Bandit", "AR Barrel"),
    "AR_Barrel_Dahl": ("Dahl", "AR Barrel"),
    "AR_Barrel_Jakobs": ("Jakobs", "AR Barrel"),
    "AR_Barrel_Torgue": ("Torgue", "AR Barrel"),
    "AR_Barrel_Vladof_Alt": ("Vladof", "AR Barrel"),
    "AR_Barrel_Vladof": ("Vladof", "Minigun AR Barrel"),
    "AR_Body_Bandit": ("Bandit", "AR Body"),
    "AR_Body_Dahl": ("Dahl", "AR Body"),
    "AR_Body_Jakobs": ("Jakobs", "AR Body"),
    "AR_Body_Torgue": ("Torgue", "AR Body"),
    "AR_Body_Vladof": ("Vladof", "AR Body"),
    "AR_Grip_Bandit": ("Bandit", "AR Grip"),
    "AR_Grip_Dahl": ("Dahl", "AR Grip"),
    "AR_Grip_Jakobs": ("Jakobs", "AR Grip"),
    "AR_Grip_Torgue": ("Torgue", "AR Grip"),
    "AR_Grip_Vladof": ("Vladof", "AR Grip"),
    "AR_Scope_Bandit": ("Bandit", "AR Sight"),
    "AR_Scope_Dahl": ("Dahl", "AR Sight"),
    "AR_Scope_Jakobs": ("Jakobs", "AR Sight"),
    "AR_Scope_Torgue": ("Torgue", "AR Sight"),
    "AR_Scope_Vladof": ("Vladof", "AR Sight"),
    "AR_Stock_Bandit": ("Bandit", "AR Stock"),
    "AR_Stock_Dahl": ("Dahl", "AR Stock"),
    "AR_Stock_Jakobs": ("Jakobs", "AR Stock"),
    "AR_Stock_Torgue": ("Torgue", "AR Stock"),
    "AR_Stock_Vladof": ("Vladof", "AR Stock"),
    "L_Barrel_Alien": ("ETech", "RL Barrel"),
    "L_Barrel_Bandit": ("Bandit", "RL Barrel"),
    "L_Barrel_Maliwan": ("Maliwan", "RL Barrel"),
    "L_Barrel_Tediore": ("Tediore", "RL Barrel"),
    "L_Barrel_Torgue": ("Torgue", "RL Barrel"),
    "L_Barrel_Vladof": ("Vladof", "RL Barrel"),
    "L_Body_Bandit": ("Bandit", "RL Body"),
    "L_Body_Maliwan": ("Maliwan", "RL Body"),
    "L_Body_Tediore": ("Tediore", "RL Body"),
    "L_Body_Torgue": ("Torgue", "RL Body"),
    "L_Body_Vladof": ("Vladof", "RL Body"),
    "L_Exhaust_Bandit": ("Bandit", "RL Exhaust"),
    "L_Exhaust_Maliwan": ("Maliwan", "RL Exhaust"),
    "L_Exhaust_Tediore": ("Tediore", "RL Exhaust"),
    "L_Exhaust_Torgue": ("Torgue", "RL Exhaust"),
    "L_Exhaust_Vladof": ("Vladof", "RL Exhaust"),
    "L_Grip_Bandit": ("Bandit", "RL Grip"),
    "L_Grip_Maliwan": ("Maliwan", "RL Grip"),
    "L_Grip_Tediore": ("Tediore", "RL Grip"),
    "L_Grip_Torgue": ("Torgue", "RL Grip"),
    "L_Grip_Vladof": ("Vladof", "RL Grip"),
    "L_Scope_Bandit": ("Bandit", "RL Sight"),
    "L_Scope_Maliwan": ("Maliwan", "RL Sight"),
    "L_Scope_Tediore": ("Tediore", "RL Sight"),
    "L_Scope_Torgue": ("Torgue", "RL Sight"),
    "L_Scope_Vladof": ("Vladof", "RL Sight"),
    "Laser_Barrel_Dahl": ("Dahl", "Laser Barrel"),
    "Laser_Barrel_Hyperion": ("Hyperion", "Laser Barrel"),
    "Laser_Barrel_Maliwan": ("Maliwan", "Laser Barrel"),
    "Laser_Barrel_Tediore": ("Tediore", "Laser Barrel"),
    "Laser_Body_Dahl": ("Dahl", "Laser Body"),
    "Laser_Body_Hyperion": ("Hyperion", "Laser Body"),
    "Laser_Body_Maliwan": ("Maliwan", "Laser Body"),
    "Laser_Body_Tediore": ("Tediore", "Laser Body"),
    "Laser_FrontGrip_Dahl": ("Dahl", "Laser Grip"),
    "Laser_FrontGrip_Hyperion": ("Hyperion", "Laser Grip"),
    "Laser_FrontGrip_Maliwan": ("Maliwan", "Laser Grip"),
    "Laser_FrontGrip_Tediore": ("Tediore", "Laser Grip"),
    "Laser_Sight_Dahl": ("Dahl", "Laser Sight"),
    "Laser_Sight_Hyperion": ("Hyperion", "Laser Sight"),
    "Laser_Sight_Maliwan": ("Maliwan", "Laser Sight"),
    "Laser_Sight_Tediore": ("Tediore", "Laser Sight"),
    "Laser_Stock_Dahl": ("Dahl", "Laser Stock"),
    "Laser_Stock_Hyperion": ("Hyperion", "Laser Stock"),
    "Laser_Stock_Maliwan": ("Maliwan", "Laser Stock"),
    "Laser_Stock_Tediore": ("Tediore", "Laser Stock"),
    "Pistol_Barrel_Alien": ("ETech", "Pistol Barrel"),
    "Pistol_Barrel_Bandit": ("Bandit", "Pistol Barrel"),
    "Pistol_Barrel_Dahl": ("Dahl", "Pistol Barrel"),
    "Pistol_Barrel_Hyperion": ("Hyperion", "Pistol Barrel"),
    "Pistol_Barrel_Jakobs": ("Jakobs", "Pistol Barrel"),
    "Pistol_Barrel_Maliwan": ("Maliwan", "Pistol Barrel"),
    "Pistol_Barrel_Tediore": ("Tediore", "Pistol Barrel"),
    "Pistol_Barrel_Torgue": ("Torgue", "Pistol Barrel"),
    "Pistol_Barrel_Vladof": ("Vladof", "Pistol Barrel"),
    "Pistol_Body_Bandit": ("Bandit", "Pistol Body"),
    "Pistol_Body_Dahl": ("Dahl", "Pistol Body"),
    "Pistol_Body_Hyperion": ("Hyperion", "Pistol Body"),
    "Pistol_Body_Jakobs": ("Jakobs", "Pistol Body"),
    "Pistol_Body_Maliwan": ("Maliwan", "Pistol Body"),
    "Pistol_Body_Tediore": ("Tediore", "Pistol Body"),
    "Pistol_Body_Torgue": ("Torgue", "Pistol Body"),
    "Pistol_Body_Vladof": ("Vladof", "Pistol Body"),
    "Pistol_Grip_Bandit": ("Bandit", "Pistol Grip"),
    "Pistol_Grip_Dahl": ("Dahl", "Pistol Grip"),
    "Pistol_Grip_Hyperion": ("Hyperion", "Pistol Grip"),
    "Pistol_Grip_Jakobs": ("Jakobs", "Pistol Grip"),
    "Pistol_Grip_Maliwan": ("Maliwan", "Pistol Grip"),
    "Pistol_Grip_Tediore": ("Tediore", "Pistol Grip"),
    "Pistol_Grip_Torgue": ("Torgue", "Pistol Grip"),
    "Pistol_Grip_Vladof": ("Vladof", "Pistol Grip"),
    "Pistol_Scope_Bandit": ("Bandit", "Pistol Sight"),
    "Pistol_Scope_Dahl": ("Dahl", "Pistol Sight"),
    "Pistol_Scope_Hyperion": ("Hyperion", "Pistol Sight"),
    "Pistol_Scope_Jakobs": ("Jakobs", "Pistol Sight"),
    "Pistol_Scope_Maliwan": ("Maliwan", "Pistol Sight"),
    "Pistol_Scope_Tediore": ("Tediore", "Pistol Sight"),
    "Pistol_Scope_Torgue": ("Torgue", "Pistol Sight"),
    "Pistol_Scope_Vladof": ("Vladof", "Pistol Sight"),
    "SG_Barrel_Alien": ("ETech", "SG Barrel"),
    "SG_Barrel_Bandit": ("Bandit", "SG Barrel"),
    "SG_Barrel_Hyperion": ("Hyperion", "SG Barrel"),
    "SG_Barrel_Jakobs": ("Jakobs", "SG Barrel"),
    "SG_Barrel_Tediore": ("Tediore", "SG Barrel"),
    "SG_Barrel_Torgue": ("Torgue", "SG Barrel"),
    "SG_Body_Bandit": ("Bandit", "SG Body"),
    "SG_Body_Hyperion": ("Hyperion", "SG Body"),
    "SG_Body_Jakobs": ("Jakobs", "SG Body"),
    "SG_Body_Tediore": ("Tediore", "SG Body"),
    "SG_Body_Torgue": ("Torgue", "SG Body"),
    "SG_FrontGrip_Bandit": ("Bandit", "SG Grip"),
    "SG_FrontGrip_Hyperion": ("Hyperion", "SG Grip"),
    "SG_FrontGrip_Jakobs": ("Jakobs", "SG Grip"),
    "SG_FrontGrip_Tediore": ("Tediore", "SG Grip"),
    "SG_FrontGrip_Torgue": ("Torgue", "SG Grip"),
    "SG_Scope_Bandit": ("Bandit", "SG Sight"),
    "SG_Scope_Hyperion": ("Hyperion", "SG Sight"),
    "SG_Scope_Jakobs": ("Jakobs", "SG Sight"),
    "SG_Scope_Tediore": ("Tediore", "SG Sight"),
    "SG_Scope_Torgue": ("Torgue", "SG Sight"),
    "SG_Stock_Bandit": ("Bandit", "Bandit SG Stock"),
    "SG_Stock_Hyperion": ("Hyperion", "SG Stock"),
    "SG_Stock_Jakobs": ("Jakobs", "SG Stock"),
    "SG_Stock_Tediore": ("Tediore", "SG Stock"),
    "SG_Stock_Torgue": ("Torgue", "SG Stock"),
    "SMG_Barrel_Alien": ("ETech", "SMG Barrel"),
    "SMG_Barrel_Bandit": ("Bandit", "SMG Barrel"),
    "SMG_Barrel_Dahl": ("Dahl", "SMG Barrel"),
    "SMG_Barrel_Hyperion": ("Hyperion", "SMG Barrel"),
    "SMG_Barrel_Maliwan": ("Maliwan", "SMG Barrel"),
    "SMG_Barrel_Tediore": ("Tediore", "SMG Barrel"),
    "SMG_Body_Bandit": ("Bandit", "SMG Body"),
    "SMG_Body_Dahl": ("Dahl", "SMG Body"),
    "SMG_Body_Hyperion": ("Hyperion", "SMG Body"),
    "SMG_Body_Maliwan": ("Maliwan", "SMG Body"),
    "SMG_Body_Tediore": ("Tediore", "SMG Body"),
    "SMG_Grip_Bandit": ("Bandit", "SMG Grip"),
    "SMG_Grip_Dahl": ("Dahl", "SMG Grip"),
    "SMG_Grip_Hyperion": ("Hyperion", "SMG Grip"),
    "SMG_Grip_Maliwan": ("Maliwan", "SMG Grip"),
    "SMG_Grip_Tediore": ("Tediore", "SMG Grip"),
    "SMG_Scope_Bandit": ("Bandit", "SMG Sight"),
    "SMG_Scope_Dahl": ("Dahl", "SMG Sight"),
    "SMG_Scope_Hyperion": ("Hyperion", "SMG Sight"),
    "SMG_Scope_Maliwan": ("Maliwan", "SMG Sight"),
    "SMG_Scope_Tediore": ("Tediore", "SMG Sight"),
    "SMG_Stock_Bandit": ("Bandit", "SMG Stock"),
    "SMG_Stock_Dahl": ("Dahl", "SMG Stock"),
    "SMG_Stock_Hyperion": ("Hyperion", "SMG Stock"),
    "SMG_Stock_Maliwan": ("Maliwan", "SMG Stock"),
    "SMG_Stock_Tediore": ("Tediore", "SMG Stock"),
    "SR_Barrel_Alien": ("ETech", "SR Barrel"),
    "SR_Barrel_Dahl": ("Dahl", "SR Barrel"),
    "SR_Barrel_Hyperion": ("Hyperion", "SR Barrel"),
    "SR_Barrel_Jakobs": ("Jakobs", "SR Barrel"),
    "SR_Barrel_Maliwan": ("Maliwan", "SR Barrel"),
    "SR_Barrel_Vladof": ("Vladof", "SR Barrel"),
    "SR_Body_Dahl": ("Dahl", "SR Body"),
    "SR_Body_Hyperion": ("Hyperion", "SR Body"),
    "SR_Body_Jakobs": ("Jakobs", "SR Body"),
    "SR_Body_Maliwan": ("Maliwan", "SR Body"),
    "SR_Body_Vladof": ("Vladof", "SR Body"),
    "SR_Grip_Dahl": ("Dahl", "SR Grip"),
    "SR_Grip_Hyperion": ("Hyperion", "SR Grip"),
    "SR_Grip_Jakobs": ("Jakobs", "SR Grip"),
    "SR_Grip_Maliwan": ("Maliwan", "SR Grip"),
    "SR_Grip_Vladof": ("Vladof", "SR Grip"),
    "SR_Scope_Dahl": ("Dahl", "SR Sight"),
    "SR_Scope_Hyperion": ("Hyperion", "SR Sight"),
    "SR_Scope_Jakobs": ("Jakobs", "SR Sight"),
    "SR_Scope_Maliwan": ("Maliwan", "SR Sight"),
    "SR_Scope_Vladof": ("Vladof", "SR Sight"),
    "SR_Stock_Dahl": ("Dahl", "SR Stock"),
    "SR_Stock_Hyperion": ("Hyperion", "SR Stock"),
    "SR_Stock_Jakobs": ("Jakobs", "SR Stock"),
    "SR_Stock_Maliwan": ("Maliwan", "SR Stock"),
    "SR_Stock_Vladof": ("Vladof", "SR Stock"),
}
