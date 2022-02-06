import unrealsdk
from typing import Dict

from Mods.ModMenu import Game  # type: ignore

from . import YAML, float_error
from .data import (ATTRIBUTES_TO_IGNORE, BASE_SCALING_CONSTANT, CONSTRAINT_NAMES, GRADES_TO_IGNORE,
                   KNOWN_ATTRIBUTES, KNOWN_INITALIZATIONS, MODIFIER_NAMES, PART_NAMES)

WEAPON_DAMAGE_ID: unrealsdk.UObject = unrealsdk.FindObject(
    "AttributeInitializationDefinition",
    "GD_Balance_HealthAndDamage.HealthAndDamage.Init_WeaponDamage"
)

WEAPON_DAMAGE_ATTR: str = "D_Attributes.Weapon.WeaponDamage"
STATUS_CHANCE_ATTR: str = "D_Attributes.Weapon.WeaponBaseStatusEffectChanceModifier"
STATUS_DAMAGE_ATTR: str = "D_Attributes.Weapon.WeaponStatusEffectDamage"

SIMPLE_WEAPON_BASE_VALUES: Dict[str, str] = {
    "FireRate": "D_Attributes.Weapon.WeaponFireInterval",
    "ClipSize": "D_Attributes.Weapon.WeaponClipSize",
    "ReloadTime": "D_Attributes.Weapon.WeaponReloadSpeed",
    "Spread": "D_Attributes.Weapon.WeaponSpread",
    "PerShotAccuracyImpulse": "D_Attributes.Weapon.WeaponPerShotAccuracyImpulse",
    "BurstShotAccuracyImpulseScale": "D_Attributes.Weapon.WeaponBurstShotAccuracyImpulseScale",
    "ZoomedEndFOV": "D_Attributes.Weapon.WeaponZoomEndFOV",
    "ProjectilesPerShot": "D_Attributes.Weapon.WeaponProjectilesPerShot",
    "ShotCost": "D_Attributes.Weapon.WeaponShotCost",
}


def get_definition_data(def_obj: unrealsdk.UObject) -> YAML:
    """
    Gets data about the provided definition.

    Args:
        def_obj: The definition object to process
    Returns:
        YAML data describing the definition
    """

    def_name = def_obj.PathName(def_obj)

    friendly_name: str
    if def_name in PART_NAMES:
        name_data = PART_NAMES[def_name]
        override = name_data.get("game_overrides", {}).get(Game.GetCurrent()._name_)  # type: ignore

        friendly_name = override if override is not None else name_data["name"]  # type: ignore
    else:
        friendly_name = def_name.split(".")[-1]

    data = {
        "_obj_name": def_name,
        "name": friendly_name,
        "base": []
    }

    if def_obj.Class.Name == "WeaponTypeDefinition":
        for field, attr in SIMPLE_WEAPON_BASE_VALUES.items():
            data["base"].append({
                "attribute": attr,
                "value": float_error(getattr(def_obj, field))
            })

        assert def_obj.InstantHitDamage.BaseValueAttribute is None
        assert def_obj.InstantHitDamage.InitializationDefinition == WEAPON_DAMAGE_ID
        assert def_obj.StatusEffectDamage.BaseValueAttribute is None
        assert def_obj.StatusEffectDamage.InitializationDefinition == WEAPON_DAMAGE_ID
        assert def_obj.BaseStatusEffectChanceModifier.BaseValueAttribute is None
        assert def_obj.BaseStatusEffectChanceModifier.InitializationDefinition is None

        data["base"].append({
            "attribute": WEAPON_DAMAGE_ATTR,
            "scale": BASE_SCALING_CONSTANT,
            "value": float_error(8 * def_obj.InstantHitDamage.BaseValueScaleConstant),
        })
        data["base"].append({
            "attribute": STATUS_DAMAGE_ATTR,
            "scale": BASE_SCALING_CONSTANT,
            "value": float_error(8 * def_obj.StatusEffectDamage.BaseValueScaleConstant),
        })
        data["base"].append({
            "attribute": STATUS_CHANCE_ATTR,
            "value": float_error(
                def_obj.BaseStatusEffectChanceModifier.BaseValueConstant
                * def_obj.BaseStatusEffectChanceModifier.BaseValueScaleConstant
            ),
        })

    grades = []
    for idx, slot in enumerate(def_obj.AttributeSlotEffects):
        if slot.AttributeToModify is None or slot.AttributeToModifier in ATTRIBUTES_TO_IGNORE:
            continue

        if slot.SlotName in GRADES_TO_IGNORE.get(def_obj.Class.Name, ()):
            continue

        grade_data = {
            "slot": slot.SlotName,
            "attribute": def_obj.PathName(slot.AttributeToModify),
            "type": MODIFIER_NAMES[slot.ModifierType],
        }

        if slot.ConstraintAttribute:
            if slot.ConstraintAttribute not in CONSTRAINT_NAMES:
                constraint_name = def_obj.PathName(slot.ConstraintAttribute)
                unrealsdk.Log(f"Unknown constraint '{constraint_name}' on '{def_name}'")
                grade_data["constraint"] = constraint_name
            else:
                grade_data["constraint"] = CONSTRAINT_NAMES[slot.ConstraintAttribute]

        for value_key, scale_key, offset_key, bvc_struct in (
            ("base", "scale", "offset", slot.BaseModifierValue),
            ("per_grade", "per_grade_scale", "per_grade_offset", slot.PerGradeUpgrade),
        ):
            attr = bvc_struct.BaseValueAttribute
            init = bvc_struct.InitializationDefinition

            if attr is None and init is None:
                grade_data[value_key] = float_error(
                    bvc_struct.BaseValueConstant * bvc_struct.BaseValueScaleConstant
                )

            elif (
                (attr in KNOWN_ATTRIBUTES and init is None)
                or (attr is None and init in KNOWN_INITALIZATIONS)
            ):
                stat_data = KNOWN_INITALIZATIONS[init] if attr is None else KNOWN_ATTRIBUTES[attr]

                if stat_data.scale:
                    grade_data[scale_key] = stat_data.scale
                if stat_data.offset != 0:
                    grade_data[offset_key] = float_error(
                        stat_data.offset
                        * bvc_struct.BaseValueScaleConstant
                    )

                grade_data[value_key] = float_error(
                    stat_data.value * bvc_struct.BaseValueScaleConstant
                )

            else:
                unrealsdk.Log(f"Unparseable grade {value_key} in index {idx} of '{def_name}'")
                continue

        grades.append(grade_data)

    data["grades"] = grades

    return data
