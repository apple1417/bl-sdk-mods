import unrealsdk
from typing import Tuple

from Mods.ModMenu import Game  # type: ignore

from . import YAML, float_error
from .data import (DEFINITION_PART_TYPE, MODIFIER_NAMES, PART_NAMES, PART_TYPE_OVERRIDES,
                   WEAPON_MANU_ATTRIBUTES, WEAPON_PART_TYPE_NAMES)


def get_part_data(part: unrealsdk.UObject) -> Tuple[str, YAML]:
    """
    Gets data about the provided part.

    Args:
        part: The part object to process
    Returns:
        A tuple of the part's type, and the YAML data describing it
    """
    part_name = part.PathName(part)

    part_type: str
    if part_name in PART_TYPE_OVERRIDES:
        part_type = PART_TYPE_OVERRIDES[part_name]
    elif part.Class.Name == "WeaponTypeDefinition":
        part_type = DEFINITION_PART_TYPE
    elif part.Material is not None:
        part_type = WEAPON_PART_TYPE_NAMES[8]
    elif 0 <= part.PartType < len(WEAPON_PART_TYPE_NAMES):
        part_type = WEAPON_PART_TYPE_NAMES[part.PartType]
    else:
        raise ValueError(f"Bad part type {part.PartType} on {part_name}")

    all_bonuses = []

    for grade in part.AttributeSlotUpgrades:
        if grade.GradeIncrease == 0:
            continue
        all_bonuses.append({
            "slot": grade.SlotName,
            "value": grade.GradeIncrease,
            "type": "grade",
        })

    for attr_group, base_restrict in (
        (part.WeaponAttributeEffects, None),
        (part.ExternalAttributeEffects, None),
        (part.ZoomWeaponAttributeEffects, "Zoom"),
        (part.ZoomExternalAttributeEffects, "Zoom"),
    ):
        for attr in attr_group:
            bonus_data = {
                "attribute": part.PathName(attr.AttributeToModify),
                "type": MODIFIER_NAMES[attr.ModifierType],
            }

            restrict = base_restrict

            if (
                attr.BaseModifierValue.BaseValueAttribute in WEAPON_MANU_ATTRIBUTES
                and attr.BaseModifierValue.InitializationDefinition is None
            ):
                value = float_error(attr.BaseModifierValue.BaseValueScaleConstant)
                if restrict is not None:
                    unrealsdk.Log(
                        f"Found manufacturer restriction on bonus with existing restriction"
                        f" {part_name}"
                    )
                restrict = WEAPON_MANU_ATTRIBUTES[attr.BaseModifierValue.BaseValueAttribute]
            elif (
                attr.BaseModifierValue.BaseValueAttribute is not None
                or attr.BaseModifierValue.InitializationDefinition is not None
            ):
                unrealsdk.Log(f"Unparsable bonus on {part_name}")
                continue
            else:
                value = float_error(
                    attr.BaseModifierValue.BaseValueConstant
                    * attr.BaseModifierValue.BaseValueScaleConstant
                )

            if value == 0:
                continue

            bonus_data["value"] = value
            if restrict is not None:
                bonus_data["restrict"] = restrict

            all_bonuses.append(bonus_data)

    part_data = {
        "_obj_name": part_name
    }

    if part_name in PART_NAMES:
        name_data = PART_NAMES[part_name]
        override = name_data.get("game_overrides", {}).get(Game.GetCurrent()._name_)  # type: ignore

        part_data["name"] = override if override is not None else name_data["name"]
    else:
        part_data["name"] = part_name.split(".")[-1]

    if len(all_bonuses) > 0:
        part_data["bonuses"] = all_bonuses

    if part.GestaltModeSkeletalMeshName not in (None, "", "None") and part.bIsGestaltMode:
        part_data["mesh"] = part.GestaltModeSkeletalMeshName

    return part_type, part_data
