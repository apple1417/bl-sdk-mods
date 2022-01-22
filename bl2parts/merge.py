import json
import os
from typing import Any, Dict, List, Tuple, TypeVar

import yaml

# ==================================================================================================

PART_NAME_OVERRIDES: Dict[str, Dict[str, str]] = {
    "GD_Weap_Shotgun.A_Weapons.WT_Jakobs_Shotgun": {
        "BL2": "Jakobs (BL2)",
        "TPS": "Jakobs (TPS)",
    },
    "GD_Weap_Shotgun.A_Weapons.WT_Tediore_Shotgun": {
        "BL2": "Tediore (BL2)",
        "TPS": "Tediore (TPS)",
    },
    "GD_Weap_Shotgun.A_Weapons.WT_Torgue_Shotgun": {
        "BL2": "Torgue (BL2)",
        "TPS": "Torgue (TPS)",
    },
    "GD_Weap_Shotgun.Barrel.SG_Barrel_Hyperion_Striker": {
        "BL2": "Striker (BL2)",
    },
    "GD_Weap_Shotgun.Barrel.SG_Barrel_Jakobs_Sledges": {
        "BL2": "Sledge's Shotgun (BL2)",
    },
    "GD_Cork_Weap_Shotgun.Barrel.SG_Barrel_Hyperion_Striker": {
        "TPS": "Striker (TPS)",
    },
    "GD_Cork_Weap_Shotgun.Barrel.SG_Barrel_Jakobs_Sledges": {
        "TPS": "Sledge's Shotgun (TPS)",
    },
    "GD_Weap_Pistol.A_Weapons.WeaponType_Jakobs_Pistol": {
        "BL2": "Jakobs (BL2)",
        "TPS": "Jakobs (TPS)",
    },
}

PARTS_TO_NAIVE_BONUS_MERGE: Tuple[str, ...] = (
    # These just conflict on cryo/slag, otherwise identical
    "GD_GrenadeMods.Payload.Payload_AreaEffect",
    "GD_GrenadeMods.StatusDamage.StatusDamage_Grade1",
    "GD_GrenadeMods.StatusDamage.StatusDamage_Grade2",
    "GD_GrenadeMods.StatusDamage.StatusDamage_Grade3",
    "GD_GrenadeMods.StatusDamage.StatusDamage_Grade4",
    "GD_GrenadeMods.StatusDamage.StatusDamage_Grade5",
)

# ==================================================================================================

BASE_DATA_FOLDER: str = "bl2parts/data"
GAMES: Tuple[str, ...] = ("BL2", "TPS")

OUTPUT_DIR: str = "bl2parts/merged"
os.makedirs(OUTPUT_DIR, exist_ok=True)


# {"filename": [("path_to_file", "game"), ("path_to_matching_file", "game")]}
def get_file_mappings(extension: str) -> Dict[str, List[Tuple[str, str]]]:
    return {
        file: [
            (os.path.join(BASE_DATA_FOLDER, game, file), game)
            for game in GAMES
        ]
        for file in os.listdir(os.path.join(BASE_DATA_FOLDER, GAMES[0]))
        if file.endswith(extension)
    }


_K = TypeVar("_K")
_V = TypeVar("_V")


def remove_key(val: Dict[_K, _V], key: str) -> Dict[_K, _V]:
    return {k: v for k, v in val.items() if k != key}


for name, matching_files in get_file_mappings("json").items():
    output_file = os.path.join(OUTPUT_DIR, name)
    if os.path.exists(output_file):
        continue

    merged_json = {}
    for (filename, _) in matching_files:
        with open(filename) as file:
            for key, value in json.load(file).items():
                if key not in merged_json:
                    merged_json[key] = value
                    continue

                if merged_json[key] == value:
                    continue

                old = remove_key(merged_json[key], "name")
                new = remove_key(value, "name")
                if old == new:
                    continue

                print(f"Collision on '{key}'!")
                print(merged_json[key])
                print(value)
                print()

        with open(output_file, "w") as file:
            json.dump(
                merged_json,
                file,
                indent=4,
                sort_keys=True
            )


for name, matching_files in get_file_mappings("yml").items():
    merged_yml: Dict[str, Any] = {}
    merged_meta_definitions: List[Dict[str, Any]] = []

    for (filename, game) in matching_files:
        with open(filename) as file:
            data = yaml.load(file, Loader=yaml.Loader)  # type: ignore

            for part_type, part_list in remove_key(data, "meta").items():
                if part_type not in merged_yml:
                    merged_yml[part_type] = []

                for part in part_list:
                    if part["_obj_name"] in PART_NAME_OVERRIDES:
                        part["name"] = PART_NAME_OVERRIDES[part["_obj_name"]][game]

                    if part in merged_yml[part_type]:
                        continue

                    duplicate = next(filter(
                        lambda x: x["name"] == part["name"],
                        merged_yml[part_type]
                    ), None)
                    if not duplicate:
                        merged_yml[part_type].append(part)
                        continue

                    if remove_key(part, "_obj_name") == remove_key(duplicate, "_obj_name"):
                        continue

                    if (
                        remove_key(part, "prefixes") == remove_key(duplicate, "prefixes")
                        and not any(
                            (
                                existing_prefix["restrict"] == prefix["restrict"]
                                and existing_prefix != prefix
                            )
                            for existing_prefix in duplicate["prefixes"]
                            for prefix in part["prefixes"]
                        )
                    ):
                        new_prefixes = list(duplicate["prefixes"])
                        for prefix in part["prefixes"]:
                            if prefix not in new_prefixes:
                                new_prefixes.append(prefix)

                        new_prefixes.sort(key=lambda p: p["restrict"])  # type: ignore
                        duplicate["prefixes"] = new_prefixes
                        continue

                    if part["_obj_name"] in PARTS_TO_NAIVE_BONUS_MERGE:
                        for bonus in part["bonuses"]:
                            if bonus not in duplicate["bonuses"]:
                                duplicate["bonuses"].append(bonus)
                        continue

                    print("Collision on '" + part["_obj_name"] + "'!")

            for def_data in data["meta"]["definitions"]:
                if def_data in merged_meta_definitions:
                    continue

                duplicate = next(filter(
                    lambda x: x["name"] == part["name"],  # type: ignore
                    merged_meta_definitions
                ), None)
                if not duplicate:
                    merged_meta_definitions.append(def_data)
                    continue

                print("Collision on meta '" + def_data["_obj_name"] + "'!")

    for parts in merged_yml.values():
        parts.sort(key=lambda x: x["_obj_name"])
    merged_meta_definitions.sort(key=lambda x: x["_obj_name"])  # type: ignore

    with open(os.path.join(OUTPUT_DIR, name), "w") as file:
        # Seperate passes to force ordering
        yaml.dump(merged_yml, file)  # type: ignore
        yaml.dump({  # type: ignore
            "meta": {
                "definitions": merged_meta_definitions
            }
        }, file)
