import unrealsdk
import importlib
import itertools
import json
import os
import sys
from typing import Set

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
    "tools.data",
    "tools.balances",
    "tools.definitions",
    "tools.parts",
    "tools.prefixes",
):
    if mod in sys.modules:
        importlib.reload(sys.modules[mod])

from tools import YAML  # noqa: E402
from tools.balances import get_parts_for_definitions, get_parts_on_balance  # noqa: E402
from tools.data import (ALL_DEFINITIONS, DEFINITION_PART_TYPE, GLITCH_PARTS,  # noqa: E402
                        ITEM_CLASS_OVERRIDES, ITEM_PART_TYPE_NAMES, MOONSTONE_PARTS,
                        NON_UNIQUE_BALANCES, PLURAL_WEAPON_PART_TYPE, UNIQUE_WEAPON_DEFINITIONS)
from tools.definitions import get_definition_data  # noqa: E402
from tools.parts import get_part_data  # noqa: E402
from tools.prefixes import get_prefix_data  # noqa: E402

output_dir = f"Mods/bl2parts/data/{Game.GetCurrent()._name_}/"
os.makedirs(output_dir, exist_ok=True)

GEN_NAME_DUMP_TEMPLATE: bool = True

for item_type, def_list in ALL_DEFINITIONS.items():
    non_unique_parts = set()
    for base_bal in NON_UNIQUE_BALANCES[item_type]:
        bal = unrealsdk.FindObject("InventoryBalanceDefinition", base_bal)
        while bal is not None:
            non_unique_parts.update(get_parts_on_balance(bal))
            bal = bal.BaseDefinition

    def_objects = {
        unrealsdk.FindObject("WillowInventoryDefinition", def_name)
        for def_name in def_list
    }
    def_objects = {x for x in def_objects if x is not None}

    non_unique_parts.update(def_objects - UNIQUE_WEAPON_DEFINITIONS)

    part_objects: Set[unrealsdk.UObject]
    if item_type in ITEM_CLASS_OVERRIDES:
        class_data = ITEM_CLASS_OVERRIDES[item_type]
        def_objects = {
            obj
            for obj in unrealsdk.FindAll(class_data.def_class)
            if not obj.Name.startswith("Default__")
        }
        part_objects = {
            obj
            for obj in unrealsdk.FindAll(class_data.part_class)
            if not obj.Name.startswith("Default__")
        }
    else:
        part_objects = get_parts_for_definitions(def_objects)
    data: YAML = {}

    for part in itertools.chain(def_objects, part_objects):
        if part in MOONSTONE_PARTS or part in GLITCH_PARTS:
            continue

        part_type, part_data = get_part_data(part)

        unique = part not in non_unique_parts
        part_data["unique"] = unique

        if part_type == "accessory" and not unique:
            prefixes = get_prefix_data(part)
            if prefixes:
                part_data["prefixes"] = prefixes

        if part.Class.Name in ("WeaponTypeDefinition", "WeaponPartDefinition"):
            part_type = PLURAL_WEAPON_PART_TYPE[part_type]

        if part_type not in data:
            data[part_type] = []
        data[part_type].append(part_data)

    meta_definitions = []
    for def_obj in def_objects:
        def_data = get_definition_data(def_obj)
        def_data["unique"] = def_obj not in non_unique_parts
        meta_definitions.append(def_data)

    for parts in data.values():
        parts.sort(key=lambda x: x["_obj_name"])

    meta_definitions.sort(key=lambda x: x["_obj_name"])  # type: ignore

    with open(os.path.join(output_dir, f"{item_type}s.yml"), "w") as file:
        # Seperate passes to force ordering
        yaml.dump(data, file, allow_unicode=True)  # type: ignore
        yaml.dump({  # type: ignore
            "meta": {
                PLURAL_WEAPON_PART_TYPE[DEFINITION_PART_TYPE]: meta_definitions
            }
        }, file, allow_unicode=True)

    name_path = os.path.join(output_dir, f"{item_type}_names.json")
    if GEN_NAME_DUMP_TEMPLATE and not os.path.exists(name_path):
        depluralize_part_type = {x: x for x in ITEM_PART_TYPE_NAMES}
        depluralize_part_type[DEFINITION_PART_TYPE] = DEFINITION_PART_TYPE

        depluralize_part_type.update({v: k for k, v in PLURAL_WEAPON_PART_TYPE.items()})

        with open(name_path, "w") as file:
            json.dump(
                {
                    part_data["_obj_name"]: {
                        "name": "",
                        "type": item_type.title(),
                        "slot": depluralize_part_type[part_type].title(),
                    }
                    for part_type, part_list in data.items()
                    for part_data in part_list
                },
                file,
                indent=4,
                sort_keys=True
            )
