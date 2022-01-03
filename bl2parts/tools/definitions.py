import unrealsdk

from . import MODIFIER_NAMES, YAML, float_error


def get_definition_data(def_obj: unrealsdk.UObject) -> YAML:
    """
    Gets data about the provided definition.

    Args:
        def_obj: The definition object to process
    Returns:
        YAML data describing the definition
    """
    grades = []
    for slot in def_obj.AttributeSlotEffects:
        assert(slot.BaseModifierValue.BaseValueAttribute is None)
        assert(slot.BaseModifierValue.InitializationDefinition is None)
        assert(slot.PerGradeUpgrade.BaseValueAttribute is None)
        assert(slot.PerGradeUpgrade.InitializationDefinition is None)

        grades.append({
            "slot": slot.SlotName,
            "attribute": slot.AttributeToModify.Name,
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

    return {
        "_obj_name": def_obj.PathName(def_obj),
        "grades": grades
    }
