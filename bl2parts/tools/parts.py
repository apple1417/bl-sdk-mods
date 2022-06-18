import unrealsdk
from typing import Optional, Tuple

from Mods.ModMenu import Game  # type: ignore

from . import YAML, float_error
from .data import (ALLOWED_DEFINITION_CLASSES, ALLOWED_ZERO_GRADES, ATTRIBUTES_TO_IGNORE,
                   GRADES_TO_IGNORE, IGNORED_POST_INIT_PARTS, KNOWN_ATTRIBUTES,
                   KNOWN_INITALIZATIONS, MESH_OVERRIDES, MODIFIER_NAMES, PART_NAMES,
                   PART_TYPE_OVERRIDES, WEAPON_MANU_ATTRIBUTES, BasePartTypeEnum, GenericPartType,
                   ItemPartType, WeaponPartType)


def _create_bonus_data(
    part: unrealsdk.UObject,
    attr_struct: unrealsdk.FStruct,
) -> Optional[YAML]:
    """
    Create bonus yaml from an attribute struct.

    Args:
        part: The part currently being parsed.
        attr_struct: The attribute struct to parse.
    Returns:
        None if the bonus was unparseable and should be skipped.
        The bonus yaml otherwise.
    """
    if attr_struct.AttributeToModify in ATTRIBUTES_TO_IGNORE.get(part.Class.Name, ()):
        return None

    bonus_data = {
        "attribute": part.PathName(attr_struct.AttributeToModify),
        "type": MODIFIER_NAMES[attr_struct.ModifierType],
    }

    bvc = attr_struct.BaseModifierValue.BaseValueConstant
    attr = attr_struct.BaseModifierValue.BaseValueAttribute
    init = attr_struct.BaseModifierValue.InitializationDefinition
    bvsc = attr_struct.BaseModifierValue.BaseValueScaleConstant

    if attr in WEAPON_MANU_ATTRIBUTES and init is None:
        value = float_error(bvsc)
        bonus_data["restrict"] = {
            "manu": WEAPON_MANU_ATTRIBUTES[attr]
        }

    elif (
        (attr in KNOWN_ATTRIBUTES and init is None)
        or (attr is None and init in KNOWN_INITALIZATIONS)
    ):
        stat_data = KNOWN_INITALIZATIONS[init] if attr is None else KNOWN_ATTRIBUTES[attr]

        value = float_error(stat_data.value * bvsc)

        formula = stat_data.get_formula()
        if formula:
            bonus_data["value_formula"] = formula

    elif attr is not None or init is not None:
        unrealsdk.Log(f"Unparsable bonus on {part.PathName(part)}")
        return None

    else:
        value = float_error(bvc * bvsc)

    if value == 0:
        return None

    bonus_data["value"] = value

    return bonus_data


def get_part_data(part: unrealsdk.UObject) -> Tuple[BasePartTypeEnum, YAML]:
    """
    Gets data about the provided part.

    Args:
        part: The part object to process
    Returns:
        A tuple of the part's type, and the YAML data describing it
    """
    part_name = part.PathName(part)

    part_type_enum = (
        WeaponPartType
        if part.Class.Name == "WeaponPartDefinition" else
        ItemPartType
    )

    part_type: BasePartTypeEnum
    if part_name in PART_TYPE_OVERRIDES:
        part_type = PART_TYPE_OVERRIDES[part_name]
    elif part.Class.Name in ALLOWED_DEFINITION_CLASSES:
        part_type = GenericPartType.Definition
    elif part.Material is not None:
        part_type = part_type_enum.Material  # type: ignore
    elif 0 <= part.PartType < len(part_type_enum):
        part_type = part_type_enum.from_index(part.PartType)
    else:
        raise ValueError(f"Bad part type {part.PartType} on {part_name}")

    all_bonuses = []

    for grade in part.AttributeSlotUpgrades:
        if grade.GradeIncrease == 0:
            if not grade.bActivateSlot:
                continue
            if grade.SlotName not in ALLOWED_ZERO_GRADES.get(part.Class.Name, ()):
                continue
        if grade.SlotName in GRADES_TO_IGNORE.get(part.Class.Name, ()):
            continue

        all_bonuses.append({
            "slot": grade.SlotName,
            "value": grade.GradeIncrease,
            "type": "grade",
        })

    for attr_group, is_zoom in (
        (part.WeaponAttributeEffects, False),
        (part.ItemAttributeEffects, False),
        (part.ExternalAttributeEffects, False),
        (part.ZoomWeaponAttributeEffects, True),
        (part.ZoomExternalAttributeEffects, True),
    ):
        if attr_group is None:
            continue
        for attr_struct in attr_group:
            bonus_data = _create_bonus_data(part, attr_struct)
            if bonus_data is None:
                continue

            if is_zoom:
                if "restrict" not in bonus_data:
                    bonus_data["restrict"] = {}
                bonus_data["restrict"]["zoom"] = True

            all_bonuses.append(bonus_data)

    # This catches the fibber, we'll see if it works for anything else
    # Just going for simple logic, it's not perfect, it'll catch some stuff that's not connected
    if part.BehaviorProviderDefinition is not None and part not in IGNORED_POST_INIT_PARTS:
        for seq in part.BehaviorProviderDefinition.BehaviorSequences:
            for behaviour_struct in seq.BehaviorData2:
                if behaviour_struct.Behavior.Class.Name != "Behavior_AttributeEffect":
                    continue
                for attr_struct in behaviour_struct.Behavior.AttributeEffects:
                    bonus_data = _create_bonus_data(part, attr_struct)
                    if bonus_data is None:
                        continue

                    if "restrict" not in bonus_data:
                        bonus_data["restrict"] = {}
                    bonus_data["restrict"]["post_init"] = True

                    all_bonuses.append(bonus_data)

    part_data = {
        "_obj_name": part_name
    }

    if part_name in PART_NAMES:
        name_data = PART_NAMES[part_name]
        override = name_data.get("game_overrides", {}).get(Game.GetCurrent().name)  # type: ignore

        part_data["name"] = override if override is not None else name_data["name"]
    else:
        part_data["name"] = part_name.split(".")[-1]

    if len(all_bonuses) > 0:
        part_data["bonuses"] = all_bonuses

    if part.bIsGestaltMode:
        if part in MESH_OVERRIDES:
            part_data["mesh"] = MESH_OVERRIDES[part]
        elif part.GestaltModeSkeletalMeshName not in (None, "", "None"):
            part_data["mesh"] = part.GestaltModeSkeletalMeshName

    rarity_struct = part.BaseRarity if part_type == GenericPartType.Definition else part.Rarity
    assert rarity_struct.InitializationDefinition is None

    rarity: float
    if rarity_struct.BaseValueAttribute:
        rarity = rarity_struct.BaseValueAttribute.ValueResolverChain[0].ConstantValue
    else:
        rarity = rarity_struct.BaseValueConstant
    rarity *= rarity_struct.BaseValueScaleConstant
    part_data["rarity"] = float_error(rarity)

    return part_type, part_data
