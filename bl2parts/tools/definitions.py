import unrealsdk
from typing import Dict

from . import YAML, float_error
from .data import MODIFIER_NAMES, PART_NAMES

WEAPON_DAMAGE_ID: unrealsdk.UObject = unrealsdk.FindObject(
    "AttributeInitializationDefinition",
    "GD_Balance_HealthAndDamage.HealthAndDamage.Init_WeaponDamage"
)

WEAPON_DAMAGE_ATTR: str = "D_Attributes.Weapon.WeaponDamage"
STATUS_CHANCE_ATTR: str = "D_Attributes.Weapon.WeaponBaseStatusEffectChanceModifier"

# TODO: investigate which attr is actually right
STATUS_DAMAGE_ATTR: str = "FAKE:Status Damage"

SIMPLE_BASE_VALUES: Dict[str, str] = {
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

BASE_SCALING_CONSTANT: str = "&beta;"


def get_definition_data(def_obj: unrealsdk.UObject) -> YAML:
    """
    Gets data about the provided definition.

    Args:
        def_obj: The definition object to process
    Returns:
        YAML data describing the definition
    """

    def_name = def_obj.PathName(def_obj)

    data = {
        "_obj_name": def_name,
        "name": PART_NAMES[def_name]["name"],
        "base": []
    }

    for field, attr in SIMPLE_BASE_VALUES.items():
        data["base"].append({
            "attribute": attr,
            "value": float_error(getattr(def_obj, field))
        })

    assert(def_obj.InstantHitDamage.BaseValueAttribute is None)
    assert(def_obj.InstantHitDamage.InitializationDefinition == WEAPON_DAMAGE_ID)
    assert(def_obj.StatusEffectDamage.BaseValueAttribute is None)
    assert(def_obj.StatusEffectDamage.InitializationDefinition == WEAPON_DAMAGE_ID)
    assert(def_obj.BaseStatusEffectChanceModifier.BaseValueAttribute is None)
    assert(def_obj.BaseStatusEffectChanceModifier.InitializationDefinition is None)

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
    for slot in def_obj.AttributeSlotEffects:
        assert(slot.BaseModifierValue.BaseValueAttribute is None)
        assert(slot.BaseModifierValue.InitializationDefinition is None)
        assert(slot.PerGradeUpgrade.BaseValueAttribute is None)
        assert(slot.PerGradeUpgrade.InitializationDefinition is None)

        grades.append({
            "slot": slot.SlotName,
            "attribute": def_obj.PathName(slot.AttributeToModify),
            "type": MODIFIER_NAMES[slot.ModifierType],
            "base": float_error(
                slot.BaseModifierValue.BaseValueConstant
                * slot.BaseModifierValue.BaseValueScaleConstant
            ),
            "per_grade": float_error(
                slot.PerGradeUpgrade.BaseValueConstant
                * slot.PerGradeUpgrade.BaseValueScaleConstant
            )
        })

    data["grades"] = grades

    return data
