import gzip
import json
import re
from glob import glob
from os import path
from typing import Any, Dict, Set, Tuple

"""
For bl2.parts, we only want to use "Bandit" in part names, no point showing two identical parts
 which everyone knows are just a rename of each other. For other use cases though, we do want to
 overwrite it back to "Scav" in TPS. This script fixes that.

Also gzip's the file so that it's smaller for other uses.
"""

JSON = Dict[str, Any]

TPS_DATA_FOLDER: str = "bl2parts/data/TPS"
INPUT_NAME_FILE: str = "bl2parts/part_names.json"
OUTPUT_NAME_FILE: str = "bl2parts/complete_part_names.json.gz"

RE_BANDIT = re.compile("bandit", flags=re.I)
SCAV_REPLACEMENT: str = "Scav"

KNOWN_NON_TPS_PARTS: Tuple[str, ...] = (
    "GD_Anemone_GrenadeMods.Material.Material_Bandit",
    "GD_Anemone_GrenadeMods.Material.Material_Bandit_2_Uncommon",
    "GD_Anemone_GrenadeMods.Material.Material_Bandit_3_Rare",
    "GD_Anemone_GrenadeMods.Material.Material_Bandit_4_VeryRare",
    "GD_Anemone_GrenadeMods.Material.Material_Bandit_5_Legendary",
    "GD_GrenadeMods.Material.Material_Bandit_5_Legendary",
)


def scav_replacement_case_preserving(match: re.Match) -> str:  # type: ignore
    """
    Custom replacement function for re.sub which replaces the match with 'Scav', attempting to
     preserve case.
    """
    g = match.group()
    if g.islower():
        return SCAV_REPLACEMENT.lower()
    if g.istitle():
        return SCAV_REPLACEMENT.title()
    if g.isupper():
        return SCAV_REPLACEMENT.upper()
    raise NotImplementedError


known_tps_parts: Set[str] = set()
for base_name_file in glob(path.join(TPS_DATA_FOLDER, "*.json")):
    with open(base_name_file) as file:
        data = json.load(file)
        known_tps_parts.update(data.keys())


fixed_names: JSON = {}
with open(INPUT_NAME_FILE) as file:
    for part, data in json.load(file).items():
        fixed_names[part] = data

        if "bandit" not in data["name"].lower():
            continue

        if part not in known_tps_parts:
            if part not in KNOWN_NON_TPS_PARTS:
                print(f"'{part}' does not appear to be a TPS part!")
            continue

        if "game_overrides" not in data:
            data["game_overrides"] = {}
        if "TPS" in data["game_overrides"]:
            print(f"'{part}' already has a TPS override!")
            continue

        new_name = RE_BANDIT.sub(scav_replacement_case_preserving, data["name"])
        data["game_overrides"]["TPS"] = new_name


with gzip.open(OUTPUT_NAME_FILE, "wt", encoding="utf8") as gzfile:
    json.dump(
        fixed_names,
        gzfile,
        indent=None,
        separators=(",", ":")
    )
