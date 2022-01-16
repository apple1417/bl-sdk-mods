import unrealsdk
import importlib
import itertools
import json
import os
import sys
from typing import List

from Mods.ModMenu import Game  # type: ignore

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
    "tools.data",
    "tools.definitions",
    "tools.parts",
    "tools.prefixes",
):
    if mod in sys.modules:
        importlib.reload(sys.modules[mod])

from tools import YAML  # noqa: E402
from tools.balances import get_parts_for_definitions, get_parts_on_balance  # noqa: E402
from tools.data import (ALL_WEAPON_DEFINITIONS, GLITCH_PARTS, MOONSTONE_PARTS,  # noqa: E402
                        NON_UNIQUE_BALANCES, PLURAL_WEAPON_PART_TYPE)
from tools.definitions import get_definition_data  # noqa: E402
from tools.parts import get_part_data  # noqa: E402
from tools.prefixes import get_prefix_data  # noqa: E402

output_dir = f"Mods/bl2parts/data/{Game.GetCurrent()._name_}/"
os.makedirs(output_dir, exist_ok=True)

GEN_NAME_DUMP_TEMPLATE: bool = True

for weapon_type, def_list in ALL_WEAPON_DEFINITIONS.items():
    non_unique_parts = set()
    for base_bal in NON_UNIQUE_BALANCES[weapon_type]:
        bal = unrealsdk.FindObject("WeaponBalanceDefinition", base_bal)
        while bal is not None:
            non_unique_parts.update(get_parts_on_balance(bal))
            bal = bal.BaseDefinition

    def_objects: List[unrealsdk.UObject] = [
        unrealsdk.FindObject("WeaponTypeDefinition", def_name)
        for def_name in def_list
    ]
    non_unique_parts.update(def_objects)

    data: YAML = {}

    for part in itertools.chain(def_objects, get_parts_for_definitions(def_objects)):
        if part in MOONSTONE_PARTS or part in GLITCH_PARTS:
            continue

        part_type, part_data = get_part_data(part)

        unique = part not in non_unique_parts
        part_data["unique"] = unique

        if part_type == "accessory" and not unique:
            prefixes = get_prefix_data(part)
            if prefixes:
                part_data["prefixes"] = prefixes

        plural_type = PLURAL_WEAPON_PART_TYPE[part_type]
        if plural_type not in data:
            data[plural_type] = []
        data[plural_type].append(part_data)

    for parts in data.values():
        parts.sort(key=lambda x: x["_obj_name"])

    with open(os.path.join(output_dir, f"{weapon_type}s.yml"), "w") as file:
        # Seperate passes to force ordering
        yaml.dump(data, file)  # type: ignore
        yaml.dump({  # type: ignore
            "meta": {
                "definitions": sorted([
                    get_definition_data(def_obj) for def_obj in def_objects
                ], key=lambda x: x["_obj_name"])  # type: ignore
            }
        }, file)

    name_path = os.path.join(output_dir, f"{weapon_type}_names.json")
    if GEN_NAME_DUMP_TEMPLATE and not os.path.exists(name_path):
        depluralize_weapon_part_type = {v: k for k, v in PLURAL_WEAPON_PART_TYPE.items()}

        with open(name_path, "w") as file:
            json.dump(
                {
                    part_data["_obj_name"]: {
                        "name": "",
                        "type": weapon_type.title(),
                        "slot": depluralize_weapon_part_type[part_type].title(),
                    }
                    for part_type, part_list in data.items()
                    for part_data in part_list
                },
                file,
                indent=4,
                sort_keys=True
            )
