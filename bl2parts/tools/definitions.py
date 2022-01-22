import unrealsdk
from typing import Dict

from Mods.ModMenu import Game  # type: ignore

from . import YAML, float_error
from .data import MODIFIER_NAMES, PART_NAMES, SCALING_INITALIZATIONS

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

GRENADE_DAMAGE_ATTR: str = "D_Attributes.GrenadeMod.GrenadeDamage"

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
    elif def_obj.Class.Name == "GrenadeModDefinition":
        proj_def = def_obj.DefaultProjectileDefinition
        if proj_def is not None:
            data["base"].append({
                "attribute": GRENADE_DAMAGE_ATTR,
                "scale": BASE_SCALING_CONSTANT,
                "value": float_error(8 * proj_def.Damage.BaseValueScaleConstant),
            })

    grades = []
    for slot in def_obj.AttributeSlotEffects:
        assert(slot.BaseModifierValue.BaseValueAttribute is None)
        assert(slot.BaseModifierValue.BaseValueAttribute == slot.PerGradeUpgrade.BaseValueAttribute)
        assert(
            slot.BaseModifierValue.InitializationDefinition
            == slot.PerGradeUpgrade.InitializationDefinition
        )

        grade_data = {
            "slot": slot.SlotName,
            "attribute": def_obj.PathName(slot.AttributeToModify),
            "type": MODIFIER_NAMES[slot.ModifierType],
        }

        scaling_init = slot.BaseModifierValue.InitializationDefinition

        if scaling_init is None:
            grade_data["base"] = float_error(
                slot.BaseModifierValue.BaseValueConstant
                * slot.BaseModifierValue.BaseValueScaleConstant
            )
            grade_data["per_grade"] = float_error(
                slot.PerGradeUpgrade.BaseValueConstant
                * slot.PerGradeUpgrade.BaseValueScaleConstant
            )
        elif scaling_init in SCALING_INITALIZATIONS:
            scale, scale_multi = SCALING_INITALIZATIONS[scaling_init]
            grade_data["scale"] = scale
            grade_data["base"] = float_error(
                scale_multi
                * slot.BaseModifierValue.BaseValueScaleConstant
            )
            grade_data["per_grade"] = float_error(
                scale_multi
                * slot.PerGradeUpgrade.BaseValueScaleConstant
            )
        else:
            raise AssertionError

        grades.append(grade_data)

    data["grades"] = grades

    return data
