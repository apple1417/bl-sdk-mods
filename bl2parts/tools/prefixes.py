import unrealsdk
from typing import List

from . import YAML
from .data import WEAPON_MANU_ATTRIBUTES


def get_prefix_data(part: unrealsdk.UObject) -> List[YAML]:
    prefixes = []

    for prefix in part.PrefixList:
        attribute = None

        try:
            attribute = prefix.Expressions[0].AttributeOperand1
        except ValueError:
            pass

        if attribute is None:
            prefixes.append({
                "name": prefix.PartName,
            })
        else:
            prefixes.append({
                "name": prefix.PartName,
                "restrict": WEAPON_MANU_ATTRIBUTES[attribute]
            })

    return prefixes
