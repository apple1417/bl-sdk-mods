import unrealsdk
import importlib
import os
import sys
from typing import List, Tuple

# See https://github.com/bl-sdk/PythonSDK/issues/68
try:
    raise NotImplementedError
except NotImplementedError:
    __file__ = sys.exc_info()[-1].tb_frame.f_code.co_filename  # type: ignore

if os.path.dirname(__file__) not in sys.path:
    sys.path.append(os.path.dirname(__file__))

import yaml

for mod in (
    "tools",
    "tools.balances",
    "tools.definitions",
    "tools.parts",
):
    if mod in sys.modules:
        importlib.reload(sys.modules[mod])

from tools import YAML  # noqa: E402
from tools.balances import get_parts_for_definitions, get_parts_on_balance  # noqa: E402
from tools.definitions import get_definition_data  # noqa: E402
from tools.parts import get_part_data  # noqa: E402

DEFINITIONS: Tuple[str, ...] = (
    "GD_Weap_Shotgun.A_Weapons.WT_Bandit_Shotgun",
    "GD_Weap_Shotgun.A_Weapons.WT_Hyperion_Shotgun",
    "GD_Weap_Shotgun.A_Weapons.WT_Jakobs_Shotgun",
    "GD_Weap_Shotgun.A_Weapons.WT_Tediore_Shotgun",
    "GD_Weap_Shotgun.A_Weapons.WT_Torgue_Shotgun",
)

NON_UNIQUE_BALANCES: Tuple[str, ...] = (
    "GD_Weap_Shotgun.A_Weapons.SG_Bandit_5_Alien",
    "GD_Weap_Shotgun.A_Weapons.SG_Hyperion_5_Alien",
    "GD_Weap_Shotgun.A_Weapons.SG_Jakobs_4_VeryRare",
    "GD_Weap_Shotgun.A_Weapons.SG_Tediore_5_Alien",
    "GD_Weap_Shotgun.A_Weapons.SG_Torgue_4_VeryRare",
)

non_unique_parts = set()
for base_bal in NON_UNIQUE_BALANCES:
    bal = unrealsdk.FindObject("WeaponBalanceDefinition", base_bal)
    while bal is not None:
        non_unique_parts.update(get_parts_on_balance(bal))
        bal = bal.BaseDefinition


def_objects: List[unrealsdk.UObject] = [
    unrealsdk.FindObject("WeaponTypeDefinition", def_name)
    for def_name in DEFINITIONS
]

data: YAML = {}

for part in get_parts_for_definitions(def_objects):
    part_type, part_data = get_part_data(part)

    part_data["unique"] = part not in non_unique_parts

    if part_type not in data:
        data[part_type] = []
    data[part_type].append(part_data)

with open("Mods/bl2parts/shotguns.yml", "w") as file:
    yaml.dump(data, file)  # type: ignore

with open("Mods/bl2parts/shotguns_meta.yml", "w") as file:
    yaml.dump({  # type: ignore
        "standard_definition": get_definition_data(def_objects[0])
    }, file)
