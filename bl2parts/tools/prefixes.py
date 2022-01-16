import unrealsdk
from typing import List

from Mods.ModMenu import Game  # type: ignore

from . import YAML
from .data import WEAPON_MANU_ATTRIBUTES


def get_prefix_data(part: unrealsdk.UObject) -> List[YAML]:
    prefixes = []

    for prefix in part.PrefixList:
        attribute = None

        try:
            attribute = prefix.Expressions[0].AttributeOperand1
        except (IndexError, ValueError):
            pass

        if attribute is None:
            restrict = "Default"
        else:
            restrict = WEAPON_MANU_ATTRIBUTES[attribute]

        if restrict == "Bandit" and Game.GetCurrent() == Game.TPS:
            restrict = "Scav"

        prefixes.append({
            "name": prefix.PartName,
            "restrict": restrict
        })

    prefixes.sort(key=lambda p: p["restrict"])  # type: ignore

    return prefixes
