import unrealsdk
import argparse
import functools
from typing import Callable, Dict

from .. import RegisterConsoleCommand
from . import is_obj_instance, obj_name_splitter, parse_object
from .clone import clone_object, parse_clone_target

"""
We pass a known clones dict between functions so that we don't clone the same object twice (if it's
stored in two different locations)
"""
ClonesDict = Dict[unrealsdk.UObject, unrealsdk.UObject]
recursive_cloning: bool = True


# There are a bunch of different fields skills can be stored in, hence the field arg
def fixup_skill_field(field: str, behavior: unrealsdk.UObject, known_clones: ClonesDict) -> None:
    """
    Clones skills referenced in skill bpds, as well as other bpds stored on those skills.

    Args:
        field: The name of the field on the behavior object which the skill's stored in.
        behavior: The behavior object which references a skill.
        known_clones: A dict of objects to their clones, used to prevent double-cloning.
    """
    skill = getattr(behavior, field)
    if skill is None:
        return

    if skill in known_clones:
        setattr(behavior, field, known_clones[skill])
        return

    cloned_skill = clone_object(
        skill,
        behavior,
        # Empty string gives us the auto numbering back
        "" if skill.Name == skill.Class.Name else skill.Name,
    )
    if cloned_skill is None:
        return
    known_clones[skill] = cloned_skill

    setattr(behavior, field, cloned_skill)

    bpd = cloned_skill.BehaviorProviderDefinition
    if bpd is None:
        return

    if bpd in known_clones:
        cloned_skill.BehaviorProviderDefinition = known_clones[bpd]
        return

    if not recursive_cloning:
        return

    cloned_bpd = clone_object(bpd, cloned_skill, "" if bpd.Name == bpd.Class.Name else bpd.Name)
    if cloned_bpd is None:
        return
    known_clones[bpd] = cloned_bpd

    cloned_skill.BehaviorProviderDefinition = cloned_bpd
    fixup_bpd(cloned_bpd, known_clones)


"""
Dict mapping behavior class names to functions that perform extra fixups on them, incase there are
 extra objects that need to be cloned.
"""
extra_behaviour_fixups: Dict[str, Callable[[unrealsdk.UObject, ClonesDict], None]] = {
    "Behavior_AttributeEffect": functools.partial(fixup_skill_field, "AttributeEffect"),
    "Behavior_ActivateSkill": functools.partial(fixup_skill_field, "SkillToActivate"),
    "Behavior_ActivateListenerSkill": functools.partial(fixup_skill_field, "SkillToActivate"),
    "Behavior_DeactivateSkill": functools.partial(fixup_skill_field, "SkillToDeactivate"),
}


def fixup_bpd(cloned: unrealsdk.UObject, known_clones: ClonesDict) -> None:
    """
    Looks through a BPD for subobjects which still need to be cloned.

    Args:
        cloned: The cloned BPD.
        known_clones: A dict of objects to their clones, used to prevent double-cloning.
    """
    cloned_classes = {}
    for sequence in cloned.BehaviorSequences:
        # There are a bunch of other fields, but this seems to be the only used one
        for data in sequence.BehaviorData2:
            behavior = data.Behavior
            if behavior is None:
                continue

            if behavior in known_clones:
                data.Behavior = known_clones[behavior]
                continue

            if behavior.Class.Name not in cloned_classes:
                cloned_classes[behavior.Class.Name] = 0

            cloned_behavior = clone_object(
                behavior, cloned, f"{behavior.Class.Name}_{cloned_classes[behavior.Class.Name]}"
            )
            if cloned_behavior is None:
                continue
            cloned_classes[behavior.Class.Name] += 1
            known_clones[behavior] = cloned_behavior

            data.Behavior = cloned_behavior

            for cls, fixup in extra_behaviour_fixups.items():
                if is_obj_instance(cloned_behavior, cls):
                    fixup(cloned_behavior, known_clones)


def handler(args: argparse.Namespace) -> None:
    global recursive_cloning
    recursive_cloning = not args.no_reccursive
    src = parse_object(args.base)
    if src is None:
        return
    if not is_obj_instance(src, "BehaviorProviderDefinition"):
        unrealsdk.Log(f"Object '{src.PathName(src)}' must be a 'BehaviorProviderDefinition'!")
        return

    outer, name = parse_clone_target(args.clone, src.Class.Name, args.suppress_exists)
    if name is None:
        return

    cloned = clone_object(src, outer, name)
    if cloned is None:
        return
    fixup_bpd(cloned, {})


parser = RegisterConsoleCommand(
    "clone_bpd",
    handler,
    splitter=obj_name_splitter,
    description=(
        "Creates a clone of a BehaviourProvidierDefinition, as well as recursively cloning some of"
        " the objects making it up. This may not match the exact layout of the original objects,"
        " dump them manually to check what their new names are."
    ),
)
parser.add_argument("base", help="The bpd to create a copy of.")
parser.add_argument("clone", help="The name of the clone to create.")
parser.add_argument(
    "-x",
    "--suppress-exists",
    action="store_true",
    help="Suppress the error message when an object already exists.",
)
parser.add_argument(
    "-r",
    "--no-reccursive",
    action="store_true",
    help="Stops from recursively cloning the BPD of any skills linked to via the original BPD.",
)
